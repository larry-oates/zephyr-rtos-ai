# SPI Kconfig Reference

Complete reference for SPI-related Kconfig options in Zephyr.

## Core Options

### CONFIG_SPI

```kconfig
CONFIG_SPI=y
```

Master toggle to enable Serial Peripheral Interface (SPI) bus drivers.

**Dependencies:** None
**Default:** n

---

### CONFIG_SPI_ASYNC

```kconfig
CONFIG_SPI_ASYNC=y
```

Enable asynchronous API calls (`spi_transceive_cb`, `spi_transceive_signal`).

**Dependencies:** `MULTITHREADING`
**Selects:** `POLL`
**Default:** n

---

### CONFIG_SPI_SLAVE

```kconfig
CONFIG_SPI_SLAVE=y
```

Enable SPI slave/peripheral mode operations. Support depends on driver and hardware.

**Status:** Experimental
**Default:** n

---

### CONFIG_SPI_EXTENDED_MODES

```kconfig
CONFIG_SPI_EXTENDED_MODES=y
```

Enable extended operations: dual, quad, and octal line modes (`SPI_LINES_DUAL`, `SPI_LINES_QUAD`, `SPI_LINES_OCTAL`).

**Status:** Experimental
**Default:** n

---

## RTIO Support

### CONFIG_SPI_RTIO

```kconfig
CONFIG_SPI_RTIO=y
```

Enable RTIO (Real-Time I/O) API for SPI.

**Status:** Experimental
**Selects:** `RTIO`, `RTIO_WORKQ`
**Default:** n

### CONFIG_SPI_RTIO_FALLBACK_MSGS

```kconfig
CONFIG_SPI_RTIO_FALLBACK_MSGS=4
```

Number of spi_buf structs for RTIO fallback handler when driver doesn't implement native RTIO.

**Dependencies:** `SPI_RTIO`
**Default:** 4

---

## Shell and Debugging

### CONFIG_SPI_SHELL

```kconfig
CONFIG_SPI_SHELL=y
```

Enable SPI shell for interactive debugging and simple transceive operations.

**Dependencies:** `SHELL`
**Default:** n

**Shell commands:**
- `spi transceive <device> <bytes...>` - Perform SPI transfer
- `spi conf <device> <freq> <mode>` - Configure SPI device

### CONFIG_SPI_SHELL_MAX_DEVICE_SLOTS

```kconfig
CONFIG_SPI_SHELL_MAX_DEVICE_SLOTS=16
```

Number of device slots in SPI shell. Increase if you see "not enough space" errors.

**Dependencies:** `SPI_SHELL`
**Default:** 16

---

## Statistics

### CONFIG_SPI_STATS

```kconfig
CONFIG_SPI_STATS=y
```

Enable SPI device statistics (TX bytes, RX bytes, transfer errors).

**Dependencies:** `STATS`
**Default:** n

---

## Initialization

### CONFIG_SPI_INIT_PRIORITY

```kconfig
CONFIG_SPI_INIT_PRIORITY=50
```

Device driver initialization priority.

**Default:** `KERNEL_INIT_PRIORITY_DEVICE` (typically 50)

---

## Timing

### CONFIG_SPI_COMPLETION_TIMEOUT_TOLERANCE

```kconfig
CONFIG_SPI_COMPLETION_TIMEOUT_TOLERANCE=200
```

Tolerance in milliseconds for SPI completion timeout logic.

**Default:** 200

---

## Logging

### CONFIG_SPI_LOG_LEVEL

Set via standard logging configuration:

```kconfig
CONFIG_SPI_LOG_LEVEL_DBG=y   # Debug level
CONFIG_SPI_LOG_LEVEL_INF=y   # Info level
CONFIG_SPI_LOG_LEVEL_WRN=y   # Warning level
CONFIG_SPI_LOG_LEVEL_ERR=y   # Error level
CONFIG_SPI_LOG_LEVEL_OFF=y   # Disable logging
```

**Default:** Inherits from `LOG_DEFAULT_LEVEL`

---

## Common Driver Options

Many SPI controller drivers have their own Kconfig options. Common patterns:

### DMA Support

```kconfig
CONFIG_SPI_<VENDOR>_DMA=y
```

Enable DMA for SPI transfers (driver-specific).

### Interrupt vs Polling

Some drivers offer choice between interrupt-driven and polling modes.

---

## Typical prj.conf Examples

### Basic SPI

```kconfig
CONFIG_SPI=y
CONFIG_GPIO=y  # Usually needed for CS
```

### SPI with Async

```kconfig
CONFIG_SPI=y
CONFIG_SPI_ASYNC=y
CONFIG_GPIO=y
```

### SPI with Debugging

```kconfig
CONFIG_SPI=y
CONFIG_GPIO=y
CONFIG_SPI_SHELL=y
CONFIG_SHELL=y
CONFIG_SPI_LOG_LEVEL_DBG=y
```

### SPI with DMA (STM32 example)

```kconfig
CONFIG_SPI=y
CONFIG_SPI_STM32_DMA=y
CONFIG_DMA=y
```

### SPI Slave Mode

```kconfig
CONFIG_SPI=y
CONFIG_SPI_SLAVE=y
```

---

## Driver-Specific Kconfig Files

Each SPI controller has its own Kconfig file under `drivers/spi/`:

| File | Controller |
|------|------------|
| `Kconfig.stm32` | STM32 SPI |
| `Kconfig.nrfx` | Nordic nRF |
| `Kconfig.esp32` | ESP32 |
| `Kconfig.sam` | Atmel SAM |
| `Kconfig.mcux_*` | NXP MCUXpresso |
| `Kconfig.bitbang` | Software SPI |
| `Kconfig.pl022` | ARM PL022 |

Consult driver-specific files for advanced options like DMA channels, interrupt priorities, etc.
