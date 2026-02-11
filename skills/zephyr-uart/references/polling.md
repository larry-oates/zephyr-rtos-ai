# UART Polling API Reference

The polling API is the simplest UART interface. Always available when `CONFIG_SERIAL=y`.

## Table of Contents

1. [API Functions](#api-functions)
2. [Usage Patterns](#usage-patterns)
3. [Wide Data Support](#wide-data-support)

---

## API Functions

### uart_poll_out

```c
void uart_poll_out(const struct device *dev, unsigned char out_char);
```

**Behavior**: Blocking. Waits until character is transmitted.

**Flow control**: If hardware flow control enabled, waits for CTS assertion.

**Example**:
```c
void send_string(const struct device *dev, const char *str)
{
    while (*str) {
        uart_poll_out(dev, *str++);
    }
}
```

### uart_poll_in

```c
int uart_poll_in(const struct device *dev, unsigned char *p_char);
```

**Behavior**: Non-blocking. Returns immediately.

**Returns**:
- `0`: Character received, stored in `*p_char`
- `-1`: No data available (FIFO empty)
- `-ENOSYS`: Not implemented
- `-EBUSY`: Async RX active (call `uart_rx_disable()` first)

**Example**:
```c
int try_read(const struct device *dev)
{
    unsigned char c;
    if (uart_poll_in(dev, &c) == 0) {
        return (int)c;
    }
    return -1;  /* No data */
}
```

---

## Usage Patterns

### Simple Debug Output

```c
#include <zephyr/drivers/uart.h>

#define UART_DEV DEVICE_DT_GET(DT_CHOSEN(zephyr_shell_uart))

void debug_print(const char *msg)
{
    const struct device *dev = UART_DEV;
    if (!device_is_ready(dev)) return;

    while (*msg) {
        uart_poll_out(dev, *msg++);
    }
}
```

### Blocking Read with Timeout

Polling RX is non-blocking, so implement timeout manually:

```c
int read_with_timeout(const struct device *dev, char *buf, size_t len, k_timeout_t timeout)
{
    int64_t end = k_uptime_get() + k_ticks_to_ms_ceil64(timeout.ticks);
    size_t pos = 0;
    unsigned char c;

    while (pos < len && k_uptime_get() < end) {
        if (uart_poll_in(dev, &c) == 0) {
            buf[pos++] = c;
        } else {
            k_yield();  /* Let other threads run */
        }
    }
    return pos;
}
```

### Echo Loop (Busy-Wait)

Simple but CPU-intensive:

```c
void echo_loop(const struct device *dev)
{
    unsigned char c;
    while (1) {
        if (uart_poll_in(dev, &c) == 0) {
            uart_poll_out(dev, c);
        }
    }
}
```

### Line-Based Input

```c
int read_line(const struct device *dev, char *buf, size_t max_len)
{
    size_t pos = 0;
    unsigned char c;

    while (pos < max_len - 1) {
        if (uart_poll_in(dev, &c) == 0) {
            if (c == '\n' || c == '\r') {
                buf[pos] = '\0';
                return pos;
            }
            buf[pos++] = c;
        }
        k_msleep(1);  /* Reduce CPU usage */
    }
    buf[pos] = '\0';
    return pos;
}
```

---

## Wide Data Support

For 9-bit or 16-bit data modes (requires `CONFIG_UART_WIDE_DATA=y`):

### uart_poll_out_u16

```c
void uart_poll_out_u16(const struct device *dev, uint16_t out_u16);
```

### uart_poll_in_u16

```c
int uart_poll_in_u16(const struct device *dev, uint16_t *p_u16);
```

**Returns**: Same as `uart_poll_in`.

**Note**: Not all hardware supports wide data. Check driver documentation.

---

## When to Use Polling

| Scenario | Recommendation |
|----------|----------------|
| Debug/diagnostic output | Use polling TX |
| Low-volume, infrequent data | Use polling |
| High-volume or continuous RX | Use interrupt or async |
| Background processing needed | Use interrupt or async |
| Bootloader or early init | Use polling (simpler) |

## Limitations

- **TX**: Blocking can stall thread for duration of transmission
- **RX**: Easy to miss data if not polled frequently enough
- **CPU**: Polling loops consume CPU cycles
- **No buffering**: Single-character operations only
