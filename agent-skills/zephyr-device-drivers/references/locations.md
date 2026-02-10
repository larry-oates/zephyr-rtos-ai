# Zephyr Driver Locations

## Table of Contents

1. [Driver Source Code](#driver-source-code)
2. [Devicetree Bindings](#devicetree-bindings)
3. [Samples and Examples](#samples-and-examples)
4. [Tests](#tests)
5. [Documentation](#documentation)

---

## Driver Source Code

### Main Driver Directories

| Path | Contents |
|------|----------|
| `zephyr/drivers/` | All driver implementations |
| `zephyr/drivers/gpio/` | GPIO drivers |
| `zephyr/drivers/i2c/` | I2C bus drivers |
| `zephyr/drivers/spi/` | SPI bus drivers |
| `zephyr/drivers/sensor/` | Sensor drivers |
| `zephyr/drivers/serial/` | UART/Serial drivers |
| `zephyr/drivers/adc/` | ADC drivers |
| `zephyr/drivers/pwm/` | PWM drivers |
| `zephyr/drivers/flash/` | Flash memory drivers |
| `zephyr/drivers/display/` | Display drivers |
| `zephyr/drivers/led/` | LED drivers |
| `zephyr/drivers/kscan/` | Keyboard scan drivers |
| `zephyr/drivers/rtc/` | Real-time clock drivers |
| `zephyr/drivers/watchdog/` | Watchdog drivers |
| `zephyr/drivers/counter/` | Counter/Timer drivers |
| `zephyr/drivers/can/` | CAN bus drivers |
| `zephyr/drivers/bluetooth/` | Bluetooth HCI drivers |
| `zephyr/drivers/wifi/` | WiFi drivers |
| `zephyr/drivers/ethernet/` | Ethernet drivers |

### Sensor Driver Subdirectories

| Path | Sensor Type |
|------|-------------|
| `drivers/sensor/adi/` | Analog Devices sensors |
| `drivers/sensor/bosch/` | Bosch sensors (BME280, BMP388, etc.) |
| `drivers/sensor/st/` | STMicroelectronics sensors (LIS2DH, LSM6DSO, etc.) |
| `drivers/sensor/ti/` | Texas Instruments sensors |
| `drivers/sensor/invensense/` | InvenSense/TDK sensors (MPU6050, ICM42688, etc.) |
| `drivers/sensor/sensirion/` | Sensirion sensors (SHT4x, SCD4x, etc.) |
| `drivers/sensor/asahi_kasei/` | AKM sensors (AK09918, etc.) |

### Header Files

| Path | Contents |
|------|----------|
| `zephyr/include/zephyr/drivers/` | Public driver API headers |
| `zephyr/include/zephyr/drivers/gpio.h` | GPIO API |
| `zephyr/include/zephyr/drivers/i2c.h` | I2C API |
| `zephyr/include/zephyr/drivers/spi.h` | SPI API |
| `zephyr/include/zephyr/drivers/sensor.h` | Sensor API |
| `zephyr/include/zephyr/drivers/uart.h` | UART API |

---

## Devicetree Bindings

### Binding Locations

| Path | Contents |
|------|----------|
| `zephyr/dts/bindings/` | All devicetree bindings |
| `zephyr/dts/bindings/gpio/` | GPIO controller bindings |
| `zephyr/dts/bindings/i2c/` | I2C controller bindings |
| `zephyr/dts/bindings/spi/` | SPI controller bindings |
| `zephyr/dts/bindings/sensor/` | Sensor device bindings |
| `zephyr/dts/bindings/serial/` | UART bindings |
| `zephyr/dts/bindings/base/` | Base bindings (base.yaml, i2c-device.yaml, etc.) |

### Common Base Bindings

| File | Use For |
|------|---------|
| `base/base.yaml` | All devices (provides status, compatible) |
| `base/i2c-device.yaml` | I2C slave devices |
| `base/spi-device.yaml` | SPI slave devices |
| `base/uart-device.yaml` | UART child devices |
| `gpio/gpio-controller.yaml` | GPIO controllers |

### Finding Bindings by Compatible

```bash
# Search for a specific compatible string
find $ZEPHYR_BASE/dts/bindings -name "*.yaml" | xargs grep -l "compatible.*bme280"

# List all sensor bindings
ls $ZEPHYR_BASE/dts/bindings/sensor/
```

---

## Samples and Examples

### Driver Samples

| Path | Description |
|------|-------------|
| `zephyr/samples/basic/blinky/` | Basic GPIO LED example |
| `zephyr/samples/basic/button/` | GPIO button with interrupt |
| `zephyr/samples/drivers/` | All driver samples |
| `zephyr/samples/drivers/gpio/` | GPIO-specific samples |
| `zephyr/samples/drivers/i2c_scanner/` | I2C bus scanner |
| `zephyr/samples/drivers/spi_flash/` | SPI flash usage |
| `zephyr/samples/drivers/adc/` | ADC reading samples |
| `zephyr/samples/drivers/pwm/` | PWM control samples |
| `zephyr/samples/drivers/uart/` | UART samples |

### Sensor Samples

| Path | Description |
|------|-------------|
| `zephyr/samples/sensor/` | All sensor samples |
| `zephyr/samples/sensor/bme280/` | BME280 temperature/pressure/humidity |
| `zephyr/samples/sensor/bme680/` | BME680 air quality |
| `zephyr/samples/sensor/lis2dh/` | LIS2DH accelerometer |
| `zephyr/samples/sensor/lsm6dso/` | LSM6DSO IMU |
| `zephyr/samples/sensor/thermometer/` | Generic temperature sensor |
| `zephyr/samples/sensor/accel_polling/` | Generic accelerometer polling |

### Application-Level Samples

| Path | Description |
|------|-------------|
| `zephyr/samples/boards/` | Board-specific examples |
| `zephyr/samples/bluetooth/peripheral_hr/` | BLE with sensor data |
| `zephyr/samples/net/sockets/echo_server/` | Network with driver usage |

---

## Tests

### Driver Tests

| Path | Contents |
|------|----------|
| `zephyr/tests/drivers/` | All driver tests |
| `zephyr/tests/drivers/gpio/` | GPIO driver tests |
| `zephyr/tests/drivers/i2c/` | I2C driver tests |
| `zephyr/tests/drivers/spi/` | SPI driver tests |
| `zephyr/tests/drivers/sensor/` | Sensor driver tests |
| `zephyr/tests/drivers/uart/` | UART driver tests |
| `zephyr/tests/drivers/adc/` | ADC driver tests |
| `zephyr/tests/drivers/flash/` | Flash driver tests |
| `zephyr/tests/drivers/build_all/` | Build smoke tests |

### Emulator Tests

| Path | Contents |
|------|----------|
| `zephyr/tests/drivers/gpio/gpio_emul/` | GPIO emulator tests |
| `zephyr/tests/drivers/i2c/i2c_emul/` | I2C emulator tests |
| `zephyr/tests/drivers/spi/spi_emul/` | SPI emulator tests |

### Running Driver Tests

```bash
# Run all driver tests on native_sim
west twister -T tests/drivers/ -p native_sim

# Run specific driver test
west twister -T tests/drivers/sensor/bme280/

# Run with hardware (e.g., nRF52840 DK)
west twister -T tests/drivers/gpio/ -p nrf52840dk_nrf52840 --device-testing
```

---

## Documentation

### Driver Documentation

| Path | Contents |
|------|----------|
| `zephyr/doc/hardware/` | Hardware and driver docs |
| `zephyr/doc/hardware/peripherals/` | Peripheral driver guides |
| `zephyr/doc/hardware/peripherals/gpio.rst` | GPIO documentation |
| `zephyr/doc/hardware/peripherals/i2c.rst` | I2C documentation |
| `zephyr/doc/hardware/peripherals/spi.rst` | SPI documentation |
| `zephyr/doc/hardware/peripherals/sensor.rst` | Sensor subsystem docs |
| `zephyr/doc/hardware/porting/` | Porting guides |

### Online Documentation

| Resource | URL |
|----------|-----|
| Zephyr Docs | https://docs.zephyrproject.org/latest/ |
| Driver API Reference | https://docs.zephyrproject.org/latest/doxygen/html/group__io__interfaces.html |
| Devicetree Guide | https://docs.zephyrproject.org/latest/build/dts/ |
| Sensor API | https://docs.zephyrproject.org/latest/doxygen/html/group__sensor__interface.html |

---

## Quick Reference Commands

```bash
# Find driver by compatible string
grep -r "DT_DRV_COMPAT.*bme280" $ZEPHYR_BASE/drivers/

# Find all drivers for a chip vendor
ls $ZEPHYR_BASE/drivers/sensor/bosch/

# Find binding for a device
find $ZEPHYR_BASE/dts/bindings -name "*bme280*"

# Find sample for a driver
find $ZEPHYR_BASE/samples -name "*bme280*" -type d

# Find tests for a driver
find $ZEPHYR_BASE/tests/drivers -name "*bme280*" -type d

# List all sensor drivers
ls $ZEPHYR_BASE/drivers/sensor/

# Search for driver API usage in samples
grep -r "sensor_sample_fetch" $ZEPHYR_BASE/samples/

# Find Kconfig for a driver
find $ZEPHYR_BASE/drivers -name "Kconfig*" | xargs grep -l "BME280"
```

---

## Out-of-Tree Driver Locations

For custom drivers in your project:

```
my_project/
├── drivers/
│   └── my_driver/
│       ├── CMakeLists.txt
│       ├── Kconfig
│       └── my_driver.c
├── dts/
│   └── bindings/
│       └── vendor,my-device.yaml
├── boards/
│   └── my_board.overlay
├── CMakeLists.txt
└── prj.conf
```

### CMakeLists.txt Integration

```cmake
# Add before find_package(Zephyr)
list(APPEND ZEPHYR_EXTRA_MODULES ${CMAKE_CURRENT_SOURCE_DIR}/drivers/my_driver)
list(APPEND DTS_ROOT ${CMAKE_CURRENT_SOURCE_DIR})
```
