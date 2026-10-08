# Using the add-on

## Home Assistant entities

When provisioning succeeds and MQTT is connected, supported lights are published through MQTT discovery as Home Assistant devices and `light.<name>` entities. Home Assistant discovers the entities automatically; add them to dashboards from Home Assistant.

The entity exposes on/off and, if the light advertises the relevant Bluetooth Mesh models, brightness and color temperature. RGB/color controls are not implemented. See [supported devices](supported-devices.md) for the model-to-control mapping.

## Manage paired devices

The **BLE Mesh** panel shows paired devices and provides the available device controls and configuration:

- **Rename:** changes the name shown by the add-on and Home Assistant.
- **Device type:** controls whether the node is treated as a light. Choosing **light** does not provide support for an incompatible device.
- **Relay:** enable only on mains-powered devices. A mesh relay re-broadcasts messages and may extend range. Leave it off for battery devices.
- **Remove:** attempts to reset the device and then forgets it. The device needs to be reachable for the reset to take effect.
- **Force remove:** forgets the device without contacting it. Use this when it is unavailable or normal removal cannot reach it.

The network overview lists mesh addresses, readiness, and relay settings. Confirmed Bluetooth Mesh neighbor/link telemetry is not available, so links are shown as unknown rather than inferred.

## State and physical controls

The gateway displays the latest light state it has observed. It does not continuously poll the light, so changes made using a physical switch may not be reflected until the gateway receives another update.

## Pairing data and backups

The mesh network keys, paired-device information, and settings are stored in the add-on's `/data` directory. They survive add-on updates and restarts and are included in Home Assistant backups. Restore a Home Assistant backup to retain the paired network.

Backups contain mesh network credentials. Store and share them securely.
