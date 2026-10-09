import asyncio
import logging

from mesh import Node
from mesh.composition import Composition, Element

from bluetooth_mesh import models


class Generic(Node):
    """
    Generic Bluetooth Mesh node

    Provides additional functionality compared to the very basic Node class,
    like composition model helpers and node configuration.
    """

    OnlineProperty = "online"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._composition = None
        if self.composition is not None:
            try:
                # also cleans up non-plain objects persisted by earlier versions
                plain = self._plain(self.composition)
                if self._valid_composition(plain):
                    self.composition = plain
                    self._composition = Composition(plain)
                else:
                    self.composition = None
            except Exception as error:
                logging.warning("Ignoring stored composition for %s: %s", self, error)
                self.composition = None
        # lists all bound model
        self._bound_models = set()

    @classmethod
    def _plain(cls, value):
        """
        Convert parsed construct containers to plain YAML-safe values
        """
        if isinstance(value, dict):
            return {str(k): cls._plain(v) for k, v in value.items() if not str(k).startswith("_")}
        if isinstance(value, (list, tuple, set, frozenset)):
            return [cls._plain(v) for v in value]
        if isinstance(value, bool) or value is None or isinstance(value, (str, float)):
            return value
        if isinstance(value, int):
            return int(value)
        return str(value)

    @staticmethod
    def _valid_composition(data):
        if not (isinstance(data, dict) and isinstance(data.get("elements"), list) and data["elements"]):
            return False
        return all(
            isinstance(e, dict) and isinstance(e.get("sig_models"), list) and isinstance(e.get("vendor_models"), list)
            for e in data["elements"]
        )

    def _is_model_bound(self, model):
        """
        Check if the given model is supported and bound
        """
        return model in self._bound_models

    async def fetch_composition(self):
        """
        Fetch the composition data

        This data contains information about the node's capabilities.
        Use the helper functions to retrieve information.
        """
        client = self._app.elements[0][models.ConfigClient]
        for attempt in range(1, 3):
            logging.info("Requesting composition from %s (attempt %s/2)", self, attempt)
            try:
                data = await client.get_composition_data([self.unicast], net_index=0, timeout=10)
            except asyncio.CancelledError:
                raise
            except Exception as error:
                logging.warning(
                    "Composition request %s/2 failed for %s: %s",
                    attempt,
                    self,
                    error or type(error).__name__,
                )
            else:
                # TODO: multi page composition data support
                node_data = data.get(self.unicast) if isinstance(data, dict) else None
                page_zero = node_data.get("zero") if isinstance(node_data, dict) else None
                page_zero = self._plain(page_zero) if page_zero is not None else None
                if self._valid_composition(page_zero):
                    self.composition = page_zero
                    self._composition = Composition(page_zero)
                    self._app.nodes.persist()
                    logging.info("Received composition from %s (%s element(s))", self, len(page_zero["elements"]))
                    return

                logging.warning("No valid composition data received for %s (attempt %s/2)", self, attempt)

            if attempt < 2:
                await asyncio.sleep(2)

        if self._composition is None:
            logging.warning("No cached composition data available for %s; model discovery is unavailable", self)
        else:
            logging.warning("Using cached composition for %s after radio requests failed", self)

    async def bind(self, app):
        await super().bind(app)

        # update the composition data
        await self.fetch_composition()

        logging.debug(f"Node composition:\n{self._composition}")

    async def bind_model(self, model):
        """
        Bind the given model to the application key

        If the node supports the given model, it is bound to the appliaction key
        and listed within the supported models.

        If the node does not support the given model, the request is skipped.
        """

        if self._composition is None:
            logging.info(f"No composition data for {self}")
            return False

        element = self._composition.element(0)
        if not element or not element.supports(model):
            logging.info(f"{self} does not support {model}")
            return False

        # configure model
        client = self._app.elements[0][models.ConfigClient]
        await client.bind_app_key(
            self.unicast, net_index=0, element_address=self.unicast, app_key_index=self._app.app_keys[0][0], model=model
        )
        self._bound_models.add(model)

        logging.info(f"{self} bound {model}")
        return True
