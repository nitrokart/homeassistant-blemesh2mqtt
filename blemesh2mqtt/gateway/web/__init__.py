import logging
import os
import re
import unicodedata
from uuid import UUID

from aiohttp import web

STATIC = os.path.join(os.path.dirname(__file__), "static")
NODE_ID_PATTERN = re.compile(r"[^a-z0-9_]+")

# only the Home Assistant ingress proxy (and local dev) may reach the UI
ALLOWED_IPS = set(os.environ.get("ALLOWED_IPS", "172.30.32.2,127.0.0.1,::1").split(","))


@web.middleware
async def guard(request, handler):
    if request.remote not in ALLOWED_IPS:
        raise web.HTTPForbidden()

    try:
        return await handler(request)
    except (ValueError, KeyError) as e:
        return web.json_response({"error": str(e)}, status=400)
    except RuntimeError as e:
        return web.json_response({"error": str(e)}, status=409)


def _uuid(value):
    try:
        return UUID(str(value))
    except ValueError:
        raise ValueError("Invalid uuid")


class WebServer:
    """
    Small JSON API plus a single page UI, served through Home Assistant ingress
    """

    def __init__(self, app, log_buffer, node_types):
        self._app = app
        self._log_buffer = log_buffer
        self._node_types = list(node_types)
        self._runner = None

        self._web = web.Application(middlewares=[guard])
        self._web.add_routes(
            [
                web.get("/", self._index),
                web.get("/api/state", self._state),
                web.get("/api/logs", self._logs),
                web.post("/api/scan", self._scan),
                web.post("/api/nodes", self._save_node),
                web.post("/api/nodes/{uuid}/configure", self._configure),
                web.post("/api/nodes/{uuid}/power", self._power),
                web.post("/api/nodes/{uuid}/brightness", self._brightness),
                web.post("/api/nodes/{uuid}/color-temperature", self._color_temperature),
                web.put("/api/nodes/{uuid}/name", self._rename),
                web.post("/api/nodes/{uuid}/type", self._type),
                web.post("/api/nodes/{uuid}/relay", self._relay),
                web.post("/api/nodes/{uuid}/diagnose", self._diagnose),
                web.delete("/api/nodes/{uuid}", self._remove),
                web.put("/api/mqtt", self._save_mqtt),
            ]
        )

    async def start(self, port):
        self._runner = web.AppRunner(self._web)
        await self._runner.setup()
        await web.TCPSite(self._runner, "0.0.0.0", port).start()
        logging.info(f"Web UI listening on port {port}")

    async def _index(self, request):
        return web.FileResponse(
            os.path.join(STATIC, "index.html"),
            headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
        )

    async def _state(self, request):
        state = self._app.ui_state()
        state["node_types"] = self._node_types
        return web.json_response(state)

    async def _logs(self, request):
        return web.json_response(self._log_buffer.lines())

    def _node_id(self, name, uuid):
        mesh = self._app._config.optional("mesh", None) or {}
        for node_id, info in mesh.items():
            if info.get("uuid") == str(uuid):
                return node_id

        normalized = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
        base = NODE_ID_PATTERN.sub("_", normalized).strip("_")[:40].rstrip("_")
        base = base or f"device_{uuid.hex[:8]}"
        if base not in mesh:
            return base

        suffix = uuid.hex[:6]
        return f"{base[:33].rstrip('_')}_{suffix}"

    async def _scan(self, request):
        self._app.start_job("scan", self._app.scan())
        return web.json_response({})

    async def _save_node(self, request):
        body = await request.json()

        uuid = _uuid(body.get("uuid"))
        name = str(body.get("name", "")).strip()[:80]
        if not name:
            raise ValueError("Enter a device name")
        if body.get("type") not in self._node_types:
            raise ValueError("Invalid node type")

        node_id = self._node_id(name, uuid)
        info = {
            "uuid": str(uuid),
            "name": name,
            "type": body["type"],
            "relay": bool(body.get("relay", False)),
        }
        self._app.start_job("provision", self._app.provision(uuid, node_id, info))
        return web.json_response({})

    async def _configure(self, request):
        uuid = _uuid(request.match_info["uuid"])
        self._app.start_job("configure", self._app.setup_node(uuid))
        return web.json_response({})

    async def _power(self, request):
        uuid = _uuid(request.match_info["uuid"])
        body = await request.json()
        on = body.get("on")
        if not isinstance(on, bool):
            raise ValueError("Power must be true or false")
        self._app.start_job("power", self._app.set_power(uuid, on))
        return web.json_response({})

    async def _brightness(self, request):
        uuid = _uuid(request.match_info["uuid"])
        body = await request.json()
        brightness = body.get("brightness")
        if isinstance(brightness, bool) or not isinstance(brightness, (int, float)) or not 0 <= brightness <= 100:
            raise ValueError("Brightness must be between 0 and 100")
        self._app.start_job("brightness", self._app.set_brightness(uuid, brightness))
        return web.json_response({})

    async def _color_temperature(self, request):
        uuid = _uuid(request.match_info["uuid"])
        body = await request.json()
        mireds = body.get("mireds")
        if isinstance(mireds, bool) or not isinstance(mireds, int) or not 50 <= mireds <= 1250:
            raise ValueError("Color temperature must be between 50 and 1250 mireds")
        self._app.start_job("color_temperature", self._app.set_color_temperature(uuid, mireds))
        return web.json_response({})

    async def _rename(self, request):
        uuid = _uuid(request.match_info["uuid"])
        body = await request.json()
        name = str(body.get("name", "")).strip()[:80]
        if not name:
            raise ValueError("Enter a device name")
        self._app.start_job("rename", self._app.rename_node(uuid, name))
        return web.json_response({})

    async def _type(self, request):
        uuid = _uuid(request.match_info["uuid"])
        body = await request.json()
        if body.get("type") not in self._node_types:
            raise ValueError("Invalid node type")
        self._app.start_job("type", self._app.set_type(uuid, body["type"]))
        return web.json_response({})

    async def _relay(self, request):
        uuid = _uuid(request.match_info["uuid"])
        body = await request.json()
        self._app.start_job("relay", self._app.set_relay(uuid, bool(body.get("relay"))))
        return web.json_response({})

    async def _diagnose(self, request):
        uuid = _uuid(request.match_info["uuid"])
        self._app.start_job("diagnose", self._app.diagnose(uuid))
        return web.json_response({})

    async def _remove(self, request):
        uuid = _uuid(request.match_info["uuid"])
        self._app.start_job("remove", self._app.remove(uuid, force=request.query.get("force") == "1"))
        return web.json_response({})

    async def _save_mqtt(self, request):
        body = await request.json()

        values = {}
        for key in ("broker", "username", "password"):
            value = str(body.get(key) or "")
            if key != "password":
                value = value.strip()
            if value:
                values[key] = value
        if body.get("port"):
            values["port"] = int(body["port"])

        await self._app.save_mqtt(values)
        return web.json_response({})
