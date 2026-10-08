# Changelog

## 0.1.22
- Add per-device Diagnose: heartbeat-confirmed hop distance, default TTL, network transmit, relay, proxy, friend and beacon state with round-trip times, plus raw debug JSON.
- Show scan signal strength (RSSI) for unpaired devices.

## 0.1.21
- Prevent Home Assistant Ingress from caching the web UI HTML.

## 0.1.20
- Add direct brightness and color-temperature controls for capable lights, with corrected MQTT brightness scaling and CTL state reporting.
- Add device renaming and a mesh overview that marks unavailable topology links as unknown rather than inferring them.

## 0.1.19
- Clearer provisioning errors (timeout, device did not answer).
- No more harmless "Missing handler" warnings for the gateway's own MQTT publishes.

## 0.1.18
- Fix: empty red status pill shown in the UI header when no job is running.

## 0.1.17
- Redesigned web UI: device cards with On/Off, device type and mesh relay controls, step-by-step pairing guide, warnings (MQTT disconnected, generic devices, relay tip), progress banner, copyable log, dark mode.
- Lights are registered as Home Assistant devices (not only entities).
- Device type can be changed after pairing; mesh relay can be switched on or off after pairing.
- MQTT discovery config is published retained, so Home Assistant finds the light after a restart.
- Fix: Raspberry Pi 4 onboard Bluetooth pairing. BlueZ 5.87 `bluetooth-meshd` is built into the image and patched so the Remote Provisioning client exists, and the new `io` option (`generic`) bypasses the controller that rejects `LE Set Random Address`.
- Fix: MQTT status stays connected when no devices are paired yet.
- The saved MQTT broker and username are trimmed.

## 0.1.16
- Lights are registered as Home Assistant devices; discovery is retained; Pi 4 onboard Bluetooth fix; MQTT status fix.

## 0.1.0
- Initial add-on packaging: scan, provision and configure Bluetooth Mesh lights from the web UI and expose them over MQTT discovery.
