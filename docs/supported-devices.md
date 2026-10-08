# Supported devices

## Compatibility summary

This add-on supports **Bluetooth Mesh lights**, not every device that uses Bluetooth. The light must be provisionable onto a Bluetooth Mesh network and expose compatible Bluetooth Mesh SIG lighting server models.

| Device or model | Status | Expected controls |
| --- | --- | --- |
| Ledvance E27 Bluetooth Mesh bulb | Reported tested by this project; exact model/SKU was not recorded | Light controls available in the bulb's advertised capabilities |
| Bluetooth Mesh light with a Generic OnOff Server | Compatible at the model level; specific products have not been verified here | On/off |
| Bluetooth Mesh light with a Light Lightness Server | Compatible at the model level; specific products have not been verified here | On/off and brightness |
| Bluetooth Mesh light with a Light CTL Server | Compatible at the model level; specific products have not been verified here | Brightness and color temperature; on/off requires Generic OnOff support |

There is not yet a verified, SKU-by-SKU compatibility list. Do not assume that every product from a listed manufacturer works: product generations and regional variants can use different radios, mesh protocols, or model sets.

## Not supported

- Bluetooth Low Energy devices that do not use Bluetooth Mesh.
- Zigbee, Wi-Fi, and vendor-specific mesh products.
- RGB/color control and other vendor-specific lighting features.
- Non-light device types as controllable Home Assistant entities.

The add-on may show an unrecognized node as **generic**. Changing its type to **light** only changes how the add-on treats it; it does not add support for an incompatible protocol or model.

## Report a device

When reporting a successful test or compatibility problem, include:

- Manufacturer and exact product name/model/SKU (a photo of the label is useful).
- Firmware version, if known.
- Whether factory reset, scanning, and provisioning succeeded.
- Which controls work: on/off, brightness, and color temperature.
- Home Assistant version, add-on version, adapter model, and relevant sanitized logs.

Please remove passwords, tokens, and other sensitive information from logs before sharing them. Open a report in the [GitHub issue tracker](https://github.com/nitrokart/homeassistant-blemesh2mqtt/issues).
