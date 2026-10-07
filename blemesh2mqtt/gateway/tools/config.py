import copy
import logging

import yaml


def _merge(base, override):
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge(result[key], value)
        else:
            result[key] = value
    return result


class Config:
    def __init__(self, filename=None, config=None, defaults=None):
        self._filename = filename
        self._defaults = defaults or {}

        if self._filename:
            try:
                with open(self._filename, "r") as config_file:
                    self._user = yaml.safe_load(config_file) or {}
            except FileNotFoundError:
                self._user = {}

        elif config is not None:
            self._user = config

        else:
            raise Exception("Invalid config initialization")

        self._rebuild()

    def _rebuild(self):
        self._config = _merge(self._defaults, self._user)

    def _get(self, path, section, info):
        if "." in path:
            prefix, remainder = path.split(".", 1)
            subsection = self._get(prefix, section, info)
            return self._get(remainder, subsection, info)

        if path not in section:
            if "raise" in info:
                raise info["raise"]
            return info["fallback"]

        return section[path]

    def require(self, path):
        return self._get(
            path,
            self._config,
            {
                "raise": Exception(f"{path} missing in config"),
            },
        )

    def optional(self, path, fallback=None):
        return self._get(
            path,
            self._config,
            {
                "fallback": fallback,
            },
        )

    def node_config(self, uuid):
        """
        Get config for given node
        """
        mesh = self.optional("mesh", None) or {}

        for id, info in mesh.items():
            if info.get("uuid") == str(uuid):
                return Config(config={"id": id, **info})

        logging.warning(f"Missing configuration for node {uuid}")
        return Config(config={})

    def items(self):
        return self._config.items()

    @property
    def user(self):
        """
        Settings saved by the user, without defaults
        """
        return self._user

    def persist(self):
        with open(self._filename, "w") as config_file:
            yaml.safe_dump(self._user, config_file)

    def set_mqtt(self, values):
        self._user["mqtt"] = values
        self._rebuild()
        self.persist()

    def set_node(self, id, info):
        mesh = self._user.setdefault("mesh", {})

        # a uuid must only be configured once
        for other, other_info in list(mesh.items()):
            if other_info.get("uuid") == info["uuid"]:
                del mesh[other]

        mesh[id] = info
        self._rebuild()
        self.persist()

    def remove_node(self, uuid):
        mesh = self._user.get("mesh") or {}

        for id, info in list(mesh.items()):
            if info.get("uuid") == str(uuid):
                del mesh[id]

        self._rebuild()
        self.persist()
