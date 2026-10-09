# Changelog

## 0.1.32
- Fix node binding crash: gracefully handle missing or incomplete composition data when a node is added or restarted.

## 0.1.31
- Robust provisioning: automatically retry up to 3 times on RF timeouts, bad-pdu, and busy responses when adding new mesh devices.

## 0.1.30
- UI optimization: debounce brightness and color-temperature slider inputs (250ms) to avoid queue saturation during rapid dragging.

## 0.1.29
- Add-on manifest cleanup: remove deprecated `ingress_port` and obsolete `map` per Home Assistant add-on schema rules.
- Shell script quality: fix SC2155 variable declaration and SC2164 directory change handling in `run.sh`.
- Docker build optimization: preinstall `wheel` in venv to eliminate pip legacy setup.py warnings.

## 0.1.28
- Fix brightness: the lamp's Lightness range is 1..100 (read from the device), not 0..65535. Panel (0-100%) and Home Assistant (1-255) now map onto that range.

## 0.1.27
- Fix brightness control: notify target lightness instead of transient transition present_lightness (which caused brightness to report 0%).
- Fix MQTT brightness set conflict: avoid sending redundant GenericOnOffSet when brightness is explicitly set.
- Redesign Web UI into modern 5-tab dashboard (Devices, Mesh Topology Map, Pairing Wizard, Logs Console, Settings).

## 0.1.26
- Diagnose also reads the device's Lightness range and present Lightness (to debug brightness).

## 0.1.25
- Brightness now uses an acknowledged Light Lightness Set and logs the status the device reports (falls back to unacknowledged if no reply).

## 0.1.24
- Keep the "Raw debug data" panel open across refreshes.
- Brightness slider defaults to 100% (range 1-100); turning a light on from 0% restores full brightness.
- Log every brightness command for debugging.

## 0.1.23
- Fix the web UI showing no devices (render error in the mesh network section introduced in 0.1.22).

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
