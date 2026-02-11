# UART Interrupt-Driven API Reference

The interrupt-driven API enables background UART operations without blocking the main thread. Requires `CONFIG_UART_INTERRUPT_DRIVEN=y`.

## Table of Contents

1. [API Functions](#api-functions)
2. [ISR Pattern](#isr-pattern)
3. [RX Patterns](#rx-patterns)
4. [TX Patterns](#tx-patterns)
5. [Complete Examples](#complete-examples)

---

## API Functions

### Callback Setup

```c
int uart_irq_callback_user_data_set(const struct device *dev,
                                     uart_irq_callback_user_data_t cb,
                                     void *user_data);
```

**Callback signature**:
```c
typedef void (*uart_irq_callback_user_data_t)(const struct device *dev, void *user_data);
```

### Interrupt Control

| Function | Purpose |
|----------|---------|
| `uart_irq_rx_enable(dev)` | Enable RX interrupt |
| `uart_irq_rx_disable(dev)` | Disable RX interrupt |
| `uart_irq_tx_enable(dev)` | Enable TX interrupt |
| `uart_irq_tx_disable(dev)` | Disable TX interrupt |
| `uart_irq_err_enable(dev)` | Enable error interrupt |
| `uart_irq_err_disable(dev)` | Disable error interrupt |

### ISR Helper Functions

| Function | Purpose | Returns |
|----------|---------|---------|
| `uart_irq_update(dev)` | Refresh IRQ status cache | 1 on success |
| `uart_irq_rx_ready(dev)` | Check if RX data available | 1 if data ready |
| `uart_irq_tx_ready(dev)` | Check if TX FIFO can accept data | >0 if ready |
| `uart_irq_tx_complete(dev)` | Check if TX fully done | 1 if idle |
| `uart_irq_is_pending(dev)` | Check for any pending IRQ | 1 if pending |

### FIFO Operations

```c
int uart_fifo_read(const struct device *dev, uint8_t *rx_data, const int size);
int uart_fifo_fill(const struct device *dev, const uint8_t *tx_data, int size);
```

**Returns**: Number of bytes read/written, or negative errno.

**Critical**: Must drain FIFO completely when `uart_irq_rx_ready()` returns true.

---

## ISR Pattern

### Standard ISR Structure

```c
void uart_isr_handler(const struct device *dev, void *user_data)
{
    /* Step 1: Update IRQ status (REQUIRED first) */
    if (!uart_irq_update(dev)) {
        return;
    }

    /* Step 2: Handle RX if data available */
    if (uart_irq_rx_ready(dev)) {
        uint8_t buf[64];
        int len;
        /* Drain entire FIFO */
        while ((len = uart_fifo_read(dev, buf, sizeof(buf))) > 0) {
            process_rx_data(buf, len);
        }
    }

    /* Step 3: Handle TX if FIFO ready */
    if (uart_irq_tx_ready(dev)) {
        /* Fill FIFO with pending TX data */
        int sent = uart_fifo_fill(dev, tx_buf, tx_len);
        if (sent > 0) {
            tx_buf += sent;
            tx_len -= sent;
        }
        if (tx_len == 0) {
            uart_irq_tx_disable(dev);  /* No more data to send */
        }
    }
}
```

### Key Rules

1. **Always call `uart_irq_update()` first** - required before checking rx/tx ready
2. **Drain RX FIFO completely** - some hardware auto-clears IRQ only when FIFO empty
3. **Disable TX IRQ when done** - TX IRQ fires continuously when FIFO empty
4. **Keep ISR short** - defer processing to thread context

---

## RX Patterns

### Line-Based with Message Queue

```c
#include <zephyr/drivers/uart.h>

#define MSG_SIZE 64
K_MSGQ_DEFINE(uart_msgq, MSG_SIZE, 10, 4);

static char rx_line[MSG_SIZE];
static int rx_pos;

void uart_rx_isr(const struct device *dev, void *user_data)
{
    if (!uart_irq_update(dev)) return;
    if (!uart_irq_rx_ready(dev)) return;

    uint8_t c;
    while (uart_fifo_read(dev, &c, 1) == 1) {
        if (c == '\n' || c == '\r') {
            if (rx_pos > 0) {
                rx_line[rx_pos] = '\0';
                k_msgq_put(&uart_msgq, rx_line, K_NO_WAIT);
                rx_pos = 0;
            }
        } else if (rx_pos < MSG_SIZE - 1) {
            rx_line[rx_pos++] = c;
        }
    }
}

/* Thread processing */
void process_lines(void)
{
    char buf[MSG_SIZE];
    while (k_msgq_get(&uart_msgq, buf, K_FOREVER) == 0) {
        handle_command(buf);
    }
}
```

### Ring Buffer Pattern

```c
#include <zephyr/sys/ring_buffer.h>

RING_BUF_DECLARE(uart_rx_ring, 256);

void uart_rx_isr(const struct device *dev, void *user_data)
{
    if (!uart_irq_update(dev)) return;
    if (!uart_irq_rx_ready(dev)) return;

    uint8_t buf[32];
    int len;
    while ((len = uart_fifo_read(dev, buf, sizeof(buf))) > 0) {
        ring_buf_put(&uart_rx_ring, buf, len);
    }
    k_sem_give(&rx_sem);  /* Signal waiting thread */
}

/* Thread context */
int read_from_uart(uint8_t *buf, size_t len, k_timeout_t timeout)
{
    if (k_sem_take(&rx_sem, timeout) != 0) {
        return -ETIMEDOUT;
    }
    return ring_buf_get(&uart_rx_ring, buf, len);
}
```

---

## TX Patterns

### Non-Blocking TX with Ring Buffer

```c
RING_BUF_DECLARE(uart_tx_ring, 256);
static volatile bool tx_active;

void uart_tx_isr(const struct device *dev)
{
    uint8_t buf[16];
    int len = ring_buf_get(&uart_tx_ring, buf, sizeof(buf));

    if (len > 0) {
        uart_fifo_fill(dev, buf, len);
    } else {
        uart_irq_tx_disable(dev);
        tx_active = false;
    }
}

int uart_send(const struct device *dev, const uint8_t *data, size_t len)
{
    int written = ring_buf_put(&uart_tx_ring, data, len);

    if (!tx_active) {
        tx_active = true;
        uart_irq_tx_enable(dev);
    }
    return written;
}
```

### Blocking TX (with ISR assist)

```c
K_SEM_DEFINE(tx_done_sem, 0, 1);
static const uint8_t *tx_ptr;
static size_t tx_remaining;

void uart_tx_isr(const struct device *dev)
{
    if (tx_remaining > 0) {
        int sent = uart_fifo_fill(dev, tx_ptr, tx_remaining);
        tx_ptr += sent;
        tx_remaining -= sent;
    }

    if (tx_remaining == 0) {
        uart_irq_tx_disable(dev);
        k_sem_give(&tx_done_sem);
    }
}

int uart_send_blocking(const struct device *dev, const uint8_t *data, size_t len)
{
    tx_ptr = data;
    tx_remaining = len;
    uart_irq_tx_enable(dev);
    return k_sem_take(&tx_done_sem, K_FOREVER);
}
```

---

## Complete Examples

### Echo Bot (RX + TX)

```c
#include <zephyr/kernel.h>
#include <zephyr/drivers/uart.h>

#define UART_DEV DEVICE_DT_GET(DT_CHOSEN(zephyr_shell_uart))
#define BUF_SIZE 64

K_MSGQ_DEFINE(rx_msgq, BUF_SIZE, 8, 4);

static char rx_buf[BUF_SIZE];
static int rx_pos;

void serial_cb(const struct device *dev, void *user_data)
{
    if (!uart_irq_update(dev)) return;
    if (!uart_irq_rx_ready(dev)) return;

    uint8_t c;
    while (uart_fifo_read(dev, &c, 1) == 1) {
        if (c == '\r' || c == '\n') {
            if (rx_pos > 0) {
                rx_buf[rx_pos] = '\0';
                k_msgq_put(&rx_msgq, rx_buf, K_NO_WAIT);
                rx_pos = 0;
            }
        } else if (rx_pos < BUF_SIZE - 1) {
            rx_buf[rx_pos++] = c;
        }
    }
}

void print_uart(const struct device *dev, const char *str)
{
    while (*str) {
        uart_poll_out(dev, *str++);
    }
}

int main(void)
{
    const struct device *dev = UART_DEV;
    char line[BUF_SIZE];

    if (!device_is_ready(dev)) {
        return -ENODEV;
    }

    uart_irq_callback_user_data_set(dev, serial_cb, NULL);
    uart_irq_rx_enable(dev);

    print_uart(dev, "Echo bot ready\r\n");

    while (k_msgq_get(&rx_msgq, line, K_FOREVER) == 0) {
        print_uart(dev, "Echo: ");
        print_uart(dev, line);
        print_uart(dev, "\r\n");
    }
    return 0;
}
```

---

## Common Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| Callback never called | IRQ not enabled | Call `uart_irq_rx_enable()` |
| Missing characters | FIFO not drained | Read until `uart_fifo_read()` returns 0 |
| TX IRQ storms | TX IRQ not disabled | Disable TX IRQ when buffer empty |
| Data corruption | ISR too slow | Use ring buffer, process in thread |
| `-ENOSYS` error | API not implemented | Check driver support |
| `-ENOTSUP` error | API not enabled | Enable `CONFIG_UART_INTERRUPT_DRIVEN` |
