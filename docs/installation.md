# Installation and pairing

## Requirements

- Home Assistant OS or Supervised. This project is a Home Assistant add-on and is not installed as a Home Assistant Core integration.
- An MQTT broker, such as the Mosquitto add-on, and the MQTT integration configured in Home Assistant.
- A Bluetooth adapter the add-on can use **exclusively**. The mesh daemon takes over the adapter while running. Do not share it with Home Assistant's Bluetooth integration or another Bluetooth service. A dedicated USB adapter is recommended.
- A compatible, mains-powered Bluetooth Mesh light that has been factory-reset and is not paired to another app, hub, or mesh network.

Check the [supported device list](supported-devices.md) before purchasing hardware.

The Raspberry Pi 4 onboard Bluetooth adapter can work with `io: generic`. The Home Assistant Bluetooth integration must not use that same adapter.

## Install the add-on

1. In Home Assistant, open **Settings → Add-ons → Add-on Store**.
2. Open the store menu (**⋮ → Repositories**) and add:
   `https://github.com/nitrokart/homeassistant-blemesh2mqtt`
3. Find **Bluetooth Mesh to MQTT** in the store and select **Install**.
4. Open the add-on's **Configuration** tab and set the options below if needed. For a Raspberry Pi 4 using onboard Bluetooth, set `io` to `generic`.
5. Start the add-on. The first installation builds BlueZ from source and may take 10–20 minutes on a Raspberry Pi.
6. Open **BLE Mesh** in the Home Assistant sidebar.

Alternatively, copy the `blemesh2mqtt/` directory to Home Assistant's `/addons` share and install it as a local add-on.

## Add-on options

| Option | Default | Description |
| --- | --- | --- |
| `adapter` | `0` | Bluetooth HCI adapter index (`hciN`; `0` selects `hci0`). |
| `io` | `auto` | Mesh I/O backend: `auto`, `generic` (raw HCI), or `mgmt`. Use `generic` for Raspberry Pi 4 onboard Bluetooth. |
| `log_level` | `info` | Log verbosity. `debug` also enables detailed BlueZ mesh and Bluetooth traces. |

MQTT host, port, and credentials are automatically populated from the Mosquitto add-on (or supervisor environment). They can also be viewed and updated in the **Settings** tab in the BLE Mesh panel.

## Pair a light

1. Factory-reset the light and put it into Bluetooth Mesh pairing/provisioning mode. For most smart bulbs: switch off and on 3 to 5 times until the bulb blinks rapidly.
2. Keep the light powered and within 2–3 metres of the Bluetooth adapter during pairing.
3. In the **BLE Mesh** panel, switch to the **Add Device** tab and select **Start Discovery Scan (10s)**.
4. When the device appears in the discovered list (showing its UUID and live RSSI signal strength), select **Configure & Pair**.
5. Give the device a friendly name, select the **light** device type, choose whether to enable **Mesh Relay** (recommended for mains-powered lights), and click **Provision into Mesh**.
6. Keep the light powered and in pairing mode while provisioning completes. Once finished, the device appears in the **Devices** tab as **Online**.
7. Once MQTT is connected, Home Assistant automatically discovers the device and a `light.<name>` entity. Add the entity to your dashboards from Home Assistant.

Only one device can be provisioned at a time. If a discovered node is not a compatible light, selecting the **light** type will not make it compatible.

## Bluetooth adapter notes

- Do not configure the same adapter for simultaneous use by this add-on and Home Assistant Bluetooth.
- Use the add-on's `adapter` option to select the intended `hciN` device. The adapter numbers are available under `/sys/class/bluetooth` on the host.
- On Raspberry Pi 4 onboard Bluetooth, set `io: generic`. If provisioning still fails, see [Raspberry Pi troubleshooting](troubleshooting.md#raspberry-pi-4-provisioning-fails).
