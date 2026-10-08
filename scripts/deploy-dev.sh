#!/bin/sh
# Dev deploy to the Pi: stages blemesh2mqtt/ without the `image:` line so the
# Supervisor builds locally instead of pulling from GHCR. Git keeps the line for PRD.
set -eu

cd "$(dirname "$0")/.."
HOST="hassio@192.168.1.250"
KEY="$HOME/.ssh/ha_blemesh2mqtt"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

COPYFILE_DISABLE=1 tar --exclude=__pycache__ --exclude=.DS_Store -C blemesh2mqtt -cf - . | tar -C "$STAGE" -xf -
sed -i.bak '/^image:/d' "$STAGE/config.yaml" && rm "$STAGE/config.yaml.bak"

S="ssh -i $KEY -o IdentitiesOnly=yes $HOST"
COPYFILE_DISABLE=1 tar -C "$STAGE" -cf - . | $S 'sudo -n rm -rf /addons/blemesh2mqtt && sudo -n mkdir -p /addons/blemesh2mqtt && sudo -n tar -C /addons/blemesh2mqtt -xf -'
$S 'sh -lc "ha store reload; ha apps update local_blemesh2mqtt; ha apps info local_blemesh2mqtt | grep -E \"^(state|version|version_latest)\""'
