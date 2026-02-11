# UART Async (DMA) API Reference

The asynchronous API enables high-throughput UART with DMA, minimal CPU overhead, and zero-copy operation. Requires `CONFIG_UART_ASYNC_API=y`.

## Table of Contents

1. [Event Model](#event-model)
2. [API Functions](#api-functions)
3. [RX Flow](#rx-flow)
4. [TX Flow](#tx-flow)
5. [Buffer Management](#buffer-management)
6. [Complete Examples](#complete-examples)

---

## Event Model

The async API is event-driven. Register a callback to receive `struct uart_event`:

```c
typedef void (*uart_callback_t)(const struct device *dev,
                                struct uart_event *evt,
                                void *user_data);
```

### Event Types

| Event | Trigger | Action Required |
|-------|---------|-----------------|
| `UART_TX_DONE` | TX buffer fully sent | Free/reuse TX buffer |
| `UART_TX_ABORTED` | TX aborted (timeout/manual) | Handle partial send |
| `UART_RX_RDY` | Data received in buffer | Process received data |
| `UART_RX_BUF_REQUEST` | Need next RX buffer | Provide buffer via `uart_rx_buf_rsp()` |
| `UART_RX_BUF_RELEASED` | Buffer no longer used | Buffer safe to reuse |
| `UART_RX_DISABLED` | RX stopped | Can call `uart_rx_enable()` again |
| `UART_RX_STOPPED` | RX stopped due to error | Check error, re-enable if needed |

### Event Data Structures

```c
struct uart_event {
    enum uart_event_type type;
    union uart_event_data {
        struct uart_event_tx tx;        /* TX_DONE, TX_ABORTED */
        struct uart_event_rx rx;        /* RX_RDY */
        struct uart_event_rx_buf rx_buf; /* RX_BUF_RELEASED */
        struct uart_event_rx_stop rx_stop; /* RX_STOPPED */
    } data;
};

struct uart_event_rx {
    uint8_t *buf;    /* Pointer to buffer */
    size_t offset;   /* Offset of new data in buffer */
    size_t len;      /* Length of new data */
};
```

**Data location**: `evt->data.rx.buf + evt->data.rx.offset` for `len` bytes.

---

## API Functions

### Setup

```c
int uart_callback_set(const struct device *dev,
                      uart_callback_t callback,
                      void *user_data);
```

**Returns**: `0` on success, `-ENOSYS` if not implemented, `-ENOTSUP` if API not enabled.

### Transmit

```c
int uart_tx(const struct device *dev, const uint8_t *buf,
            size_t len, int32_t timeout);
```

- **timeout**: Microseconds. `SYS_FOREVER_US` for no timeout. Only meaningful with flow control.
- **Returns**: `0` on success, `-EBUSY` if TX already in progress.

```c
int uart_tx_abort(const struct device *dev);
```

Aborts current TX. Generates `UART_TX_ABORTED` with bytes sent.

### Receive

```c
int uart_rx_enable(const struct device *dev, uint8_t *buf,
                   size_t len, int32_t timeout);
```

- **buf**: First receive buffer
- **timeout**: Inactivity timeout in microseconds. Triggers `UART_RX_RDY` if no data received for this period.
- **Returns**: `0` on success, `-EBUSY` if RX already active.

```c
int uart_rx_buf_rsp(const struct device *dev, uint8_t *buf, size_t len);
```

Provide next buffer in response to `UART_RX_BUF_REQUEST`.

- **Returns**: `0` on success, `-EBUSY` if buffer already provided, `-EACCES` if RX disabled.

```c
int uart_rx_disable(const struct device *dev);
```

Stop receiving. Generates `UART_RX_RDY` (if data pending), `UART_RX_BUF_RELEASED` for each buffer, then `UART_RX_DISABLED`.

---

## RX Flow

### Event Sequence

```
uart_rx_enable(buf1)
        │
        ▼
UART_RX_BUF_REQUEST ────► uart_rx_buf_rsp(buf2)
        │
        ▼
    [Receiving into buf1]
        │
        ▼
UART_RX_RDY (buf1, partial)  ← Timeout or buffer full
        │
        ▼
UART_RX_BUF_RELEASED (buf1)
        │
        ▼
    [Receiving into buf2]
        │
        ▼
UART_RX_BUF_REQUEST ────► uart_rx_buf_rsp(buf1)
        │
        ▼
    ... continues ...
```

### Double Buffering Pattern

```c
#define RX_BUF_SIZE 64
uint8_t rx_bufs[2][RX_BUF_SIZE];
volatile int next_buf_idx = 1;

void uart_cb(const struct device *dev, struct uart_event *evt, void *data)
{
    switch (evt->type) {
    case UART_RX_RDY:
        /* Process: evt->data.rx.buf + evt->data.rx.offset, len: evt->data.rx.len */
        process_data(evt->data.rx.buf + evt->data.rx.offset, evt->data.rx.len);
        break;

    case UART_RX_BUF_REQUEST:
        uart_rx_buf_rsp(dev, rx_bufs[next_buf_idx], RX_BUF_SIZE);
        next_buf_idx = next_buf_idx ? 0 : 1;
        break;

    case UART_RX_BUF_RELEASED:
        /* Buffer evt->data.rx_buf.buf is now safe to reuse */
        break;

    case UART_RX_DISABLED:
        /* RX stopped, can re-enable */
        break;

    case UART_RX_STOPPED:
        /* Error occurred: evt->data.rx_stop.reason */
        LOG_ERR("RX stopped: reason=%d", evt->data.rx_stop.reason);
        break;
    }
}

int start_rx(const struct device *dev)
{
    uart_callback_set(dev, uart_cb, NULL);
    next_buf_idx = 1;
    return uart_rx_enable(dev, rx_bufs[0], RX_BUF_SIZE, 100 /* 100us timeout */);
}
```

---

## TX Flow

### Event Sequence

```
uart_tx(buf, len, timeout)
        │
        ▼
    [Transmitting]
        │
        ├──► UART_TX_DONE (success)
        │         └── buf can be freed/reused
        │
        └──► UART_TX_ABORTED (timeout or uart_tx_abort)
                  └── Check evt->data.tx.len for bytes sent
```

### TX Pattern with Buffer Pool

```c
#include <zephyr/net_buf.h>

NET_BUF_POOL_DEFINE(tx_pool, 8, 64, 0, NULL);

struct k_fifo tx_queue;
struct net_buf *tx_pending;

void uart_cb(const struct device *dev, struct uart_event *evt, void *data)
{
    struct net_buf *buf;

    switch (evt->type) {
    case UART_TX_DONE:
        /* Free completed buffer */
        net_buf_unref(tx_pending);
        tx_pending = NULL;

        /* Send next queued buffer */
        buf = k_fifo_get(&tx_queue, K_NO_WAIT);
        if (buf) {
            if (uart_tx(dev, buf->data, buf->len, SYS_FOREVER_US) == 0) {
                tx_pending = buf;
            } else {
                net_buf_unref(buf);
            }
        }
        break;

    case UART_TX_ABORTED:
        LOG_WRN("TX aborted, sent %d bytes", evt->data.tx.len);
        net_buf_unref(tx_pending);
        tx_pending = NULL;
        break;
    }
}

int send_async(const struct device *dev, const uint8_t *data, size_t len)
{
    struct net_buf *buf = net_buf_alloc(&tx_pool, K_NO_WAIT);
    if (!buf) return -ENOMEM;

    memcpy(net_buf_add(buf, len), data, len);

    if (tx_pending == NULL) {
        if (uart_tx(dev, buf->data, buf->len, SYS_FOREVER_US) == 0) {
            tx_pending = buf;
            return 0;
        }
        net_buf_unref(buf);
        return -EIO;
    }

    /* Queue for later */
    k_fifo_put(&tx_queue, buf);
    return 0;
}
```

---

## Buffer Management

### Rules

1. **Never reuse a buffer until released** - Wait for `UART_RX_BUF_RELEASED`
2. **Provide next buffer promptly** - On `UART_RX_BUF_REQUEST`, provide buffer immediately
3. **Handle partial fills** - `UART_RX_RDY` can fire multiple times per buffer
4. **Offset matters** - Data is at `buf + offset`, not `buf`

### Memory Considerations

| Buffer Count | Behavior |
|--------------|----------|
| 1 buffer | RX stops when buffer full, gaps possible |
| 2 buffers | Seamless switching, recommended minimum |
| 3+ buffers | Extra margin for slow processing |

### Buffer Size Considerations

- **Too small**: Frequent `UART_RX_RDY` events, overhead
- **Too large**: Memory waste, high latency before data available
- **Recommended**: Match typical message size or ~64-256 bytes

---

## Complete Examples

### Continuous RX with Processing

```c
#include <zephyr/kernel.h>
#include <zephyr/drivers/uart.h>

#define UART_DEV DEVICE_DT_GET(DT_NODELABEL(uart0))
#define BUF_SIZE 128

static uint8_t rx_buf[2][BUF_SIZE];
static int buf_idx;

K_MSGQ_DEFINE(rx_queue, sizeof(struct rx_data), 16, 4);

struct rx_data {
    uint8_t *buf;
    size_t offset;
    size_t len;
};

void uart_cb(const struct device *dev, struct uart_event *evt, void *data)
{
    struct rx_data rx;

    switch (evt->type) {
    case UART_RX_RDY:
        rx.buf = evt->data.rx.buf;
        rx.offset = evt->data.rx.offset;
        rx.len = evt->data.rx.len;
        k_msgq_put(&rx_queue, &rx, K_NO_WAIT);
        break;

    case UART_RX_BUF_REQUEST:
        uart_rx_buf_rsp(dev, rx_buf[buf_idx], BUF_SIZE);
        buf_idx = buf_idx ? 0 : 1;
        break;

    case UART_RX_DISABLED:
    case UART_RX_BUF_RELEASED:
        break;

    case UART_RX_STOPPED:
        LOG_ERR("RX error: %d", evt->data.rx_stop.reason);
        /* Re-enable RX */
        k_work_submit(&rx_restart_work);
        break;
    }
}

int main(void)
{
    const struct device *dev = UART_DEV;
    struct rx_data rx;

    uart_callback_set(dev, uart_cb, NULL);
    buf_idx = 1;
    uart_rx_enable(dev, rx_buf[0], BUF_SIZE, 1000); /* 1ms timeout */

    while (1) {
        if (k_msgq_get(&rx_queue, &rx, K_FOREVER) == 0) {
            process_data(rx.buf + rx.offset, rx.len);
        }
    }
}
```

---

## Common Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| RX stops unexpectedly | No buffer provided | Always respond to `UART_RX_BUF_REQUEST` |
| Data gaps | Single buffer | Use double buffering |
| `-EBUSY` on `uart_rx_enable` | RX already active | Call `uart_rx_disable()` first, wait for `UART_RX_DISABLED` |
| `-EBUSY` on `uart_tx` | TX already in progress | Queue data, send on `UART_TX_DONE` |
| Buffer overwritten | Reused before released | Wait for `UART_RX_BUF_RELEASED` |
| No events | Callback not set | Call `uart_callback_set()` first |
| `-ENOTSUP` | API not enabled | Enable `CONFIG_UART_ASYNC_API` |

## Performance Tips

1. **Use DMA-capable buffers** - Some MCUs require specific memory regions
2. **Align buffers** - 4-byte alignment often required for DMA
3. **Minimize callback work** - Defer processing to thread context
4. **Size buffers for throughput** - Larger buffers = fewer interrupts
