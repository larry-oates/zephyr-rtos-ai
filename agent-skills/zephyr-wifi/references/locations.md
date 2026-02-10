# WiFi File Locations in Zephyr

This reference provides the key file locations for WiFi development in Zephyr OS.

## Header Files

### Core WiFi Headers

| Header | Path | Description |
|--------|------|-------------|
| wifi.h | `include/zephyr/net/wifi.h` | Core protocol definitions, security types, status codes |
| wifi_mgmt.h | `include/zephyr/net/wifi_mgmt.h` | Management API, NET_REQUEST/EVENT definitions, driver ops |
| wifi_nm.h | `include/zephyr/net/wifi_nm.h` | Network manager interface |
| wifi_utils.h | `include/zephyr/net/wifi_utils.h` | Channel/band utility functions |
| wifi_credentials.h | `include/zephyr/net/wifi_credentials.h` | Credential storage API |

### Network Management

| Header | Path | Description |
|--------|------|-------------|
| net_mgmt.h | `include/zephyr/net/net_mgmt.h` | net_mgmt() API for WiFi commands |
| net_if.h | `include/zephyr/net/net_if.h` | Network interface helpers |

## Source Files

### WiFi L2 Subsystem

| File | Path | Description |
|------|------|-------------|
| wifi_mgmt.c | `subsys/net/l2/wifi/wifi_mgmt.c` | WiFi management implementation |
| wifi_shell.c | `subsys/net/l2/wifi/wifi_shell.c` | WiFi shell commands |
| wifi_nm.c | `subsys/net/l2/wifi/wifi_nm.c` | Network manager integration |
| wifi_utils.c | `subsys/net/l2/wifi/wifi_utils.c` | Utility functions |
| Kconfig | `subsys/net/l2/wifi/Kconfig` | L2 WiFi Kconfig options |

### Credential Storage

| File | Path | Description |
|------|------|-------------|
| wifi_credentials.c | `subsys/net/lib/wifi_credentials/` | Credential management |
| Kconfig | `subsys/net/lib/wifi_credentials/Kconfig` | Credential Kconfig |

## WiFi Drivers

### Driver Location

All WiFi drivers are in `drivers/wifi/`:

| Driver | Path | Chips/Modules |
|--------|------|---------------|
| nrf_wifi | `drivers/wifi/nrf_wifi/` | Nordic nRF70 series |
| esp32 | `drivers/wifi/esp32/` | ESP32 integrated WiFi |
| eswifi | `drivers/wifi/eswifi/` | Inventek eS-WiFi modules |
| winc1500 | `drivers/wifi/winc1500/` | Microchip WINC1500 |
| esp_at | `drivers/wifi/esp_at/` | ESP-AT firmware modules |
| infineon_airoc | `drivers/wifi/infineon/` | Infineon AIROC |
| simplelink | `drivers/wifi/simplelink/` | TI SimpleLink |

### Driver Kconfig

| File | Path |
|------|------|
| Main driver Kconfig | `drivers/wifi/Kconfig` |
| nRF WiFi Kconfig | `drivers/wifi/nrf_wifi/Kconfig.nrfwifi` |
| ESP32 Kconfig | `drivers/wifi/esp32/Kconfig.esp32` |

## Network Manager (wpa_supplicant)

| Path | Description |
|------|-------------|
| `modules/hostap/` | wpa_supplicant integration |
| `modules/hostap/Kconfig` | wpa_supplicant Kconfig |
| `modules/hostap/src/` | wpa_supplicant source adaptations |

## Documentation

| Path | Description |
|------|-------------|
| `doc/connectivity/networking/api/wifi.rst` | WiFi API documentation |
| `doc/connectivity/networking/api/wifi_credentials.rst` | Credentials API docs |
| `doc/connectivity/networking/` | General networking docs |

## Sample Applications

### WiFi Samples Location

All WiFi samples are in `samples/net/wifi/`:

| Sample | Path | Description |
|--------|------|-------------|
| shell | `samples/net/wifi/shell/` | Comprehensive WiFi shell demo |
| apsta_mode | `samples/net/wifi/apsta_mode/` | Concurrent AP+STA mode |
| test_certs | `samples/net/wifi/test_certs/` | Enterprise certificate testing |

### Related Network Samples

| Sample | Path | Description |
|--------|------|-------------|
| dhcpv4_client | `samples/net/dhcpv4_client/` | DHCP client example |
| sockets | `samples/net/sockets/` | Socket programming examples |

## Test Suites

| Path | Description |
|------|-------------|
| `tests/net/wifi/` | WiFi subsystem tests |
| `tests/net/wifi_credentials/` | Credential storage tests |

## Device Tree Bindings

| Path | Description |
|------|-------------|
| `dts/bindings/wifi/` | WiFi device tree bindings |
| `dts/bindings/wifi/nordic,nrf70.yaml` | nRF70 binding |
| `dts/bindings/wifi/espressif,esp32-wifi.yaml` | ESP32 WiFi binding |

## Board Configurations

### Shields with WiFi

| Shield | Path |
|--------|------|
| nRF7002 shields | `boards/shields/nrf7002*/` |
| M.2 WiFi shields | `boards/shields/nxp_m2_wifi_bt/` |
| MikroE WiFi Click | `boards/shields/mikroe_wifi_bt_click/` |

### Boards with Integrated WiFi

| Board | Path |
|-------|------|
| nRF7002 DK | `boards/nordic/nrf7002dk/` |
| ESP32 boards | `boards/espressif/esp32*/` |
| RPi Pico W | `boards/raspberrypi/rpi_pico/rpi_pico_w.overlay` |

## Quick Reference Paths

```
# Headers
include/zephyr/net/wifi.h
include/zephyr/net/wifi_mgmt.h

# L2 implementation
subsys/net/l2/wifi/

# Drivers
drivers/wifi/<driver_name>/

# wpa_supplicant
modules/hostap/

# Samples
samples/net/wifi/

# Kconfig entry points
drivers/wifi/Kconfig
subsys/net/l2/wifi/Kconfig
modules/hostap/Kconfig

# Documentation
doc/connectivity/networking/api/wifi.rst
```
