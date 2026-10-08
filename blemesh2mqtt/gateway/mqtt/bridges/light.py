from mqtt.bridge import HassMqttBridge
from mesh.nodes.light import Light


class GenericLightBridge(HassMqttBridge):
    """
    Generic bridge for lights
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def component(self):
        return "light"

    async def config(self, node):
        color_modes = set()
        message = {
            "~": self._messenger.node_topic(self.component, node),
            "name": node.config.optional("name"),
            "unique_id": node.config.require("id"),
            "object_id": node.config.require("id"),
            "command_topic": "~/set",
            "state_topic": "~/state",
            "schema": "json",
            "device": {
                "identifiers": [f"blemesh_{node.config.require('id')}"],
                "name": node.config.optional("name"),
                "manufacturer": "Bluetooth Mesh",
                "model": "Light",
            },
        }

        if node.supports(Light.BrightnessProperty):
            message["brightness_scale"] = 255
            message["brightness"] = True

        if node.supports(Light.TemperatureProperty):
            color_modes.add("color_temp")
            # convert from Kelvin to mireds
            # TODO: look up max/min values from device
            # message['min_mireds'] = 1000000 // 7000
            # message['max_mireds'] = 1000000 // 2000

        if color_modes:
            message["color_mode"] = True
            message["supported_color_modes"] = list(color_modes)

        await self._messenger.publish(self.component, node, "config", message, retain=True)

    async def _state(self, node, onoff):
        """
        Send a generic state message covering the nodes full state

        If the light is on, all properties are set to their retained state.
        If the light is off, properties are not passed at all.
        """
        message = {"state": "ON" if onoff else "OFF"}

        if onoff and node.supports(Light.BrightnessProperty):
            message["brightness"] = round(node.retained(Light.BrightnessProperty, 65535) * 255 / 65535)
        if onoff and node.supports(Light.TemperatureProperty):
            message["color_temp"] = round(1000000 / node.retained(Light.TemperatureProperty, 4000))

        await self._messenger.publish(self.component, node, "state", message, retain=True)

    async def _mqtt_set(self, node, payload):
        if "color_temp" in payload:
            await node.set_mireds(payload["color_temp"])
        if "brightness" in payload:
            await node.set_brightness(round(payload["brightness"] * 65535 / 255))
        if payload.get("state") == "ON":
            await node.turn_on()
        if payload.get("state") == "OFF":
            await node.turn_off()

    async def _notify_onoff(self, node, onoff):
        await self._state(node, onoff)

    async def _notify_brightness(self, node, brightness):
        await self._state(node, brightness > 0)

    async def _notify_temperature(self, node, temperature):
        await self._state(node, node.retained(Light.OnOffProperty, False))
