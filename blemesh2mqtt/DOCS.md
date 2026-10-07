# Bluetooth Mesh to MQTT

Control Bluetooth Mesh lights (for example Ledvance Smart+ bulbs) from Home Assistant. The add-on pairs the lights with a Bluetooth Mesh network that lives on your Home Assistant host and publishes them through MQTT discovery. Open the **BLE Mesh** panel in the sidebar to pair and manage devices.

## Before you start

- An **MQTT broker** (the Mosquitto add-on) and the **MQTT integration** in Home Assistant.
- A **Bluetooth adapter** the add-on can use exclusively. The mesh daemon takes over the adapter, so other Bluetooth features that use the same adapter stop working. A dedicated USB Bluetooth 5 dongle is the safest option. The Raspberry Pi 4 onboard chip works with `io: generic`, but Home Assistant's own Bluetooth integration must not use it.
- Mains-powered mesh lights that are **factory reset** (not paired to another app or hub).

## Options

| Option | Default | Description |
| --- | --- | --- |
| `adapter` | `0` | Number N of the adapter `hciN` (`ls /sys/class/bluetooth`). |
| `io` | `auto` | Mesh I/O backend: `auto`, `generic` (raw HCI) or `mgmt`. **Raspberry Pi onboard Bluetooth: use `generic`.** |
| `log_level` | `info` | `debug` also enables BlueZ mesh and `btmon` traces. Use it when reporting a problem. |

MQTT settings are taken from the Mosquitto add-on automatically and can be changed in the web UI (MQTT connection).

## Pair a light

1. Put the light in pairing mode (usually: switch it off and on 3 to 5 times until it blinks or pulses).
2. Open the **BLE Mesh** panel, press **Scan for devices** and wait 10 seconds.
3. Press **Pair this device**, enter a name, keep the type on **light** and press **Provision device**.
4. Wait up to a few minutes. Keep the light powered, in pairing mode and close to the host. The device appears as **Ready**.
5. The light shows up in Home Assistant as a device and `light.<name>` entity.

**Mesh relay:** turn it on for mains-powered devices. They re-broadcast mesh messages, which extends range. Leave it off for battery devices. You can change it later in the device card.

## Everything pairing-related is stored in `/data`

The mesh network keys, the paired devices and the settings live in the add-on data folder. They survive add-on updates and restarts and are included in Home Assistant backups. Restore a backup to keep your paired lights.

## Known limitations

- Only lights (on/off, brightness, color temperature if the device reports it) are supported. Other device types appear as `generic` and cannot be controlled.
- The UI shows no live on/off state of a light. State changes made with the physical switch are not reported unless the device publishes them.
- One pairing at a time. The first install builds BlueZ from source and can take 10 to 20 minutes on a Raspberry Pi.

## Support

Report problems on GitHub and attach the add-on log with `log_level: debug`. Remove passwords from the log first.
