# SPI Async API Reference

Detailed reference for Zephyr's asynchronous SPI API. Requires `CONFIG_SPI_ASYNC=y`.

## Table of Contents

1. [Overview](#overview)
2. [Callback API](#callback-api)
3. [Signal API](#signal-api)
4. [Buffer Management](#buffer-management)
5. [Complete Examples](#complete-examples)
6. [Common Issues](#common-issues)

---

## Overview

The async SPI API allows non-blocking transfers. The function returns immediately after starting the transfer, and completion is notified via:

1. **Callback** - Function called when transfer completes
2. **Signal** - `k_poll_signal` raised when transfer completes

### When to Use Async

| Use Case | Recommendation |
|----------|----------------|
| Simple, infrequent transfers | Sync API (simpler) |
| Need to do work during transfer | Async |
| High throughput requirements | Async + DMA driver |
| Multiple concurrent SPI operations | Async with queuing |
| Real-time constraints | Async (predictable latency) |

---

## Callback API

### spi_transceive_cb

```c
int spi_transceive_cb(const struct device *dev,
                      const struct spi_config *config,
                      const struct spi_buf_set *tx_bufs,
                      const struct spi_buf_set *rx_bufs,
                      spi_callback_t callback,
                      void *userdata);
```

**Callback Signature:**

```c
typedef void (*spi_callback_t)(const struct device *dev,
                               int result,
                               void *data);
```

**Callback Parameters:**
- `dev`: SPI controller device
- `result`: 0 on success, -errno on failure
- `data`: userdata passed to `spi_transceive_cb`

**Important:**
- Callback runs in ISR context (on most drivers)
- Keep callback work minimal
- Do not call blocking functions in callback
- Buffers must remain valid until callback fires

### Basic Callback Pattern

```c
#include <zephyr/drivers/spi.h>
#include <zephyr/kernel.h>

static struct k_sem transfer_sem;
static int transfer_result;

void spi_done_callback(const struct device *dev, int result, void *userdata)
{
    transfer_result = result;
    k_sem_give(&transfer_sem);
}

int async_transfer_with_callback(const struct spi_dt_spec *spi,
                                  uint8_t *tx, size_t tx_len,
                                  uint8_t *rx, size_t rx_len)
{
    struct spi_buf tx_buf = {.buf = tx, .len = tx_len};
    struct spi_buf rx_buf = {.buf = rx, .len = rx_len};
    struct spi_buf_set tx_set = {.buffers = &tx_buf, .count = 1};
    struct spi_buf_set rx_set = {.buffers = &rx_buf, .count = 1};

    k_sem_init(&transfer_sem, 0, 1);

    int ret = spi_transceive_cb(spi->bus, &spi->config,
                                 &tx_set, &rx_set,
                                 spi_done_callback, NULL);
    if (ret < 0) {
        return ret;
    }

    /* Wait for completion */
    k_sem_take(&transfer_sem, K_FOREVER);

    return transfer_result;
}
```

### Callback with User Data

```c
struct transfer_context {
    struct k_sem done;
    int result;
    uint8_t *rx_data;
    size_t rx_len;
};

void spi_callback_with_context(const struct device *dev, int result, void *userdata)
{
    struct transfer_context *ctx = userdata;
    ctx->result = result;
    k_sem_give(&ctx->done);
}

int transfer_with_context(const struct spi_dt_spec *spi, uint8_t *tx, uint8_t *rx, size_t len)
{
    struct transfer_context ctx = {
        .rx_data = rx,
        .rx_len = len,
    };
    k_sem_init(&ctx.done, 0, 1);

    struct spi_buf tx_buf = {.buf = tx, .len = len};
    struct spi_buf rx_buf = {.buf = rx, .len = len};
    struct spi_buf_set tx_set = {.buffers = &tx_buf, .count = 1};
    struct spi_buf_set rx_set = {.buffers = &rx_buf, .count = 1};

    int ret = spi_transceive_cb(spi->bus, &spi->config,
                                 &tx_set, &rx_set,
                                 spi_callback_with_context, &ctx);
    if (ret < 0) {
        return ret;
    }

    k_sem_take(&ctx.done, K_FOREVER);
    return ctx.result;
}
```

---

## Signal API

Requires `CONFIG_SPI_ASYNC=y` and `CONFIG_POLL=y`.

### spi_transceive_signal

```c
int spi_transceive_signal(const struct device *dev,
                          const struct spi_config *config,
                          const struct spi_buf_set *tx_bufs,
                          const struct spi_buf_set *rx_bufs,
                          struct k_poll_signal *sig);
```

The signal is raised with the result code when transfer completes.

### Basic Signal Pattern

```c
#include <zephyr/drivers/spi.h>
#include <zephyr/kernel.h>

int async_transfer_with_signal(const struct spi_dt_spec *spi,
                                uint8_t *tx, size_t tx_len,
                                uint8_t *rx, size_t rx_len)
{
    struct k_poll_signal sig;
    struct k_poll_event evt = K_POLL_EVENT_INITIALIZER(
        K_POLL_TYPE_SIGNAL, K_POLL_MODE_NOTIFY_ONLY, &sig);

    k_poll_signal_init(&sig);

    struct spi_buf tx_buf = {.buf = tx, .len = tx_len};
    struct spi_buf rx_buf = {.buf = rx, .len = rx_len};
    struct spi_buf_set tx_set = {.buffers = &tx_buf, .count = 1};
    struct spi_buf_set rx_set = {.buffers = &rx_buf, .count = 1};

    int ret = spi_transceive_signal(spi->bus, &spi->config,
                                     &tx_set, &rx_set, &sig);
    if (ret < 0) {
        return ret;
    }

    /* Wait for completion */
    k_poll(&evt, 1, K_FOREVER);

    /* Get result from signal */
    int result;
    unsigned int signaled;
    k_poll_signal_check(&sig, &signaled, &result);

    return result;
}
```

### Polling Multiple Signals

```c
struct k_poll_signal spi_sig, other_sig;
struct k_poll_event events[] = {
    K_POLL_EVENT_INITIALIZER(K_POLL_TYPE_SIGNAL, K_POLL_MODE_NOTIFY_ONLY, &spi_sig),
    K_POLL_EVENT_INITIALIZER(K_POLL_TYPE_SIGNAL, K_POLL_MODE_NOTIFY_ONLY, &other_sig),
};

/* Start async SPI transfer */
spi_transceive_signal(..., &spi_sig);

/* Wait for any event */
k_poll(events, ARRAY_SIZE(events), K_FOREVER);

if (events[0].state == K_POLL_STATE_SIGNALED) {
    /* SPI transfer complete */
}
```

---

## Buffer Management

### Rules

1. **Buffers must remain valid** until transfer completes (callback fires or signal raised)
2. **Do not modify buffers** during transfer
3. **Align buffers** for DMA (often 4-byte or cache-line alignment)
4. **Use static or heap buffers** - stack buffers are risky if function returns before completion

### DMA Buffer Alignment

```c
/* Ensure proper alignment for DMA */
static uint8_t tx_buf[64] __aligned(4);
static uint8_t rx_buf[64] __aligned(4);

/* Or use cache-line alignment if needed */
static uint8_t tx_buf[64] __aligned(CONFIG_DCACHE_LINE_SIZE);
```

### Buffer Lifecycle

```c
/* WRONG - buffer may be invalid when callback fires */
void bad_transfer(void)
{
    uint8_t local_buf[16];  /* Stack buffer */
    spi_transceive_cb(..., local_buf, ...);
    return;  /* Function returns, local_buf invalid! */
}

/* CORRECT - buffer persists */
static uint8_t persistent_buf[16];

void good_transfer(void)
{
    spi_transceive_cb(..., persistent_buf, ...);
    /* Wait for completion before returning */
}
```

---

## Complete Examples

### Non-Blocking Sensor Read

```c
#include <zephyr/drivers/spi.h>
#include <zephyr/kernel.h>

#define SENSOR_DT DT_NODELABEL(my_sensor)
static const struct spi_dt_spec sensor = SPI_DT_SPEC_GET(
    SENSOR_DT, SPI_OP_MODE_MASTER | SPI_WORD_SET(8));

static uint8_t tx_cmd[1] __aligned(4) = {0x80};  /* Read command */
static uint8_t rx_data[8] __aligned(4);
static struct k_sem read_done;

void sensor_read_callback(const struct device *dev, int result, void *userdata)
{
    if (result == 0) {
        /* Process received data */
        int16_t value = (rx_data[1] << 8) | rx_data[2];
        printk("Sensor value: %d\n", value);
    }
    k_sem_give(&read_done);
}

int start_sensor_read(void)
{
    struct spi_buf tx = {.buf = tx_cmd, .len = 1};
    struct spi_buf rx = {.buf = rx_data, .len = sizeof(rx_data)};
    struct spi_buf_set tx_set = {.buffers = &tx, .count = 1};
    struct spi_buf_set rx_set = {.buffers = &rx, .count = 1};

    return spi_transceive_cb(sensor.bus, &sensor.config,
                              &tx_set, &rx_set,
                              sensor_read_callback, NULL);
}

int main(void)
{
    k_sem_init(&read_done, 0, 1);

    if (!spi_is_ready_dt(&sensor)) {
        return -ENODEV;
    }

    while (1) {
        start_sensor_read();

        /* Do other work while transfer runs */
        do_other_stuff();

        /* Wait for read to complete */
        k_sem_take(&read_done, K_FOREVER);

        k_sleep(K_MSEC(100));
    }
}
```

### Queue-Based Async Transfers

```c
#include <zephyr/drivers/spi.h>
#include <zephyr/kernel.h>

struct spi_transfer_request {
    uint8_t *tx_buf;
    uint8_t *rx_buf;
    size_t len;
    struct k_sem *done;
    int *result;
};

K_MSGQ_DEFINE(transfer_queue, sizeof(struct spi_transfer_request), 8, 4);

static struct spi_transfer_request current_request;
static volatile bool transfer_in_progress;

void spi_queue_callback(const struct device *dev, int result, void *userdata)
{
    struct spi_transfer_request *req = userdata;
    if (req->result) {
        *req->result = result;
    }
    if (req->done) {
        k_sem_give(req->done);
    }
    transfer_in_progress = false;

    /* Start next queued transfer */
    if (k_msgq_get(&transfer_queue, &current_request, K_NO_WAIT) == 0) {
        /* Start next transfer */
        start_transfer(&current_request);
    }
}

int queue_spi_transfer(uint8_t *tx, uint8_t *rx, size_t len,
                        struct k_sem *done, int *result)
{
    struct spi_transfer_request req = {
        .tx_buf = tx, .rx_buf = rx, .len = len,
        .done = done, .result = result
    };

    if (!transfer_in_progress) {
        current_request = req;
        transfer_in_progress = true;
        return start_transfer(&current_request);
    }

    return k_msgq_put(&transfer_queue, &req, K_FOREVER);
}
```

---

## Common Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| Callback never fires | Transfer failed to start | Check return value of transceive_cb |
| Corrupted RX data | Buffer freed/reused too early | Wait for callback before reusing |
| Hard fault in callback | Buffer on stack, function returned | Use static/heap buffers |
| `-EBUSY` | Previous transfer not complete | Wait for callback or use queue |
| Signal never raised | NULL signal passed | Ensure signal pointer is valid |
| Unpredictable behavior | Modifying buffer during transfer | Do not touch buffers until complete |

### Debugging Tips

1. **Enable SPI logging**: `CONFIG_SPI_LOG_LEVEL_DBG=y`
2. **Check return values**: Always check transceive_cb return
3. **Verify callback fires**: Add printk/logging in callback
4. **Check buffer alignment**: Some DMA controllers require alignment
5. **Use static buffers**: Avoid stack buffers for async operations
