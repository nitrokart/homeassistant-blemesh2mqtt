#!/usr/bin/with-contenv bashio

ADAPTER="$(bashio::config 'adapter')"
MESH_IO="$(bashio::config 'io')"
if [ -z "$MESH_IO" ] || [ "$MESH_IO" = "null" ]; then
    MESH_IO=auto
fi
export LOG_LEVEL="$(bashio::config 'log_level')"
MESH_DEBUG=()
if [ "$LOG_LEVEL" = "debug" ] || [ "$LOG_LEVEL" = "trace" ]; then
    MESH_DEBUG+=(--debug --dbus-debug)
fi

# defaults for the UI-managed MQTT settings
if bashio::services.available mqtt; then
    export MQTT_HOST="$(bashio::services mqtt host)"
    export MQTT_PORT="$(bashio::services mqtt port)"
    export MQTT_USER="$(bashio::services mqtt username)"
    export MQTT_PASSWORD="$(bashio::services mqtt password)"
fi

mkdir -p /run/dbus /data/meshd/config /data/meshd/storage
rm -f /run/dbus/pid
dbus-uuidgen --ensure=/data/meshd/machine-id
cp /data/meshd/machine-id /etc/machine-id
dbus-uuidgen --ensure
dbus-daemon --system --fork

# the generic io backend needs the adapter down (user channel)
if [ "$MESH_IO" = "generic" ]; then
    python3 - "$ADAPTER" <<'PY' || echo "could not power down hci${ADAPTER}" >&2
import fcntl, socket, sys
s = socket.socket(31, socket.SOCK_RAW, 1)
fcntl.ioctl(s, 0x400448CA, int(sys.argv[1]))
print("hci%s brought down" % sys.argv[1])
PY
fi

# the mesh daemon needs exclusive access to the adapter
/opt/bluez/bin/bluetooth-meshd --nodetach \
    "${MESH_DEBUG[@]}" \
    --io="${MESH_IO}:hci${ADAPTER}" \
    --config=/data/meshd/config \
    --storage=/data/meshd/storage &

if [ ${#MESH_DEBUG[@]} -gt 0 ] && command -v btmon >/dev/null; then
    (btmon --no-pager 2>&1 | sed -u 's/^/BTMON /') &
fi

mesh_ready=false
for _ in {1..60}; do
    if dbus-send --system --print-reply --dest=org.bluez.mesh \
        /org/bluez/mesh org.freedesktop.DBus.Introspectable.Introspect 2>/dev/null \
        | grep -q 'org.bluez.mesh.Network1'; then
        mesh_ready=true
        break
    fi
    sleep 1
done

if [ "$mesh_ready" != true ]; then
    echo "bluetooth-meshd did not expose org.bluez.mesh.Network1 within 60 seconds" >&2
    echo "D-Bus introspection at /org/bluez/mesh:" >&2
    dbus-send --system --print-reply --dest=org.bluez.mesh \
        /org/bluez/mesh org.freedesktop.DBus.Introspectable.Introspect 2>&1 >&2 || true
    exit 1
fi

cd /opt/blemesh/gateway
exec /opt/venv/bin/python gateway.py --basedir /data --reload
