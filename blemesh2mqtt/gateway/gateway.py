import asyncio
import logging
import secrets
import argparse
import uuid
import os
import json
from functools import partial

from contextlib import AsyncExitStack, suppress

from bluetooth_mesh.application import Application, Element
from bluetooth_mesh.crypto import ApplicationKey, DeviceKey, NetworkKey
from bluetooth_mesh.messages.config import GATTNamespaceDescriptor
from bluetooth_mesh.tokenring import TokenRing
from bluetooth_mesh import models

from tools import Config, LogBuffer, Store, Tasks
from mesh import Node, NodeManager
from mesh.diagnostics import Diagnostics
from mqtt import HassMqttMessenger
from web import WebServer

from modules.provisioner import ProvisionerModule
from modules.scanner import ScannerModule
from modules.manager import ManagerModule

from mesh.nodes.light import Light

LOG_BUFFER = LogBuffer()
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "info").upper(), handlers=[logging.StreamHandler(), LOG_BUFFER])
logging.getLogger("aiohttp.access").setLevel(logging.WARNING)

WEB_PORT = int(os.environ.get("WEB_PORT", 8099))


MESH_MODULES = {
    "prov": ProvisionerModule(),
    "scan": ScannerModule(),
    "mgmt": ManagerModule(),
}


NODE_TYPES = {
    "generic": Node,
    "light": Light,
}


class PersistentTokenRing(TokenRing):
    def __init__(self, uuid, basedir):
        self.PATH = os.path.join(basedir, "mesh-tokenring")
        super().__init__(uuid)

        logging.info("Mesh token cache path: %s", os.path.join(self.path, self.uuid))
        node_path = os.path.join(basedir, "meshd", "storage", uuid.hex, "node.json")
        try:
            with open(node_path) as node_file:
                node_token = json.load(node_file).get("token")
            if isinstance(node_token, str) and len(node_token) == 16:
                node_token = int(node_token, 16)
                if self.token == node_token:
                    logging.info("Persistent token matches the existing BlueZ node")
                    return

                logging.warning("Repairing stale mesh attach token from BlueZ node storage")
                self.token = node_token
                return
            logging.warning(
                "BlueZ node token has invalid format (type=%s, length=%s)",
                type(node_token).__name__,
                len(node_token) if isinstance(node_token, str) else "n/a",
            )
        except (OSError, json.JSONDecodeError, ValueError) as error:
            logging.warning("Could not read BlueZ node token from %s: %s", node_path, error)

        if self.token:
            logging.info("Loaded mesh token from persistent cache")
        else:
            logging.warning("No saved mesh attach token found for %s", uuid)


class MainElement(Element):
    """
    Represents the main element of the application node
    """

    LOCATION = GATTNamespaceDescriptor.MAIN
    MODELS = [
        models.ConfigClient,
        models.HealthClient,
        models.GenericOnOffClient,
        models.LightLightnessClient,
        models.LightCTLClient,
    ]

    def dev_key_message_received(self, source, remote, net_index, data):
        # BlueZ >= 5.7x reports local scan results as a loopback Remote
        # Provisioning Scan Report instead of calling ScanResult
        if data[:2] == b"\x80\x55" and len(data) >= 19:
            rssi = int.from_bytes(data[2:3], "little", signed=True)
            self.application.scan_result(rssi, data[3:], {})
            return
        super().dev_key_message_received(source, remote, net_index, data)


class MqttGateway(Application):

    COMPANY_ID = 0x05F1  # The Linux Foundation
    PRODUCT_ID = 1
    VERSION_ID = 1
    ELEMENTS = {
        0: MainElement,
    }
    CRPL = 32768
    PATH = "/org/hass/mesh"

    def __init__(self, loop, basedir):
        super().__init__(loop)
        self.TOKEN_RING = partial(PersistentTokenRing, basedir=basedir)

        self._store = Store(location=os.path.join(basedir, "store.yaml"))
        self._config = Config(os.path.join(basedir, "config.yaml"), defaults=self._mqtt_defaults())
        self._nodes = {}
        self._diagnostics = Diagnostics(self)

        self._messenger = None
        self._messenger_task = None
        self._job = {"name": None, "state": "idle", "message": ""}
        self._job_task = None

        self._app_keys = None
        self._dev_key = None
        self._primary_net_key = None
        self._new_keys = set()

        # load mesh modules
        for name, module in MESH_MODULES.items():
            module.initialize(self, self._store.section(name), self._config)

        self._initialize()

    @staticmethod
    def _mqtt_defaults():
        """
        Broker settings provided by the Home Assistant supervisor
        """
        mqtt = {}
        for key, env in (
            ("broker", "MQTT_HOST"),
            ("port", "MQTT_PORT"),
            ("username", "MQTT_USER"),
            ("password", "MQTT_PASSWORD"),
        ):
            if os.environ.get(env):
                mqtt[key] = os.environ[env]
        return {"mqtt": mqtt}

    @property
    def dev_key(self):
        if not self._dev_key:
            raise Exception("Device key not ready")
        return self._dev_key

    @property
    def primary_net_key(self):
        if not self._primary_net_key:
            raise Exception("Primary network key not ready")
        return 0, self._primary_net_key

    @property
    def app_keys(self):
        if not self._app_keys:
            raise Exception("Application keys not ready")
        return self._app_keys

    @property
    def nodes(self):
        return self._nodes

    def _load_key(self, keychain, name):
        if name not in keychain:
            logging.info(f"Generating {name}...")
            keychain[name] = secrets.token_hex(16)
            self._new_keys.add(name)
        try:
            return bytes.fromhex(keychain[name])
        except:
            raise Exception("Invalid device key")

    def _initialize(self):
        keychain = self._store.get("keychain") or {}
        local = self._store.section("local")
        nodes = self._store.section("nodes")

        # load or set application parameters
        self.address = local.get("address", 1)
        self.iv_index = local.get("iv_index", 5)

        # load or generate keys
        self._dev_key = DeviceKey(self._load_key(keychain, "device_key"))
        self._primary_net_key = NetworkKey(self._load_key(keychain, "network_key"))
        self._app_keys = [
            # currently just a single application key supported
            (0, 0, ApplicationKey(self._load_key(keychain, "app_key"))),
        ]

        # initialize node manager
        self._nodes = NodeManager(nodes, self._config, NODE_TYPES)

        # persist changes
        self._store.set("keychain", keychain)
        self._store.persist()

    async def _import_keys(self):
        logging.info("Importing keys...")

        if "primary_net_key" in self._new_keys:
            # register primary network key as subnet key
            await self.management_interface.import_subnet(0, self.primary_net_key[1])
            logging.info("Imported primary net key as subnet key")

        if "app_key" in self._new_keys:
            # import application key into daemon
            await self.management_interface.import_app_key(*self.app_keys[0])
            logging.info("Imported app key")

        # update application key for client models
        client = self.elements[0][models.GenericOnOffClient]
        await client.bind(self.app_keys[0][0])
        client = self.elements[0][models.LightLightnessClient]
        await client.bind(self.app_keys[0][0])
        client = self.elements[0][models.LightCTLClient]
        await client.bind(self.app_keys[0][0])

    async def _try_bind_node(self, node):
        try:
            await node.bind(self)
            logging.info(f"Bound node {node}")
            node.ready.set()
        except:
            logging.exception(f"Failed to bind node {node}")

    def scan_result(self, rssi, data, options):
        MESH_MODULES["scan"]._scan_result(rssi, data, options)

    def request_prov_data(self, count):
        return MESH_MODULES["prov"]._request_prov_data(count)

    def add_node_complete(self, uuid, unicast, count):
        MESH_MODULES["prov"]._add_node_complete(uuid, unicast, count)

    def add_node_failed(self, uuid, reason):
        MESH_MODULES["prov"]._add_node_failed(uuid, reason)

    async def restart_messenger(self):
        if self._messenger_task:
            self._messenger_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._messenger_task
            self._messenger_task = None

        if not self._config.optional("mqtt.broker"):
            logging.warning("No MQTT broker configured")
            return

        self._messenger_task = asyncio.create_task(self._run_messenger())

    async def _run_messenger(self):
        while True:
            try:
                self._messenger = HassMqttMessenger(self._config, self._nodes)
                await self._messenger.run(self)
                return
            except asyncio.CancelledError:
                raise
            except Exception:
                logging.exception("MQTT messenger failed, retrying in 10 seconds")
                await asyncio.sleep(10)

    def start_job(self, name, coro):
        """
        Run a long mesh operation in the background, one at a time
        """
        if self._job["state"] == "running":
            coro.close()
            raise RuntimeError(f"Task {self._job['name']} is still running")

        self._job = {"name": name, "state": "running", "message": ""}
        self._job_task = asyncio.create_task(self._run_job(coro))

    async def _run_job(self, coro):
        try:
            await coro
            self._job["state"] = "done"
        except Exception as e:
            logging.exception(f"Task {self._job['name']} failed")
            self._job.update(state="error", message=str(e) or type(e).__name__)

    async def scan(self):
        scanner = MESH_MODULES["scan"]
        scanner._unprovisioned.clear()
        await scanner.scan()

    async def provision(self, uuid, id, info):
        self._config.set_node(id, info)

        if not self._nodes.has(uuid):
            try:
                await asyncio.wait_for(MESH_MODULES["prov"]._provision(uuid), 240)
            except asyncio.TimeoutError:
                raise RuntimeError(
                    "Provisioning timed out after 4 minutes. Put the device in pairing mode, move it closer and try again."
                )
            except RuntimeError as e:
                if "bad-pdu" in str(e):
                    raise RuntimeError(
                        "The device did not answer. Make sure it is in pairing mode when you press Provision, "
                        "is close to the host, and is not paired to another app. On a Raspberry Pi set the add-on option io to generic."
                    ) from e
                raise
            if not self._nodes.has(uuid):
                raise RuntimeError("Provisioning did not complete. Check the gateway log.")

        await self.setup_node(uuid)

    async def setup_node(self, uuid):
        if not self._nodes.has(uuid):
            raise ValueError("Unknown node")

        node = self._nodes.rebuild(uuid)
        await MESH_MODULES["prov"]._configure(node)
        await self._try_bind_node(node)
        await self.restart_messenger()

    async def set_type(self, uuid, node_type):
        if self._nodes.get(uuid) is None:
            raise ValueError("Unknown node")
        mesh = self._config.optional("mesh", None) or {}
        for node_id, info in list(mesh.items()):
            if info.get("uuid") == str(uuid):
                self._config.set_node(node_id, {**info, "type": node_type})
                break
        node = self._nodes.rebuild(uuid)
        self._nodes.persist()
        await self._try_bind_node(node)
        await self.restart_messenger()

    async def set_relay(self, uuid, relay):
        if self._nodes.get(uuid) is None:
            raise ValueError("Unknown node")
        mesh = self._config.optional("mesh", None) or {}
        for node_id, info in list(mesh.items()):
            if info.get("uuid") == str(uuid):
                self._config.set_node(node_id, {**info, "relay": bool(relay)})
                break
        await self.setup_node(uuid)

    async def set_power(self, uuid, on):
        node = self._nodes.get(uuid)
        if not node:
            raise ValueError("Unknown node")
        if not hasattr(node, "turn_on"):
            await self.set_type(uuid, "light")
            node = self._nodes.get(uuid)
            if not hasattr(node, "turn_on"):
                raise ValueError("Device cannot be switched")
        await (node.turn_on() if on else node.turn_off())

    async def set_brightness(self, uuid, brightness):
        node = self._nodes.get(uuid)
        if node is None:
            raise ValueError("Unknown node")
        if not isinstance(node, Light) or not node.supports(Light.BrightnessProperty):
            raise ValueError("Device does not support brightness")
        await node.set_brightness(round(brightness * 65535 / 100))

    async def set_color_temperature(self, uuid, mireds):
        node = self._nodes.get(uuid)
        if node is None:
            raise ValueError("Unknown node")
        if not isinstance(node, Light) or not node.supports(Light.TemperatureProperty):
            raise ValueError("Device does not support color temperature")
        await node.set_mireds(mireds)

    async def diagnose(self, uuid):
        node = self._nodes.get(uuid)
        if node is None:
            raise ValueError("Unknown node")
        await self._diagnostics.run(node)

    async def rename_node(self, uuid, name):
        if self._nodes.get(uuid) is None:
            raise ValueError("Unknown node")

        mesh = self._config.optional("mesh", None) or {}
        for node_id, info in mesh.items():
            if info.get("uuid") == str(uuid):
                self._config.set_node(node_id, {**info, "name": name})
                self._nodes.get(uuid).config = self._config.node_config(uuid)
                await self.restart_messenger()
                return
        raise ValueError("Device configuration not found")

    async def remove(self, uuid, force=False):
        node = self._nodes.get(uuid)

        if node:
            try:
                await asyncio.wait_for(MESH_MODULES["prov"]._reset(node), 30)
            except Exception:
                if not force:
                    raise
                logging.exception(f"Could not reset {node}, removing it locally")
                self._nodes.delete(uuid)
                self._nodes.persist()

        self._config.remove_node(uuid)
        await self.restart_messenger()

    async def save_mqtt(self, values):
        # keep the stored password if none was entered
        if "password" not in values and "password" in self._config.user.get("mqtt", {}):
            values["password"] = self._config.user["mqtt"]["password"]

        self._config.set_mqtt(values)
        await self.restart_messenger()

    def ui_state(self):
        nodes = []
        for node in self._nodes.all():
            supports_brightness = isinstance(node, Light) and node.supports(Light.BrightnessProperty)
            supports_temperature = isinstance(node, Light) and node.supports(Light.TemperatureProperty)
            brightness = node.retained(Light.BrightnessProperty, None) if supports_brightness else None
            temperature = node.retained(Light.TemperatureProperty, None) if supports_temperature else None
            onoff = node.retained(Light.OnOffProperty, None) if isinstance(node, Light) else None
            nodes.append(
                {
                    "uuid": str(node.uuid),
                    "id": node.config.optional("id"),
                    "name": node.config.optional("name"),
                    "type": node.type,
                    "relay": bool(node.config.optional("relay", False)),
                    "unicast": node.unicast,
                    "configured": node.configured,
                    "ready": node.ready.is_set(),
                    "supports_onoff": isinstance(node, Light) and node.supports(Light.OnOffProperty),
                    "supports_brightness": supports_brightness,
                    "supports_temperature": supports_temperature,
                    "brightness": round(brightness * 100 / 65535) if brightness is not None else None,
                    "color_temp": round(1000000 / temperature) if temperature else None,
                    "on": bool(onoff) if onoff is not None else None,
                    "diagnostics": self._diagnostics.get(node.uuid),
                }
            )

        unprovisioned = MESH_MODULES["scan"]._unprovisioned

        return {
            "nodes": nodes,
            "unprovisioned": sorted(str(u) for u in unprovisioned if not self._nodes.has(u)),
            "mqtt": {
                "broker": self._config.optional("mqtt.broker", ""),
                "port": self._config.optional("mqtt.port", 1883),
                "username": self._config.optional("mqtt.username", ""),
                "password_set": bool(self._config.optional("mqtt.password")),
                "connected": bool(self._messenger_task and not self._messenger_task.done()),
            },
            "scan_rssi": {str(u): r for u, r in MESH_MODULES["scan"]._rssi.items()},
            "gateway": {"address": self.address, "iv_index": self.iv_index},
            "job": self._job,
        }

    async def run(self, args):
        async with AsyncExitStack() as stack:
            tasks = await stack.enter_async_context(Tasks())

            # connect to daemon
            await stack.enter_async_context(self)
            await self.connect()

            # leave network
            if args.leave:
                await self.leave()
                self._nodes.reset()
                self._nodes.persist()
                return

            try:
                # set overall application key
                await self.add_app_key(*self.app_keys[0])
            except:
                logging.exception(f"Failed to set app key {self._app_keys[0][2].bytes.hex()}")

                # try to re-add application key
                await self.delete_app_key(self.app_keys[0][0], self.app_keys[0][1])
                await self.add_app_key(*self.app_keys[0])

            # force reloading keys
            if args.reload:
                self._new_keys.add("primary_net_key")
                self._new_keys.add("app_key")

            # configure all keys
            await self._import_keys()

            # run user task if specified
            if "handler" in args:
                await args.handler(args)
                return

            # initialize all nodes
            for node in self._nodes.all():
                tasks.spawn(self._try_bind_node(node), f"bind {node}")

            await self.restart_messenger()

            # keep running for the web UI, even without any nodes
            await WebServer(self, LOG_BUFFER, NODE_TYPES).start(WEB_PORT)
            await asyncio.Event().wait()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--leave", action="store_true")
    parser.add_argument("--reload", action="store_true")
    parser.add_argument("--basedir", default="..")

    # module specific CLI interfaces
    subparsers = parser.add_subparsers()
    for name, module in MESH_MODULES.items():
        subparser = subparsers.add_parser(name)
        subparser.set_defaults(handler=module.handle_cli)
        module.setup_cli(subparser)

    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    app = MqttGateway(loop, args.basedir)

    with suppress(KeyboardInterrupt):
        loop.run_until_complete(app.run(args))


if __name__ == "__main__":
    main()
