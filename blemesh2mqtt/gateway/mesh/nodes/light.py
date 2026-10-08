import asyncio
import logging

from .generic import Generic

from bluetooth_mesh import models


class Light(Generic):
    """
    Generic interface for light nodes

    Tracks the available feature of the light. Currently supports
        - GenericOnOffServer
            - turn on and off
        - LightLightnessServer
            - set brightness
        - LightCTLServer
            - set color temperature

    For now only a single element is supported.
    """

    OnOffProperty = "onoff"
    BrightnessProperty = "brightness"
    TemperatureProperty = "temperature"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._features = set()
        # Device Lightness range; the lamp reports 1..100, not the spec's 0..65535
        self.lightness_min = 1
        self.lightness_max = 100

    def supports(self, property):
        return property in self._features

    def lightness_from_fraction(self, fraction):
        """Map 0..1 to the device's lightness range."""
        value = round(fraction * self.lightness_max)
        return max(self.lightness_min, min(self.lightness_max, value))

    def fraction_from_lightness(self, lightness):
        return max(0.0, min(1.0, lightness / self.lightness_max))

    async def turn_on(self):
        await self.set_onoff_unack(True, transition_time=0.5)

    async def turn_off(self):
        await self.set_onoff_unack(False, transition_time=0.5)

    async def set_brightness(self, brightness):
        if self._is_model_bound(models.LightLightnessServer):
            await self.set_lightness_unack(brightness, transition_time=0.5)
        elif self._is_model_bound(models.LightCTLServer):
            await self.set_ctl_unack(brightness=brightness)

    async def set_kelvin(self, temperature):
        if self._is_model_bound(models.LightCTLServer):
            await self.set_ctl_unack(temperature)

    async def set_mireds(self, temperature):
        if self._is_model_bound(models.LightCTLServer):
            await self.set_ctl_unack(1000000 // temperature)

    async def bind(self, app):
        await super().bind(app)

        if await self.bind_model(models.GenericOnOffServer):
            self._features.add(Light.OnOffProperty)
            await self.get_onoff()

        if await self.bind_model(models.LightLightnessServer):
            self._features.add(Light.OnOffProperty)
            self._features.add(Light.BrightnessProperty)
            await self.get_lightness_range()
            await self.get_lightness()

        if await self.bind_model(models.LightCTLServer):
            self._features.add(Light.TemperatureProperty)
            self._features.add(Light.BrightnessProperty)
            await self.get_ctl()

    async def set_onoff_unack(self, onoff, **kwargs):
        self.notify(Light.OnOffProperty, onoff)

        client = self._app.elements[0][models.GenericOnOffClient]
        await client.set_onoff_unack(self.unicast, self._app.app_keys[0][0], onoff, **kwargs)

    async def get_onoff(self):
        client = self._app.elements[0][models.GenericOnOffClient]
        state = await client.get_light_status([self.unicast], self._app.app_keys[0][0])

        result = state[self.unicast]
        if result is None:
            logging.warn(f"Received invalid result {state}")
        elif not isinstance(result, BaseException):
            self.notify(Light.OnOffProperty, result["present_onoff"])

    async def set_lightness_unack(self, lightness, **kwargs):
        self.notify(Light.BrightnessProperty, lightness)
        if lightness > 0:
            self.notify(Light.OnOffProperty, True)

        client = self._app.elements[0][models.LightLightnessClient]
        await client.set_lightness_unack(self.unicast, self._app.app_keys[0][0], lightness, **kwargs)

    async def set_lightness_ack(self, lightness):
        """Acknowledged set: logs what the device reports it applied."""
        self.notify(Light.BrightnessProperty, lightness)
        if lightness > 0:
            self.notify(Light.OnOffProperty, True)

        client = self._app.elements[0][models.LightLightnessClient]
        app_index = self._app.app_keys[0][0]
        state = await client.set_lightness([self.unicast], lightness, app_index, timeout=5)
        result = state.get(self.unicast)
        if result is None or isinstance(result, BaseException):
            logging.warning(f"Lightness {lightness} on {self.unicast:04x}: no status ({result!r}), resending unacked")
            await client.set_lightness_unack(self.unicast, app_index, lightness, transition_time=0.5)
            return
        logging.info(f"Lightness {lightness} on {self.unicast:04x}: device reports {result}")

    async def get_lightness(self):
        client = self._app.elements[0][models.LightLightnessClient]
        state = await client.get_lightness([self.unicast], self._app.app_keys[0][0])

        result = state[self.unicast]
        if result is None:
            logging.warn(f"Received invalid result {state}")
        elif not isinstance(result, BaseException):
            present = result.get("present_lightness", 0)
            if present > 0:
                self.notify(Light.BrightnessProperty, present)

    async def get_lightness_range(self):
        client = self._app.elements[0][models.LightLightnessClient]
        try:
            state = await client.get_lightness_range([self.unicast], self._app.app_keys[0][0], timeout=6)
            result = state.get(self.unicast)
            if result is None or isinstance(result, BaseException):
                raise TimeoutError("no answer")
            low, high = result.get("range_min", 1), result.get("range_max", 100)
            if 0 < high >= low:
                self.lightness_min, self.lightness_max = max(1, low), high
            logging.info(f"{self} lightness range {self.lightness_min}..{self.lightness_max}")
        except Exception as error:
            logging.warning(f"{self}: lightness range unavailable ({error}); using 1..100")

    async def set_ctl_unack(self, temperature=None, brightness=None, **kwargs):
        if temperature is not None:
            self.notify(Light.TemperatureProperty, temperature)
        else:
            temperature = self.retained(Light.TemperatureProperty, 4000)
        if brightness is not None:
            self.notify(Light.BrightnessProperty, brightness)
        else:
            brightness = self.retained(Light.BrightnessProperty, 65535)

        client = self._app.elements[0][models.LightCTLClient]
        await client.set_ctl_unack(self.unicast, self._app.app_keys[0][0], temperature, brightness, **kwargs)

    async def get_ctl(self):
        client = self._app.elements[0][models.LightCTLClient]
        state = await client.get_ctl([self.unicast], self._app.app_keys[0][0])

        result = state[self.unicast]
        if result is None:
            logging.warn(f"Received invalid result {state}")
        elif isinstance(result, BaseException):
            logging.warning("Could not retrieve CTL state for %s: %s", self, result)
        else:
            self.notify(Light.BrightnessProperty, result["present_ctl_lightness"])
            self.notify(Light.TemperatureProperty, result["present_ctl_temperature"])
