import logging

from .generic import Generic

from bluetooth_mesh import models


class Switch(Generic):
    """
    Generic interface for switch nodes

    Supports the GenericOnOffServer model for turning a switch or plug on and off.
    For now only a single element is supported.
    """

    OnOffProperty = "onoff"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._features = set()

    def supports(self, property):
        return property in self._features

    async def turn_on(self):
        await self.set_onoff_unack(True, transition_time=0.5)

    async def turn_off(self):
        await self.set_onoff_unack(False, transition_time=0.5)

    async def bind(self, app):
        await super().bind(app)

        if await self.bind_model(models.GenericOnOffServer):
            self._features.add(Switch.OnOffProperty)
            await self.get_onoff()

    async def set_onoff_unack(self, onoff, **kwargs):
        self.notify(Switch.OnOffProperty, onoff)

        client = self._app.elements[0][models.GenericOnOffClient]
        await client.set_onoff_unack(self.unicast, self._app.app_keys[0][0], onoff, **kwargs)

    async def get_onoff(self):
        client = self._app.elements[0][models.GenericOnOffClient]
        state = await client.get_light_status([self.unicast], self._app.app_keys[0][0])

        result = state[self.unicast]
        if result is None:
            logging.warning(f"Received invalid result {state}")
        elif not isinstance(result, BaseException):
            self.notify(Switch.OnOffProperty, result["present_onoff"])
