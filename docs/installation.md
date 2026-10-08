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

MQTT host, port, and credentials are taken from the Mosquitto add-on. They can be changed in **MQTT connection** in the BLE Mesh panel.

## Pair a light

1. Factory-reset the light and put it into Bluetooth Mesh pairing/provisioning mode. The reset and pairing sequence varies; follow the manufacturer's instructions.
2. Keep the light powered and near the Bluetooth adapter.
3. In the **BLE Mesh** panel, select **Scan for devices** and wait for scanning to finish.
4. Select the discovered device, give it a name, choose the **light** device type, and select **Provision device**.
5. Keep the light powered and in pairing mode while provisioning completes. This can take a few minutes. A successfully provisioned device is shown as **Ready**.
6. Once MQTT is connected, Home Assistant discovers the device and a `light.<name>` entity. Add the entity to a dashboard from Home Assistant.

Only one device can be provisioned at a time. If a discovered node is not a compatible light, selecting the **light** type will not make it compatible.

## Bluetooth adapter notes

- Do not configure the same adapter for simultaneous use by this add-on and Home Assistant Bluetooth.
- Use the add-on's `adapter` option to select the intended `hciN` device. The adapter numbers are available under `/sys/class/bluetooth` on the host.
- On Raspberry Pi 4 onboard Bluetooth, set `io: generic`. If provisioning still fails, see [Raspberry Pi troubleshooting](troubleshooting.md#raspberry-pi-4-provisioning-fails).
