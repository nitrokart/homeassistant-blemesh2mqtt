import asyncio
import logging
import time

from bluetooth_mesh import models
from bluetooth_mesh.messages.config import ConfigOpcode

HEARTBEAT_TTL = 127
HEARTBEAT_WINDOW = 1.5


def _plain(value):
    """
    Convert parsed construct containers into JSON friendly values
    """
    if isinstance(value, dict):
        return {str(k): _plain(v) for k, v in value.items() if not str(k).startswith("_")}
    if isinstance(value, (list, tuple, set)):
        return [_plain(v) for v in value]
    if isinstance(value, float) and value == float("inf"):
        return "infinite"
    if isinstance(value, (int, float, str, bool)) or value is None:
        return value
    return str(value)


class Diagnostics:
    """
    Active probes against a node. Only values answered by the node (or by the
    local mesh daemon) are stored; failed probes keep an error text instead.
    """

    def __init__(self, app):
        self._app = app
        self._results = {}

    def get(self, uuid):
        return self._results.get(str(uuid))

    def all(self):
        return self._results

    async def _probe(self, report, name, coro):
        started = time.monotonic()
        try:
            value = await asyncio.wait_for(coro, 8)
            report["probes"][name] = {
                "ok": True,
                "rtt_ms": round((time.monotonic() - started) * 1000),
                "value": _plain(value),
            }
            return value
        except Exception as error:
            logging.info("Diagnostic probe %s failed: %s", name, error or type(error).__name__)
            report["probes"][name] = {"ok": False, "error": str(error) or type(error).__name__}
            return None

    async def run(self, node):
        client = self._app.elements[0][models.ConfigClient]
        address = node.unicast
        report = {"at": time.time(), "address": address, "probes": {}}

        async def one(opcode_get, opcode_status, key):
            request = dict(opcode=opcode_get, params=dict())
            status = dict(opcode=opcode_status, params=dict())
            result = await client.get_param([address], 0, request, status, timeout=6)
            value = result.get(address)
            if value is None:
                raise TimeoutError("no answer")
            return value

        await self._probe(
            report,
            "default_ttl",
            one(ConfigOpcode.CONFIG_DEFAULT_TTL_GET, ConfigOpcode.CONFIG_DEFAULT_TTL_STATUS, "ttl"),
        )
        await self._probe(
            report, "relay", one(ConfigOpcode.CONFIG_RELAY_GET, ConfigOpcode.CONFIG_RELAY_STATUS, "relay")
        )
        await self._probe(
            report,
            "network_transmit",
            one(ConfigOpcode.CONFIG_NETWORK_TRANSMIT_GET, ConfigOpcode.CONFIG_NETWORK_TRANSMIT_STATUS, "transmit"),
        )
        await self._probe(
            report,
            "gatt_proxy",
            one(ConfigOpcode.CONFIG_GATT_PROXY_GET, ConfigOpcode.CONFIG_GATT_PROXY_STATUS, "proxy"),
        )
        await self._probe(
            report, "friend", one(ConfigOpcode.CONFIG_FRIEND_GET, ConfigOpcode.CONFIG_FRIEND_STATUS, "friend")
        )
        await self._probe(
            report, "beacon", one(ConfigOpcode.CONFIG_BEACON_GET, ConfigOpcode.CONFIG_BEACON_STATUS, "beacon")
        )

        await self._probe(report, "hops", self._measure_hops(client, address))

        hops = report["probes"].get("hops", {})
        report["reachable"] = any(p.get("ok") for p in report["probes"].values())
        report["hops"] = hops.get("value", {}).get("hops") if hops.get("ok") else None
        composition = getattr(node, "_composition", None)
        if composition is not None:
            report["composition"] = _plain(getattr(composition, "_data", None))

        self._results[str(node.uuid)] = report
        return report

    async def _measure_hops(self, client, address):
        """
        Heartbeat based hop count: the node publishes one heartbeat with a known
        TTL to this gateway and the local daemon reports the hops it travelled.
        """
        local = self._app.address

        await client.send_dev(
            local,
            net_index=0,
            opcode=ConfigOpcode.CONFIG_HEARBEAT_SUBSCRIPTION_SET,
            params=dict(source=address, destination=local, period_log=16),
        )
        await client.send_dev(
            address,
            net_index=0,
            opcode=ConfigOpcode.CONFIG_HEARBEAT_PUBLICATION_SET,
            params=dict(
                destination=local,
                count=1,
                period=0,
                ttl=HEARTBEAT_TTL,
                features=set(),
                net_key_index=0,
            ),
        )
        await asyncio.sleep(HEARTBEAT_WINDOW)

        status = client.expect_dev(
            local,
            net_index=0,
            opcode=ConfigOpcode.CONFIG_HEARBEAT_SUBSCRIPTION_STATUS,
            params=dict(),
        )
        request = lambda: client.send_dev(
            local,
            net_index=0,
            opcode=ConfigOpcode.CONFIG_HEARBEAT_SUBSCRIPTION_GET,
            params=dict(),
        )
        result = await client.query(request, status, timeout=4)
        data = result[ConfigOpcode.CONFIG_HEARBEAT_SUBSCRIPTION_STATUS.name.lower()]

        if not data.get("count"):
            raise TimeoutError("no heartbeat received")

        return {"hops": data.get("max_hops"), "min_hops": data.get("min_hops"), "heartbeats": data.get("count")}
