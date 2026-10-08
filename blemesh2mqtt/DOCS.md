# Bluetooth Mesh to MQTT

Pair compatible Bluetooth Mesh lights with Home Assistant. This add-on provisions devices from the **BLE Mesh** panel and exposes supported lights through MQTT discovery.

> This is a Home Assistant add-on, not a Home Assistant Core integration. It requires Home Assistant OS or Supervised, an MQTT broker, and a Bluetooth adapter used exclusively by this add-on.

## Quick start

1. Add `https://github.com/nitrokart/homeassistant-blemesh2mqtt` in **Settings → Add-ons → Add-on Store → ⋮ → Repositories**.
2. Install **Bluetooth Mesh to MQTT**. On Raspberry Pi 4 using onboard Bluetooth, set `io` to `generic`.
3. Start the add-on and open **BLE Mesh** from the sidebar.
4. Factory-reset a compatible light, open the **Add Device** tab, scan, and provision it.
5. After MQTT connects, add the discovered `light.<name>` entity to a dashboard from Home Assistant.

The first installation builds BlueZ and can take 10–20 minutes on a Raspberry Pi. The Bluetooth adapter must not also be used by Home Assistant's Bluetooth integration.

## Device compatibility

| Device or model | Status |
| --- | --- |
| Ledvance E27 Bluetooth Mesh bulb | Reported tested; exact model/SKU is not recorded |
| Bluetooth Mesh SIG Generic OnOff, Light Lightness, or Light CTL lights | Model-level compatibility; individual products are not verified |

BLE-only, Zigbee, Wi-Fi, and vendor-specific mesh devices are not supported. RGB/color control is not implemented. Check the [full supported-device guide](https://github.com/nitrokart/homeassistant-blemesh2mqtt/blob/master/docs/supported-devices.md) before buying hardware.

## Add-on options

| Option | Default | Description |
| --- | --- | --- |
| `adapter` | `0` | Bluetooth adapter index (`hciN`). |
| `io` | `auto` | Mesh I/O backend: `auto`, `generic`, or `mgmt`. Use `generic` for Raspberry Pi 4 onboard Bluetooth. |
| `log_level` | `info` | Log verbosity. `debug` enables detailed Bluetooth traces. |

## Full documentation

Browse the [complete documentation](https://github.com/nitrokart/homeassistant-blemesh2mqtt/tree/master/docs) for detailed setup, device management, backups, and troubleshooting.

Please report tested device model/SKU and sanitized logs in the [GitHub issue tracker](https://github.com/nitrokart/homeassistant-blemesh2mqtt/issues).
