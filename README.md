# Bluetooth Mesh to MQTT — Home Assistant add-on

[![CI](https://github.com/nitrokart/homeassistant-blemesh2mqtt/actions/workflows/ci.yml/badge.svg)](https://github.com/nitrokart/homeassistant-blemesh2mqtt/actions/workflows/ci.yml)
[![Add repository to my Home Assistant](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fnitrokart%2Fhomeassistant-blemesh2mqtt)

Pair Bluetooth Mesh lights (tested with a Ledvance E27 bulb) from a web UI and control them in Home Assistant through MQTT discovery. No cloud, no phone app.

Fork of [dominikberse/homeassistant-bluetooth-mesh](https://github.com/dominikberse/homeassistant-bluetooth-mesh), with fixes for Raspberry Pi onboard Bluetooth, a new UI, and packaging.

## Requirements

- Home Assistant OS or Supervised (add-ons are required).
- An MQTT broker (e.g. the Mosquitto add-on).
- A Bluetooth adapter the add-on can use exclusively. A USB dongle is the safest choice. The Raspberry Pi 4 onboard chip works with `io: generic` (see below).

## Install

1. Click the badge above, or go to **Settings → Add-ons → Add-on Store → ⋮ → Repositories** and add:
   `https://github.com/nitrokart/homeassistant-blemesh2mqtt`
2. Install **Bluetooth Mesh to MQTT**. The image is built on your device the first time (10–20 minutes on a Pi).
3. On a Raspberry Pi 4 set the option `io` to `generic`. Start the add-on.
4. Open **BLE Mesh** in the sidebar, put the bulb in pairing mode, scan, and provision it.

Alternative: copy the `blemesh2mqtt/` folder to the `/addons` share and install it under *Local add-ons*.

## Usage

Full guide: [blemesh2mqtt/DOCS.md](blemesh2mqtt/DOCS.md). Changes: [CHANGELOG](blemesh2mqtt/CHANGELOG.md).

- Pairing data is stored in `/data` and survives updates.
- Each paired light shows up as an MQTT device (`light.<name>`). Home Assistant does not add it to dashboards automatically.
- Devices paired as `generic` have no on/off; change the type to `light` in the UI.
- Turn on **relay** only for mains-powered devices; it extends the mesh range.
- The UI does not show live on/off state (not read back from the device).

## Options

| Option | Default | Description |
|---|---|---|
| `adapter` | `0` | HCI index (`hciN`) used by `bluetooth-meshd` |
| `io` | `auto` | `auto`, `generic` (raw HCI) or `mgmt` |
| `log_level` | `info` | `debug`, `info`, `warning`, `error` |

When adding options in development, bump `version` in `config.yaml` so Home Assistant refreshes them.

## Troubleshooting

- **`Unexpected non-whitespace character after JSON` in the UI**: ingress returned `502` because the add-on was restarting. Wait for `Web UI listening on port 8099` in the log and reload.
- **Raspberry Pi 4**: use `io: generic`. With `auto` the controller rejects `LE Set Random Address` and provisioning packets are never sent. The image builds BlueZ 5.87 `bluetooth-meshd` and patches it so the Remote Provisioning client model exists after Attach.
- **`bad-pdu` while provisioning**: the bulb didn't answer within ~60 s. Start provisioning while the bulb is in pairing mode, disable the HA Bluetooth integration if it shares the adapter, and try `io: generic`.
- **Device cannot be switched**: it is `generic`; change its type to `light`.
- **Debug logs**: set `log_level: debug` and follow with `ha apps logs local_blemesh2mqtt -f`.

## Development

- CI (`.github/workflows/ci.yml`): black, compile check, shellcheck, yamllint, UI script syntax, add-on linter, Docker build for amd64 and aarch64.
- Release: bump `version` in `blemesh2mqtt/config.yaml`, add a `## <version>` entry to the CHANGELOG, then push tag `vX.Y.Z`. The release workflow checks the tag matches and publishes the notes.
- Run without HA: set `ALLOWED_IPS`, then `python3 gateway.py --basedir <dir>` in `blemesh2mqtt/gateway` (needs `bluetooth-meshd` and a system D-Bus).

## License

No license file yet. The upstream project does not declare one; pick and add a license before wider reuse.
