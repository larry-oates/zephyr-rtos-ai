# I2C Kconfig Reference

Complete Kconfig reference for Zephyr I2C subsystem.

## Table of Contents

1. [Core Options](#core-options)
2. [Async/RTIO Options](#asyncrtio-options)
3. [Target Mode Options](#target-mode-options)
4. [Shell/Debug Options](#shelldebug-options)
5. [Bus Recovery Options](#bus-recovery-options)
6. [Driver-Specific Options](#driver-specific-options)

---

## Core Options

### CONFIG_I2C

```kconfig
menuconfig I2C
    bool "Inter-Integrated Circuit (I2C) bus drivers"
```
Main enabler for I2C driver subsystem.

### CONFIG_I2C_INIT_PRIORITY

```kconfig
config I2C_INIT_PRIORITY
    int "I2C device driver initialization priority"
    default KERNEL_INIT_PRIORITY_DEVICE
    depends on I2C
```
Init priority for I2C drivers.

### CONFIG_I2C_CALLBACK

```kconfig
config I2C_CALLBACK
    bool "I2C asynchronous callback API"
    depends on I2C
```
Enable async `i2c_transfer_cb()` API.

### CONFIG_I2C_ALLOW_NO_STOP_TRANSACTIONS

```kconfig
config I2C_ALLOW_NO_STOP_TRANSACTIONS
    bool "Allow I2C transfers with no STOP"
    select DEPRECATED
```
**Deprecated.** Allow transfers without STOP on last message.

---

## Async/RTIO Options

### CONFIG_I2C_RTIO

```kconfig
config I2C_RTIO
    bool "I2C RTIO API"
    select EXPERIMENTAL
    select RTIO
    select RTIO_WORKQ
```
Enable Real-Time I/O subsystem for I2C. Experimental.

### CONFIG_I2C_RTIO_SQ_SIZE

```kconfig
config I2C_RTIO_SQ_SIZE
    int "Submission queue size for blocking calls"
    default 4
    depends on I2C_RTIO
```

### CONFIG_I2C_RTIO_CQ_SIZE

```kconfig
config I2C_RTIO_CQ_SIZE
    int "Completion queue size for blocking calls"
    default 4
    depends on I2C_RTIO
```

### CONFIG_I2C_RTIO_FALLBACK_MSGS

```kconfig
config I2C_RTIO_FALLBACK_MSGS
    int "i2c_msg structs for fallback handler"
    default 4
    depends on I2C_RTIO
```

---

## Target Mode Options

### CONFIG_I2C_TARGET

```kconfig
menuconfig I2C_TARGET
    bool "I2C Target drivers"
```
Enable I2C target (slave) mode support.

### CONFIG_I2C_TARGET_INIT_PRIORITY

```kconfig
config I2C_TARGET_INIT_PRIORITY
    int "Target driver init priority"
    default 60
    depends on I2C_TARGET
```

### CONFIG_I2C_TARGET_BUFFER_MODE

```kconfig
config I2C_TARGET_BUFFER_MODE
    bool "I2C target driver buffer mode"
    select EXPERIMENTAL
    depends on I2C_TARGET
```
Enable buffer-mode callbacks for target drivers.

### CONFIG_I2C_EEPROM_TARGET

```kconfig
config I2C_EEPROM_TARGET
    bool "Virtual I2C Target EEPROM driver"
```
Built-in virtual EEPROM target driver.

### CONFIG_I2C_EEPROM_TARGET_RUNTIME_ADDR

```kconfig
config I2C_EEPROM_TARGET_RUNTIME_ADDR
    bool "Change virtual EEPROM address at runtime"
    depends on I2C_EEPROM_TARGET
```

### Target Buffer Size Options

| Option | Default | Range | Description |
|--------|---------|-------|-------------|
| `CONFIG_I2C_INFINEON_CAT1_TARGET_BUF` | 64 | 1-1024 | Infineon CAT1 target buffer |
| `CONFIG_I2C_INFINEON_XMC4_TARGET_BUF` | 64 | 1-1024 | Infineon XMC4 target buffer |
| `CONFIG_I2C_TARGET_IT8XXX2_MAX_BUF_SIZE` | 256 | 4-2044 | ITE IT8XXX2 target buffer |
| `CONFIG_I2C_TARGET_IT51XXX_MAX_BUF_SIZE` | 256 | - | ITE IT51XXX target FIFO |
| `CONFIG_I2C_NRFX_TWIS_BUF_SIZE` | 64 | - | Nordic TWIS DMA buffer |

### CONFIG_I2C_TARGET_ALLOW_POWER_SAVING

```kconfig
config I2C_TARGET_ALLOW_POWER_SAVING
    bool "Allow target to enter low power when idle"
    select EXPERIMENTAL
    depends on I2C_TARGET && !SOC_IT8XXX2_REG_SET_V1
```

---

## Shell/Debug Options

### CONFIG_I2C_SHELL

```kconfig
config I2C_SHELL
    bool "I2C Shell"
    depends on SHELL
```
Enable I2C shell commands (scan, read, write, recover).

### CONFIG_I2C_STATS

```kconfig
config I2C_STATS
    bool "I2C device stats"
    depends on STATS
```
Enable I2C transfer statistics.

### CONFIG_I2C_DUMP_MESSAGES

```kconfig
config I2C_DUMP_MESSAGES
    bool "Log all I2C transactions"
    depends on LOG && I2C_LOG_LEVEL_DBG
```
Debug logging of all I2C transactions.

### CONFIG_I2C_DUMP_MESSAGES_ALLOWLIST

```kconfig
config I2C_DUMP_MESSAGES_ALLOWLIST
    bool "Allowlist for I2C transaction logging"
    depends on I2C_DUMP_MESSAGES
    depends on DT_HAS_ZEPHYR_I2C_DUMP_ALLOWLIST_ENABLED
```
Limit message dumping to specific devices.

---

## Bus Recovery Options

GPIO-based bus recovery support (varies by driver):

| Option | Driver | Description |
|--------|--------|-------------|
| `CONFIG_I2C_AMBIQ_BUS_RECOVERY` | Ambiq | GPIO bitbang recovery |
| `CONFIG_I2C_MCUX_LPI2C_BUS_RECOVERY` | NXP LPI2C | GPIO bitbang recovery |
| `CONFIG_I2C_MCUX_FLEXCOMM_BUS_RECOVERY` | NXP FlexComm | GPIO bitbang recovery |
| `CONFIG_I2C_OMAP_BUS_RECOVERY` | TI OMAP | Bitbang recovery |
| `CONFIG_I2C_STM32_BUS_RECOVERY` | STM32 | GPIO bitbang recovery |

All select `CONFIG_I2C_BITBANG`.

### CONFIG_I2C_BITBANG

```kconfig
config I2C_BITBANG
    bool "Software-driven bit-banging I2C library"
```
Base library for software I2C implementation.

### CONFIG_I2C_GPIO

```kconfig
config I2C_GPIO
    bool "GPIO bit-banging I2C driver"
    select I2C_BITBANG
    default y
    depends on DT_HAS_GPIO_I2C_ENABLED
```
Pure GPIO software I2C driver.

### CONFIG_I2C_GPIO_CLOCK_STRETCHING

```kconfig
config I2C_GPIO_CLOCK_STRETCHING
    bool "Clock stretching support"
    default y
    depends on I2C_GPIO
```

### CONFIG_I2C_GPIO_CLOCK_STRETCHING_TIMEOUT_US

```kconfig
config I2C_GPIO_CLOCK_STRETCHING_TIMEOUT_US
    int "Clock stretching timeout (us)"
    default 100000
    depends on I2C_GPIO
```

---

## Driver-Specific Options

### DMA/Interrupt Options

| Option | Driver | Description |
|--------|--------|-------------|
| `CONFIG_I2C_DW_LPSS_DMA` | DesignWare | DMA for async transfers |
| `CONFIG_I2C_STM32_INTERRUPT` | STM32 | Interrupt support (default y) |
| `CONFIG_I2C_STM32_V2_DMA` | STM32 V2 | DMA support (experimental) |
| `CONFIG_I2C_MAX32_INTERRUPT` | MAX32 | Interrupt support (default y) |
| `CONFIG_I2C_MAX32_DMA` | MAX32 | DMA support |
| `CONFIG_I2C_SAM0_DMA_DRIVEN` | SAM0 | DMA-driven transactions |
| `CONFIG_I2C_SILABS_DMA` | Silabs | DMA support |

### Timeout Options

| Option | Driver | Default | Description |
|--------|--------|---------|-------------|
| `CONFIG_I2C_DW_RW_TIMEOUT_MS` | DesignWare | 100 | Read/write timeout |
| `CONFIG_I2C_SILABS_TIMEOUT` | Silabs | 1000 | Transfer timeout (ms) |
| `CONFIG_I2C_STM32_TRANSFER_TIMEOUT_MSEC` | STM32 | 500 | Transfer timeout |
| `CONFIG_I2C_SAM0_TRANSFER_TIMEOUT` | SAM0 | 500 | Transfer timeout |
| `CONFIG_I2C_NRFX_TRANSFER_TIMEOUT` | Nordic | 500 | Transfer timeout (0=forever) |
| `CONFIG_I2C_NXP_TRANSFER_TIMEOUT` | NXP FlexComm | 0 | Transfer timeout (0=forever) |
| `CONFIG_I2C_WCH_XFER_TIMEOUT_MS` | WCH | 500 | Transfer timeout |

### DesignWare Extended

```kconfig
config I2C_DW_CLOCK_SPEED
    int "I2C clock speed"
    default 110 if I2C_RTS5912
    default 32
    depends on I2C_DW

config I2C_DW_EXTENDED_SUPPORT
    bool "Enable extended DesignWare features"
```
SCL/SDA timeout and other extensions.

### I2C Switch Options

```kconfig
menuconfig I2C_TCA954X
    bool "TCA954x I2C switch"
    default y
    depends on DT_HAS_TI_TCA9546A_ENABLED || ...

config I2C_TCA954X_ROOT_INIT_PRIO
    int "Root driver init priority"
    default I2C_INIT_PRIORITY
    depends on I2C_TCA954X

config I2C_TCA954X_CHANNEL_INIT_PRIO
    int "Channel driver init priority"
    default I2C_INIT_PRIORITY
    depends on I2C_TCA954X
```

### Emulation

```kconfig
config I2C_EMUL
    bool "I2C emulator driver"
    default y
    depends on DT_HAS_ZEPHYR_I2C_EMUL_CONTROLLER_ENABLED && EMUL
```
For testing without hardware.

---

## Common Driver Enable Options

Most drivers auto-enable based on devicetree. Pattern:

```kconfig
config I2C_<VENDOR>
    bool "<Vendor> I2C driver"
    default y
    depends on DT_HAS_<VENDOR>_<COMPAT>_ENABLED
    select PINCTRL  # common dependency
```

Major drivers:
- `CONFIG_I2C_STM32` - STMicroelectronics
- `CONFIG_I2C_NRFX` - Nordic (TWI/TWIM)
- `CONFIG_I2C_ESP32` - Espressif
- `CONFIG_I2C_MCUX_LPI2C` - NXP i.MX RT
- `CONFIG_I2C_MCUX_FLEXCOMM` - NXP LPC
- `CONFIG_I2C_SAM_TWI` / `TWIM` / `TWIHS` - Atmel SAM
- `CONFIG_I2C_DW` - Synopsys DesignWare
- `CONFIG_I2C_GD32` - GigaDevice
- `CONFIG_I2C_GECKO` - Silicon Labs EFM32
- `CONFIG_I2C_RENESAS_*` - Renesas RA/RZ
- `CONFIG_I2C_XEC` / `XEC_V2` - Microchip XEC

---

## Quick Reference

### Minimal Configuration

```kconfig
# prj.conf
CONFIG_I2C=y
```

### Debug Configuration

```kconfig
CONFIG_I2C=y
CONFIG_I2C_SHELL=y
CONFIG_I2C_DUMP_MESSAGES=y
CONFIG_LOG=y
CONFIG_I2C_LOG_LEVEL_DBG=y
```

### Async Configuration

```kconfig
CONFIG_I2C=y
CONFIG_I2C_CALLBACK=y
# or for RTIO:
CONFIG_I2C_RTIO=y
```

### Target Mode Configuration

```kconfig
CONFIG_I2C=y
CONFIG_I2C_TARGET=y
CONFIG_I2C_EEPROM_TARGET=y  # optional built-in target
```
