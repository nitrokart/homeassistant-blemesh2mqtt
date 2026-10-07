ARG BUILD_ARCH=aarch64
FROM ghcr.io/home-assistant/${BUILD_ARCH}-base-debian:bookworm AS bluez-build

# the distro BlueZ 5.66 cannot send mesh packets on the Pi 4 controller
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential ca-certificates curl xz-utils pkg-config \
        libdbus-1-dev libglib2.0-dev libudev-dev libical-dev libreadline-dev libjson-c-dev \
    && rm -rf /var/lib/apt/lists/*
RUN cd /tmp \
    && curl -fsSLO https://mirrors.edge.kernel.org/pub/linux/libs/ell/ell-0.83.tar.xz \
    && tar xf ell-0.83.tar.xz && cd ell-0.83 \
    && ./configure --prefix=/opt/bluez && make -j2 && make install
RUN cd /tmp \
    && curl -fsSLO https://mirrors.edge.kernel.org/pub/linux/bluetooth/bluez-5.87.tar.xz \
    && tar xf bluez-5.87.tar.xz && cd bluez-5.87 \
    && perl -0pi -e 's/(attach->provisioner = node->provisioner;)/$1\n\tif (attach->provisioner) { struct node_element *pe = l_queue_find(attach->elements, match_element_idx, L_UINT_TO_PTR(PRIMARY_ELE_IDX)); if (pe && mesh_model_add(attach, pe->models, REM_PROV_CLI_MODEL, NULL)) remote_prov_client_init(attach, PRIMARY_ELE_IDX); }/' mesh/node.c \
    && grep -c 'remote_prov_client_init(attach' mesh/node.c \
    && PKG_CONFIG_PATH=/opt/bluez/lib/pkgconfig LDFLAGS="-Wl,-rpath,/opt/bluez/lib" \
       ./configure --prefix=/opt/bluez --enable-mesh --enable-external-ell \
         --disable-systemd --disable-udev --disable-obex --disable-cups --disable-manpages \
         --disable-client --disable-tools --disable-monitor --disable-test --disable-deprecated \
    && make -j2 mesh/bluetooth-meshd \
    && install -D mesh/bluetooth-meshd /opt/bluez/bin/bluetooth-meshd

FROM ghcr.io/home-assistant/${BUILD_ARCH}-base-debian:bookworm

# bluez-meshd ships bluetooth-meshd, so BlueZ does not need to be compiled
RUN apt-get update && apt-get install -y --no-install-recommends \
        bluez-meshd \
        bluez \
        dbus \
        git \
        build-essential \
        libdbus-1-dev \
        libglib2.0-dev \
        libffi-dev \
        libssl-dev \
        python3 \
        python3-dev \
        python3-pip \
        python3-venv \
    && rm -rf /var/lib/apt/lists/*

COPY --from=bluez-build /opt/bluez /opt/bluez

WORKDIR /opt/blemesh
COPY requirements.txt .
COPY dbus/blemesh2mqtt.conf /etc/dbus-1/system.d/blemesh2mqtt.conf
RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --ignore-requires-python -r requirements.txt

COPY gateway /opt/blemesh/gateway
COPY run.sh /run.sh
RUN chmod +x /run.sh

CMD ["/run.sh"]
