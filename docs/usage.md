# Using the add-on

## Home Assistant entities

When provisioning succeeds and MQTT is connected, supported lights are published through MQTT discovery as Home Assistant devices and `light.<name>` entities. Home Assistant discovers the entities automatically; add them to dashboards from Home Assistant.

The entity exposes on/off and, if the light advertises the relevant Bluetooth Mesh models, brightness and color temperature. RGB/color controls are not implemented. See [supported devices](supported-devices.md) for the model-to-control mapping.

## Manage paired devices and mesh network

The **BLE Mesh** panel uses a modern tabbed layout (inspired by Zigbee2MQTT and Home Assistant):

### 1. Devices Tab
- **Direct light controls:** on/off toggle, brightness slider (1–100%), and color temperature slider (Kelvin/Mireds) for lights with Light CTL support.
- **Inline rename:** click the pencil icon next to a device name to rename it in both the add-on and Home Assistant.
- **Tech Specs (Engineer Drawer):** click **Tech Specs** on any device card to inspect:
  - **Packet Round-Trip Time (RTT):** confirmed response latency from the device.
  - **Hop Distance:** measured hop count from the gateway.
  - **Default TTL & Network Transmit:** configured packet transmit and retransmit parameters.
  - **Mesh Relay:** toggle message re-broadcasting. Enable only on mains-powered devices to extend range; leave off for battery devices.
  - **Device Type:** select `light` or `generic`.
  - **Diagnose:** actively probes confirmed hop distance, default TTL, network transmit parameters, and lightness ranges.
  - **Reconfigure:** re-sends keys and bindings.
  - **Remove & Force Remove:** reset and forget the device, or force-forget an unreachable device.
  - **Raw Diagnostics JSON:** view and copy unparsed BlueZ telemetry.

### 2. Mesh Topology Tab
- **Interactive SVG graph:** displays the central Home Assistant gateway and concentric rings distinguishing direct single-hop links from multi-hop mesh paths.
- **Relay repeaters:** highlights active mesh relay nodes with animated halos.
- **Network telemetry:** provides summary metrics including total node count, active relay count, and average network round-trip time.
- **Node selection:** clicking any node in the topology map highlights its link and opens its card in the Devices tab.

### 3. Add Device (Pairing Wizard)
- **Guided workflow:** 3-step stepper guiding through Preparation, Scanning, and Provisioning.
- **Radar scanner:** animated visual scanner with live RSSI signal meter (4-bar signal indicator with dBm reading) for unprovisioned devices.
- **Provisioning setup:** assign device name, type, and mesh relay setting before provisioning into the network.

### 4. Gateway Logs Tab
- **Real-time console:** streaming add-on log with color-coded severity levels (Info, Warning, Error).
- **Search & level filtering:** instant text/regex search and filter chips.
- **Controls:** auto-scroll lock toggle and one-click copy to clipboard.

### 5. Settings Tab
- **MQTT Broker:** configure broker host, port, username, and password with real-time connection status.
- **Mesh Parameters:** overview of Gateway unicast address and IV index.
- **Troubleshooting FAQ:** built-in reference for pairing, factory resetting, and mesh best practices.

## State and physical controls

The gateway displays the latest light state it has observed. It does not continuously poll the light, so changes made using a physical switch may not be reflected until the gateway receives another update.

## Pairing data and backups

The mesh network keys, paired-device information, and settings are stored in the add-on's `/data` directory. They survive add-on updates and restarts and are included in Home Assistant backups. Restore a Home Assistant backup to retain the paired network.

Backups contain mesh network credentials. Store and share them securely.
