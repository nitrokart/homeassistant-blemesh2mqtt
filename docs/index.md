# Bluetooth Mesh to MQTT documentation

Pair compatible Bluetooth Mesh lights from Home Assistant and control them through MQTT discovery. The add-on includes a web panel for provisioning and device management; it does not require a vendor cloud or phone app.

![Bluetooth Mesh to MQTT architecture](images/architecture.svg)

## Start here

1. Check the [supported devices](supported-devices.md) page before buying or pairing hardware.
2. Follow the [installation and pairing guide](installation.md).
3. Learn how to [manage paired lights and backups](usage.md).
4. If something goes wrong, use the [troubleshooting guide](troubleshooting.md).

## Project documentation

- [Supported devices and Bluetooth Mesh models](supported-devices.md)
- [Installation, requirements, and pairing](installation.md)
- [Using the add-on and managing devices](usage.md)
- [Troubleshooting](troubleshooting.md)
- [Development and releases](development.md)
- [Release history](../blemesh2mqtt/CHANGELOG.md)

> **Compatibility note:** The device list is intentionally conservative. Only one product is currently recorded as tested, and its exact SKU is unknown. Devices advertising the listed standard models may still behave differently depending on firmware and implementation.

This project is a Home Assistant add-on, so it requires Home Assistant OS or Supervised. See the [installation guide](installation.md) for prerequisites and Bluetooth-adapter sharing warnings.
