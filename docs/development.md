# Development

## Checks

CI runs the checks defined in `.github/workflows/ci.yml`, including:

- Black formatting and Python compile checks.
- ShellCheck and yamllint.
- Web UI JavaScript syntax validation.
- Home Assistant add-on linting.
- Docker builds for `amd64` and `aarch64`.

Run the relevant CI checks before submitting changes.

## Local gateway

To run the gateway outside Home Assistant, set `ALLOWED_IPS` and run `python3 gateway.py --basedir <dir>` from `blemesh2mqtt/gateway`. A working `bluetooth-meshd` and system D-Bus are required.

## Release process

1. Bump `version` in `blemesh2mqtt/config.yaml`.
2. Add a matching `## <version>` entry to `blemesh2mqtt/CHANGELOG.md`.
3. Merge to `main`. The `publish.yml` workflow builds and pushes `ghcr.io/nitrokart/<arch>-blemesh2mqtt:<version>` for `amd64` and `aarch64`, skipping versions that already exist.
4. Wait for the publish workflow to succeed, then push a `vX.Y.Z` tag. The release workflow validates the version and publishes the changelog notes.

Home Assistant pulls the prebuilt image named by `image` in `config.yaml`. If the image for a version is missing, installing or updating to it fails, so confirm the publish workflow succeeded before announcing a release.

### One-time setup

After the first publish, open each package under the repository owner's **Packages** page on GitHub and set its visibility to **Public**, so Home Assistant can pull it without credentials.

When changing add-on options, bump the version so Home Assistant refreshes the configuration schema.
