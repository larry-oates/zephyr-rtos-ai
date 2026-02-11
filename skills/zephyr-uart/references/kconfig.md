# UART Kconfig Reference

Complete reference for Zephyr UART/Serial subsystem Kconfig configuration options.

## Table of Contents

1. [Essential Options](#essential-options)
2. [API Selection](#api-selection)
3. [Runtime Configuration](#runtime-configuration)
4. [Advanced Options](#advanced-options)
5. [Logging](#logging)
6. [Example Configurations](#example-configurations)

---

## Essential Options

### Core Serial

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `CONFIG_SERIAL` | bool | y | Enable serial driver subsystem |
| `CONFIG_SERIAL_HAS_DRIVER` | bool | (auto) | Set by driver to indicate serial available |
| `CONFIG_SERIAL_INIT_PRIORITY` | int | varies | Driver initialization priority |

### Minimal Configuration

```kconfig
CONFIG_SERIAL=y
```

This enables polling API only. Interrupt and async APIs require additional options.

---

## API Selection

### Interrupt-Driven API

```kconfig
CONFIG_UART_INTERRUPT_DRIVEN=y
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `CONFIG_UART_INTERRUPT_DRIVEN` | bool | n | Enable interrupt-driven UART API |
| `CONFIG_SERIAL_SUPPORT_INTERRUPT` | bool | (auto) | Set by driver if hardware supports interrupts |

**Required for**: `uart_irq_*` functions, `uart_fifo_read/fill`, ISR callbacks.

### Async (DMA) API

```kconfig
CONFIG_UART_ASYNC_API=y
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `CONFIG_UART_ASYNC_API` | bool | n | Enable asynchronous UART API |
| `CONFIG_SERIAL_SUPPORT_ASYNC` | bool | (auto) | Set by driver if hardware supports async/DMA |

**Required for**: `uart_tx`, `uart_rx_enable`, `uart_callback_set`.

### API Callback Exclusivity

```kconfig
CONFIG_UART_EXCLUSIVE_API_CALLBACKS=y
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `CONFIG_UART_EXCLUSIVE_API_CALLBACKS` | bool | y | Only one API's callbacks active at a time |

**Effect**: Setting async callback disables interrupt callback and vice versa.

**Warning**: Do not disable unless you fully understand the implications.

---

## Runtime Configuration

### Dynamic Configuration

```kconfig
CONFIG_UART_USE_RUNTIME_CONFIGURE=y
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `CONFIG_UART_USE_RUNTIME_CONFIGURE` | bool | y | Enable `uart_configure()` at runtime |

**Required for**: Changing baud rate, parity, stop bits at runtime.

**Disable to**: Reduce footprint if configuration is static (from DTS only).

### Line Control

```kconfig
CONFIG_UART_LINE_CTRL=y
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `CONFIG_UART_LINE_CTRL` | bool | n | Enable line control API |

**Required for**: `uart_line_ctrl_set/get` for RTS, CTS, DTR, DSR, baud rate control.

### Driver Commands

```kconfig
CONFIG_UART_DRV_CMD=y
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `CONFIG_UART_DRV_CMD` | bool | n | Enable driver-specific commands |

**Required for**: `uart_drv_cmd()` for hardware-specific functions.

---

## Advanced Options

### Wide Data (9-bit+)

```kconfig
CONFIG_UART_WIDE_DATA=y
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `CONFIG_UART_WIDE_DATA` | bool | n | Enable 9/16-bit data support |
| `CONFIG_SERIAL_SUPPORT_WIDE_DATA` | bool | (auto) | Set by driver if hardware supports wide data |

**Required for**: `uart_poll_in_u16`, `uart_poll_out_u16`, `uart_fifo_fill_u16`, etc.

### UART Pipe

```kconfig
CONFIG_UART_PIPE=y
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `CONFIG_UART_PIPE` | bool | n | Enable pipe UART driver |

Custom protocol handling without shell/console interpretation.

### Async Helpers

```kconfig
CONFIG_UART_ASYNC_RX_HELPER=y
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `CONFIG_UART_ASYNC_RX_HELPER` | bool | n | Helper for variable-length async RX |

Zero-copy handling with multiple RX buffers.

### Async-to-Interrupt Adapter

```kconfig
CONFIG_UART_ASYNC_TO_INT_DRIVEN_API=y
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `CONFIG_UART_ASYNC_TO_INT_DRIVEN_API` | bool | n | Adapter layer for async-only drivers |
| `CONFIG_UART_ASYNC_TO_INT_DRIVEN_RX_TIMEOUT` | int | 100 | RX timeout in bauds |

Allows using interrupt API on drivers that only implement async.

---

## Logging

```kconfig
CONFIG_UART_LOG_LEVEL_DBG=y
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `CONFIG_UART_LOG_LEVEL_OFF` | bool | | Disable UART logging |
| `CONFIG_UART_LOG_LEVEL_ERR` | bool | | Error level only |
| `CONFIG_UART_LOG_LEVEL_WRN` | bool | | Warning and above |
| `CONFIG_UART_LOG_LEVEL_INF` | bool | y | Info and above (default) |
| `CONFIG_UART_LOG_LEVEL_DBG` | bool | | Debug and above |

---

## Example Configurations

### Minimal (Polling Only)

```kconfig
CONFIG_SERIAL=y
```

### Interrupt-Driven Console

```kconfig
CONFIG_SERIAL=y
CONFIG_UART_INTERRUPT_DRIVEN=y
CONFIG_CONSOLE=y
CONFIG_UART_CONSOLE=y
```

### High-Throughput Async

```kconfig
CONFIG_SERIAL=y
CONFIG_UART_ASYNC_API=y
CONFIG_UART_USE_RUNTIME_CONFIGURE=y
```

### Full-Featured Development

```kconfig
CONFIG_SERIAL=y
CONFIG_UART_INTERRUPT_DRIVEN=y
CONFIG_UART_ASYNC_API=y
CONFIG_UART_USE_RUNTIME_CONFIGURE=y
CONFIG_UART_LINE_CTRL=y
CONFIG_UART_LOG_LEVEL_DBG=y
```

### Minimal Footprint

```kconfig
CONFIG_SERIAL=y
CONFIG_UART_USE_RUNTIME_CONFIGURE=n
# Use DTS for static configuration
```

### RS-485 Mode

```kconfig
CONFIG_SERIAL=y
CONFIG_UART_INTERRUPT_DRIVEN=y
CONFIG_UART_LINE_CTRL=y
# Hardware-specific RS-485 options may vary by driver
```

---

## Shell Integration

For shell over UART:

```kconfig
CONFIG_SHELL=y
CONFIG_SHELL_BACKEND_SERIAL=y
CONFIG_SHELL_BACKEND_SERIAL_INTERRUPT_DRIVEN=y
```

---

## Driver-Specific Options

Many SoC-specific options exist under `CONFIG_UART_<VENDOR>_*`. Examples:

- `CONFIG_UART_NRFX_*` - Nordic nRF
- `CONFIG_UART_STM32_*` - STM32
- `CONFIG_UART_SAM_*` - Atmel SAM
- `CONFIG_UART_ESP32_*` - ESP32
- `CONFIG_UART_NS16550_*` - Generic 16550

Check `drivers/serial/Kconfig.<vendor>` for vendor-specific options.

---

## Troubleshooting Kconfig

| Error | Cause | Solution |
|-------|-------|----------|
| `uart_irq_*` undefined | API not enabled | Enable `CONFIG_UART_INTERRUPT_DRIVEN` |
| `uart_tx` undefined | API not enabled | Enable `CONFIG_UART_ASYNC_API` |
| `uart_configure` returns `-ENOSYS` | Runtime config disabled | Enable `CONFIG_UART_USE_RUNTIME_CONFIGURE` |
| Symbol not visible in menuconfig | Missing dependency | Check `depends on` in Kconfig |
| "SERIAL_SUPPORT_INTERRUPT not set" | Hardware doesn't support | Check driver or use different UART |
