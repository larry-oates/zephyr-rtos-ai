# Zephyr Bluetooth LE Locations

The following locations are relevant for the Bluetooth LE subsystem in Zephyr OS.
Note: `<zephyr-ws-dir>` refers to the Zephyr workspace root (e.g., `zephyr-ws/deps/zephyr`).

## Documentation

| Description | Location |
|-------------|----------|
| BLE Architecture | `<zephyr-ws-dir>/doc/connectivity/bluetooth/bluetooth-arch.rst` |
| LE Host Overview | `<zephyr-ws-dir>/doc/connectivity/bluetooth/bluetooth-le-host.rst` |
| Controller Architecture | `<zephyr-ws-dir>/doc/connectivity/bluetooth/bluetooth-ctlr-arch.rst` |
| Development Guide | `<zephyr-ws-dir>/doc/connectivity/bluetooth/bluetooth-dev.rst` |
| BT Shell Commands | `<zephyr-ws-dir>/doc/connectivity/bluetooth/bluetooth-shell.rst` |
| API Index | `<zephyr-ws-dir>/doc/connectivity/bluetooth/api/index.rst` |
| GAP API | `<zephyr-ws-dir>/doc/connectivity/bluetooth/api/gap.rst` |
| GATT API | `<zephyr-ws-dir>/doc/connectivity/bluetooth/api/gatt.rst` |
| Connection Management | `<zephyr-ws-dir>/doc/connectivity/bluetooth/api/connection_mgmt.rst` |
| L2CAP API | `<zephyr-ws-dir>/doc/connectivity/bluetooth/api/l2cap.rst` |

## Public Headers

| Description | Location |
|-------------|----------|
| Main BT Header | `<zephyr-ws-dir>/include/zephyr/bluetooth/bluetooth.h` |
| Connection API | `<zephyr-ws-dir>/include/zephyr/bluetooth/conn.h` |
| GATT API | `<zephyr-ws-dir>/include/zephyr/bluetooth/gatt.h` |
| GAP Defines | `<zephyr-ws-dir>/include/zephyr/bluetooth/gap.h` |
| UUID Definitions | `<zephyr-ws-dir>/include/zephyr/bluetooth/uuid.h` |
| ATT API | `<zephyr-ws-dir>/include/zephyr/bluetooth/att.h` |
| L2CAP API | `<zephyr-ws-dir>/include/zephyr/bluetooth/l2cap.h` |
| HCI API | `<zephyr-ws-dir>/include/zephyr/bluetooth/hci.h` |
| HCI Types | `<zephyr-ws-dir>/include/zephyr/bluetooth/hci_types.h` |
| Buffers | `<zephyr-ws-dir>/include/zephyr/bluetooth/buf.h` |
| Address Types | `<zephyr-ws-dir>/include/zephyr/bluetooth/addr.h` |
| Crypto API | `<zephyr-ws-dir>/include/zephyr/bluetooth/crypto.h` |

## Service Headers

| Service | Location |
|---------|----------|
| Battery Service (BAS) | `<zephyr-ws-dir>/include/zephyr/bluetooth/services/bas.h` |
| Device Info (DIS) | `<zephyr-ws-dir>/include/zephyr/bluetooth/services/dis.h` |
| Heart Rate (HRS) | `<zephyr-ws-dir>/include/zephyr/bluetooth/services/hrs.h` |
| Nordic UART (NUS) | `<zephyr-ws-dir>/include/zephyr/bluetooth/services/nus.h` |
| Object Transfer (OTS) | `<zephyr-ws-dir>/include/zephyr/bluetooth/services/ots.h` |
| Immediate Alert (IAS) | `<zephyr-ws-dir>/include/zephyr/bluetooth/services/ias.h` |
| Current Time (CTS) | `<zephyr-ws-dir>/include/zephyr/bluetooth/services/cts.h` |

## Source Code

| Component | Location |
|-----------|----------|
| Bluetooth Subsystem Root | `<zephyr-ws-dir>/subsys/bluetooth/` |
| Host Stack | `<zephyr-ws-dir>/subsys/bluetooth/host/` |
| Controller | `<zephyr-ws-dir>/subsys/bluetooth/controller/` |
| Services | `<zephyr-ws-dir>/subsys/bluetooth/services/` |
| Common Code | `<zephyr-ws-dir>/subsys/bluetooth/common/` |
| Crypto | `<zephyr-ws-dir>/subsys/bluetooth/crypto/` |
| Mesh | `<zephyr-ws-dir>/subsys/bluetooth/mesh/` |
| Audio | `<zephyr-ws-dir>/subsys/bluetooth/audio/` |

## Key Host Source Files

| File | Description |
|------|-------------|
| `host/hci_core.c` | HCI core implementation |
| `host/conn.c` | Connection management |
| `host/gatt.c` | GATT implementation |
| `host/att.c` | ATT protocol |
| `host/smp.c` | Security Manager Protocol |
| `host/adv.c` | Advertising |
| `host/scan.c` | Scanning |
| `host/l2cap.c` | L2CAP layer |
| `host/keys.c` | Key management |
| `host/settings.c` | BT settings integration |

## Kconfig Files

| Description | Location |
|-------------|----------|
| Main BT Kconfig | `<zephyr-ws-dir>/subsys/bluetooth/Kconfig` |
| Advertising Kconfig | `<zephyr-ws-dir>/subsys/bluetooth/Kconfig.adv` |
| Logging Kconfig | `<zephyr-ws-dir>/subsys/bluetooth/Kconfig.logging` |
| Host Kconfig | `<zephyr-ws-dir>/subsys/bluetooth/host/Kconfig` |
| GATT Kconfig | `<zephyr-ws-dir>/subsys/bluetooth/host/Kconfig.gatt` |
| L2CAP Kconfig | `<zephyr-ws-dir>/subsys/bluetooth/host/Kconfig.l2cap` |

## Samples

| Sample | Description | Location |
|--------|-------------|----------|
| Peripheral HR | Heart rate peripheral | `<zephyr-ws-dir>/samples/bluetooth/peripheral_hr/` |
| Central HR | Heart rate central | `<zephyr-ws-dir>/samples/bluetooth/central_hr/` |
| Beacon | iBeacon/Eddystone | `<zephyr-ws-dir>/samples/bluetooth/beacon/` |
| Peripheral | Basic peripheral | `<zephyr-ws-dir>/samples/bluetooth/peripheral/` |
| Central | Basic central | `<zephyr-ws-dir>/samples/bluetooth/central/` |
| Broadcaster | Non-connectable advertiser | `<zephyr-ws-dir>/samples/bluetooth/broadcaster/` |
| HCI UART | HCI over UART | `<zephyr-ws-dir>/samples/bluetooth/hci_uart/` |
| Peripheral OTS | Object Transfer | `<zephyr-ws-dir>/samples/bluetooth/peripheral_ots/` |
| Extended Adv | Extended advertising | `<zephyr-ws-dir>/samples/bluetooth/extended_adv/` |
| Direct Adv | Directed advertising | `<zephyr-ws-dir>/samples/bluetooth/direct_adv/` |
| Eddystone | Eddystone beacon | `<zephyr-ws-dir>/samples/bluetooth/eddystone/` |

## Shell Commands

When `CONFIG_BT_SHELL=y` is enabled:

| Command | Description |
|---------|-------------|
| `bt init` | Initialize Bluetooth |
| `bt advertise on` | Start advertising |
| `bt advertise off` | Stop advertising |
| `bt scan on` | Start scanning |
| `bt scan off` | Stop scanning |
| `bt connect <addr>` | Connect to device |
| `bt disconnect` | Disconnect |
| `gatt discover` | Discover services |
| `gatt read <handle>` | Read attribute |
| `gatt write <handle> <data>` | Write attribute |
| `gatt subscribe <handle>` | Subscribe to notifications |

## Tests

| Description | Location |
|-------------|----------|
| Bluetooth Tests | `<zephyr-ws-dir>/tests/bluetooth/` |
| GATT Tests | `<zephyr-ws-dir>/tests/bluetooth/gatt/` |
| Host Tests | `<zephyr-ws-dir>/tests/bluetooth/host/` |
| Controller Tests | `<zephyr-ws-dir>/tests/bluetooth/controller/` |
