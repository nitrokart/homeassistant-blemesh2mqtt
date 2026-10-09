# Troubleshooting

## No devices found

- Confirm the light is factory-reset and in Bluetooth Mesh pairing mode. Follow the manufacturer's instructions; reset sequences vary.
- Keep the light powered and close to the adapter during the scan.
- Make sure the adapter is available exclusively to this add-on.

## Provisioning times out or reports `bad-pdu`

The light may have left pairing mode or may not have received the provisioning request.

1. Factory-reset the light and start pairing again.
2. Begin provisioning promptly after the device is found.
3. Move the light close to the Bluetooth adapter and keep it powered.
4. Ensure no other service is using the adapter.
5. If using Raspberry Pi 4 onboard Bluetooth, set `io: generic`.

## Raspberry Pi 4 provisioning fails

Set the add-on option `io` to `generic`. Ensure the Home Assistant Bluetooth integration is not using the onboard adapter. The `auto` backend may fail with the onboard controller.

## Lights stay on "Starting" after an add-on restart

Node model discovery uses Bluetooth Mesh configuration messages. The gateway now binds nodes one at a time, retries composition discovery once, and reuses a previously received composition if the node does not answer. Check the gateway log for `Requesting composition`, `Received composition`, or `Using cached composition` entries. If a node has no cached composition and both radio attempts fail, move it closer to the gateway or a known working relay and restart the add-on.

## Reconfigure gets no response from a device

If reconfiguration times out while adding the application key or fetching composition data, the gateway is not receiving a response from that node. Bluetooth Mesh uses managed flooding rather than a fixed route, so an intermediate light only helps if its Mesh Relay feature is enabled and it can hear and retransmit traffic along the path.

- In the **Devices** tab, verify **Mesh Relay** is enabled for the intermediate light. Check its **Tech Specs** diagnostics for a successful relay probe.
- Keep both lights powered, and check the topology diagnostics for a reachable multi-hop path. A relay cannot help if the radio link to either side is unreliable.
- Reconfigure the intermediate light first if you just enabled its relay setting, then retry the unreachable device.
- A relay setting on the unreachable device itself cannot restore the route to that device; it must first receive the configuration message.

## Light is missing from Home Assistant

- Check that the MQTT broker is running and the Home Assistant MQTT integration is configured.
- Check the **Settings** tab in the BLE Mesh panel to ensure the MQTT broker shows as **Connected**.
- A device configured as `generic` is not exposed as a controllable light. In the **Devices** tab, expand **Tech Specs** and change the type to **light** only if it is a compatible Bluetooth Mesh light.

## Controls are missing

The add-on exposes only capabilities advertised by supported Bluetooth Mesh SIG models. Brightness requires Light Lightness or CTL support; color temperature requires CTL support. RGB/color modes are not supported. See [supported devices](supported-devices.md).

## Add-on panel reports an error during restart

If the panel reports `Unexpected non-whitespace character after JSON`, ingress may have returned a `502` while the add-on was restarting. Wait for `Web UI listening on port 8099` in the add-on log, then reload the panel.

## Collect logs and ask for help

1. Set `log_level` to `debug`.
2. Reproduce the problem and save the add-on log.
3. Remove passwords, tokens, and other sensitive information.
4. Open an issue in the [GitHub issue tracker](https://github.com/nitrokart/homeassistant-blemesh2mqtt/issues) with the add-on version, Home Assistant version, adapter, device model/SKU, and steps to reproduce.

Do not post unredacted credentials, MQTT passwords, or Home Assistant backups.
