# Bluetooth Mesh to MQTT

[![CI](https://github.com/nitrokart/homeassistant-blemesh2mqtt/actions/workflows/ci.yml/badge.svg)](https://github.com/nitrokart/homeassistant-blemesh2mqtt/actions/workflows/ci.yml)
[![Add repository to my Home Assistant](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fnitrokart%2Fhomeassistant-blemesh2mqtt)

Provision compatible Bluetooth Mesh lights from Home Assistant and control them through MQTT discovery. No vendor cloud or phone app is required.

![Bluetooth Mesh to MQTT architecture](docs/images/architecture.svg)

> **Compatibility:** one Ledvance E27 Bluetooth Mesh bulb is reported tested, but the exact model is not recorded. Other products are not verified by SKU. Check the [supported devices](docs/supported-devices.md) before buying hardware.

## Get started

1. Make sure you use Home Assistant OS or Supervised, have an MQTT broker and MQTT integration, and have a Bluetooth adapter this add-on can use exclusively.
2. Select the **Add repository to my Home Assistant** badge above, or add `https://github.com/nitrokart/homeassistant-blemesh2mqtt` under **Settings → Add-ons → Add-on Store → ⋮ → Repositories**.
3. Install **Bluetooth Mesh to MQTT**. For Raspberry Pi 4 onboard Bluetooth, set `io` to `generic` in the add-on configuration.
4. Start the add-on, open **BLE Mesh** from the sidebar, factory-reset a compatible light, then scan and provision it.
5. Once MQTT is connected, Home Assistant discovers a `light.<name>` entity. Add it to a dashboard from Home Assistant.

The first install builds BlueZ from source and may take 10–20 minutes on a Raspberry Pi. Follow the [full installation and pairing guide](docs/installation.md) for details.

## Documentation

- [Documentation home](docs/index.md)
- [Supported devices and capabilities](docs/supported-devices.md)
- [Installation and pairing](docs/installation.md)
- [Using the add-on and backups](docs/usage.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Development and releases](docs/development.md)
- [Home Assistant add-on documentation](blemesh2mqtt/DOCS.md)
- [Changelog](blemesh2mqtt/CHANGELOG.md)

## Important notes

- The add-on takes exclusive control of its Bluetooth adapter. Do not share that adapter with Home Assistant's Bluetooth integration or another Bluetooth service.
- Only compatible Bluetooth Mesh lighting models are supported. BLE-only, Zigbee, Wi-Fi, vendor-specific mesh protocols, and RGB/color controls are not supported.
- Mesh credentials and device settings are saved in `/data` and included in Home Assistant backups. Keep backups private.
- This project is a fork of [dominikberse/homeassistant-bluetooth-mesh](https://github.com/dominikberse/homeassistant-bluetooth-mesh), with Raspberry Pi onboard Bluetooth fixes, a new UI, and add-on packaging.

## License

There is currently no `LICENSE` file. Without an explicit license, this repository is not yet licensed for reuse, modification, or redistribution. A license must be chosen and added before inviting the public to reuse this project as open source.
