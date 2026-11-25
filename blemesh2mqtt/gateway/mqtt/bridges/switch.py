from mqtt.bridge import HassMqttBridge


class GenericSwitchBridge(HassMqttBridge):
    """
    Generic bridge for switches and plugs
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def component(self):
        return "switch"

    async def config(self, node):
        message = {
            "~": self._messenger.node_topic(self.component, node),
            "name": node.config.optional("name"),
            "unique_id": node.config.require("id"),
            "object_id": node.config.require("id"),
            "command_topic": "~/set",
            "state_topic": "~/state",
            "payload_on": '{"state": "ON"}',
            "payload_off": '{"state": "OFF"}',
            "state_on": "ON",
            "state_off": "OFF",
            "value_template": "{{ value_json.state }}",
            "device": {
                "identifiers": [f"blemesh_{node.config.require('id')}"],
                "name": node.config.optional("name"),
                "manufacturer": "Bluetooth Mesh",
                "model": "Switch",
            },
        }

        await self._messenger.publish(self.component, node, "config", message, retain=True)

    async def _state(self, node, onoff):
        """
        Send the switch's on/off state
        """
        message = {"state": "ON" if onoff else "OFF"}
        await self._messenger.publish(self.component, node, "state", message, retain=True)

    async def _mqtt_set(self, node, payload):
        if payload.get("state") == "ON":
            await node.turn_on()
        elif payload.get("state") == "OFF":
            await node.turn_off()

    async def _notify_onoff(self, node, onoff):
        await self._state(node, onoff)
