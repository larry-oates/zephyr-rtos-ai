# Kconfig Examples

Complete patterns for common Zephyr Kconfig scenarios.

## Table of Contents

1. [Simple Driver Toggle](#simple-driver-toggle)
2. [Driver with Parameters](#driver-with-parameters)
3. [Subsystem with Feature Flags](#subsystem-with-feature-flags)
4. [Mutually Exclusive Choices](#mutually-exclusive-choices)
5. [Module Integration](#module-integration)
6. [Board-Specific Configuration](#board-specific-configuration)
7. [Application with App-Specific Options](#application-with-app-specific-options)

---

## Simple Driver Toggle

Enable/disable a driver with hardware dependency.

```kconfig
# drivers/sensor/my_sensor/Kconfig

config MY_SENSOR
    bool "My Sensor Driver"
    default y
    depends on I2C
    help
      Enable driver for My Sensor over I2C bus.
```

**prj.conf:**
```
CONFIG_I2C=y
CONFIG_MY_SENSOR=y
```

---

## Driver with Parameters

Driver with configurable parameters.

```kconfig
# drivers/sensor/my_sensor/Kconfig

menuconfig MY_SENSOR
    bool "My Sensor Driver"
    depends on I2C
    help
      Enable My Sensor driver.

if MY_SENSOR

config MY_SENSOR_POLL_INTERVAL_MS
    int "Polling interval in milliseconds"
    default 100
    range 10 10000
    help
      How often to poll the sensor.

config MY_SENSOR_TRIGGER
    bool "Enable trigger mode"
    depends on GPIO
    help
      Use GPIO interrupt instead of polling.

config MY_SENSOR_I2C_ADDR
    hex "I2C address"
    default 0x48
    help
      I2C slave address of the sensor.

endif # MY_SENSOR
```

**prj.conf:**
```
CONFIG_I2C=y
CONFIG_MY_SENSOR=y
CONFIG_MY_SENSOR_POLL_INTERVAL_MS=50
CONFIG_MY_SENSOR_TRIGGER=y
```

---

## Subsystem with Feature Flags

Subsystem with optional features.

```kconfig
# subsys/my_subsystem/Kconfig

menuconfig MY_SUBSYSTEM
    bool "My Subsystem"
    help
      Enable My Subsystem.

if MY_SUBSYSTEM

config MY_SUBSYSTEM_FEATURE_A
    bool "Enable Feature A"
    default y
    help
      Feature A provides...

config MY_SUBSYSTEM_FEATURE_B
    bool "Enable Feature B"
    select REQUIRES_HEAP
    help
      Feature B requires heap allocation.

config MY_SUBSYSTEM_LOG_LEVEL
    int "Log level (0=off, 4=debug)"
    default 3
    range 0 4
    depends on LOG
    help
      Set logging verbosity.

endif # MY_SUBSYSTEM
```

---

## Mutually Exclusive Choices

Select one backend from multiple options.

```kconfig
# subsys/storage/Kconfig

menuconfig STORAGE
    bool "Storage subsystem"

if STORAGE

choice STORAGE_BACKEND
    prompt "Storage backend"
    default STORAGE_FLASH

config STORAGE_FLASH
    bool "Flash storage"
    depends on FLASH
    help
      Use internal flash for storage.

config STORAGE_EEPROM
    bool "EEPROM storage"
    depends on EEPROM
    help
      Use external EEPROM.

config STORAGE_SD
    bool "SD Card storage"
    depends on DISK_ACCESS
    help
      Use SD card via FAT filesystem.

endchoice

endif # STORAGE
```

**prj.conf:**
```
CONFIG_STORAGE=y
CONFIG_STORAGE_SD=y
```

---

## Module Integration

External module with Zephyr integration.

**Directory structure:**
```
my_module/
├── zephyr/
│   └── module.yml
├── Kconfig
├── CMakeLists.txt
└── src/
    └── my_module.c
```

**zephyr/module.yml:**
```yaml
build:
  cmake: .
  kconfig: Kconfig
```

**Kconfig:**
```kconfig
config MY_MODULE
    bool "My External Module"
    help
      Enable my external module functionality.

if MY_MODULE

config MY_MODULE_BUFFER_SIZE
    int "Buffer size"
    default 256

endif # MY_MODULE
```

**CMakeLists.txt:**
```cmake
if(CONFIG_MY_MODULE)
  zephyr_library()
  zephyr_library_sources(src/my_module.c)
endif()
```

---

## Board-Specific Configuration

Different defaults per board.

```kconfig
config MY_DRIVER_DMA
    bool "Use DMA for transfers"
    default y if SOC_SERIES_STM32F4X
    default y if SOC_SERIES_NRF52X
    default n
    depends on DMA
    help
      Enable DMA acceleration. Enabled by default on
      capable SoCs.

config MY_DRIVER_BUFFER_SIZE
    int "Transfer buffer size"
    default 4096 if SOC_SERIES_STM32F4X
    default 1024 if SOC_SERIES_NRF52X
    default 512
    help
      Size varies based on available RAM.
```

---

## Application with App-Specific Options

Application-level Kconfig.

**app/Kconfig:**
```kconfig
mainmenu "My Application Configuration"

config APP_VERSION_MAJOR
    int "Major version"
    default 1

config APP_VERSION_MINOR
    int "Minor version"
    default 0

config APP_DEVICE_NAME
    string "Device name"
    default "MyDevice"

config APP_FEATURE_ADVANCED
    bool "Enable advanced features"
    default n
    select LOG
    select SENSOR
    help
      Enables advanced features that require
      logging and sensor subsystems.

menu "Network Settings"
    visible if NETWORKING

config APP_SERVER_HOST
    string "Server hostname"
    default "api.example.com"

config APP_SERVER_PORT
    int "Server port"
    default 8080
    range 1 65535

endmenu

source "Kconfig.zephyr"
```

**prj.conf:**
```
CONFIG_APP_DEVICE_NAME="ProductionUnit"
CONFIG_APP_FEATURE_ADVANCED=y
CONFIG_APP_SERVER_PORT=443
```

---

## Using in C Code

Access configured values:

```c
#include <zephyr/kernel.h>

/* Boolean check */
#if defined(CONFIG_MY_FEATURE)
    /* Feature enabled */
#endif

/* Integer value */
#define BUFFER_SIZE CONFIG_MY_BUFFER_SIZE

/* String value */
const char *name = CONFIG_APP_DEVICE_NAME;

/* Conditional compilation */
#ifdef CONFIG_MY_SENSOR_TRIGGER
static void sensor_trigger_handler(void) { ... }
#endif
```
