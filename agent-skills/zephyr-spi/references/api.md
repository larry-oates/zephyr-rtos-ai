# SPI API Reference

Complete reference for Zephyr's SPI driver API functions.

## Table of Contents

1. [Core Structures](#core-structures)
2. [Synchronous API](#synchronous-api)
3. [Asynchronous API](#asynchronous-api)
4. [Utility Functions](#utility-functions)
5. [Devicetree Macros](#devicetree-macros)

---

## Core Structures

### struct spi_config

Configuration for SPI transactions:

```c
struct spi_config {
    uint32_t frequency;           /* Bus frequency in Hz */
    spi_operation_t operation;    /* Operation flags (mode, word size, etc.) */
    uint16_t slave;               /* Slave number (0 to controller limit) */
    struct spi_cs_control cs;     /* GPIO chip-select (optional) */
    uint16_t word_delay;          /* Delay between words in ns */
};
```

### struct spi_dt_spec

Complete SPI device specification from devicetree:

```c
struct spi_dt_spec {
    const struct device *bus;     /* SPI controller device */
    struct spi_config config;     /* Slave-specific configuration */
};
```

### struct spi_buf

Single buffer descriptor:

```c
struct spi_buf {
    void *buf;    /* Data buffer, or NULL for NOP */
    size_t len;   /* Buffer length in bytes */
};
```

- If `buf` is NULL for TX: sends zeros for `len` bytes
- If `buf` is NULL for RX: ignores `len` received bytes

### struct spi_buf_set

Scatter-gather buffer array:

```c
struct spi_buf_set {
    const struct spi_buf *buffers;  /* Array of spi_buf */
    size_t count;                   /* Number of buffers */
};
```

### struct spi_cs_control

Chip select control (GPIO or hardware):

```c
struct spi_cs_control {
    struct gpio_dt_spec gpio;  /* GPIO for CS (if cs_is_gpio=true) */
    uint32_t delay;            /* Delay in microseconds */
    /* OR for native CS: */
    uint32_t setup_ns;         /* CS setup time in ns */
    uint32_t hold_ns;          /* CS hold time in ns */
    bool cs_is_gpio;           /* True if using GPIO CS */
};
```

---

## Synchronous API

All synchronous functions block until the transfer completes.

### spi_transceive

```c
int spi_transceive(const struct device *dev,
                   const struct spi_config *config,
                   const struct spi_buf_set *tx_bufs,
                   const struct spi_buf_set *rx_bufs);
```

Read and write data simultaneously.

**Parameters:**
- `dev`: SPI controller device
- `config`: SPI configuration
- `tx_bufs`: TX buffer set (or NULL)
- `rx_bufs`: RX buffer set (or NULL)

**Returns:**
- `0`: Success (master mode)
- `> 0`: Frames received (slave mode)
- `-ENOTSUP`: Unsupported configuration
- `-EINVAL`: Invalid parameter
- `-errno`: Other failure

### spi_transceive_dt

```c
int spi_transceive_dt(const struct spi_dt_spec *spec,
                      const struct spi_buf_set *tx_bufs,
                      const struct spi_buf_set *rx_bufs);
```

Devicetree variant. Equivalent to `spi_transceive(spec->bus, &spec->config, tx_bufs, rx_bufs)`.

### spi_read

```c
int spi_read(const struct device *dev,
             const struct spi_config *config,
             const struct spi_buf_set *rx_bufs);
```

Read-only transfer (TX sends zeros or overrun character).

### spi_read_dt

```c
int spi_read_dt(const struct spi_dt_spec *spec,
                const struct spi_buf_set *rx_bufs);
```

Devicetree variant of `spi_read`.

### spi_write

```c
int spi_write(const struct device *dev,
              const struct spi_config *config,
              const struct spi_buf_set *tx_bufs);
```

Write-only transfer (RX data discarded).

### spi_write_dt

```c
int spi_write_dt(const struct spi_dt_spec *spec,
                 const struct spi_buf_set *tx_bufs);
```

Devicetree variant of `spi_write`.

### spi_release

```c
int spi_release(const struct device *dev,
                const struct spi_config *config);
```

Release locked SPI device. Use after transactions with `SPI_LOCK_ON` or `SPI_HOLD_ON_CS`.

### spi_release_dt

```c
int spi_release_dt(const struct spi_dt_spec *spec);
```

Devicetree variant of `spi_release`.

---

## Asynchronous API

Requires `CONFIG_SPI_ASYNC=y`. Functions return immediately; completion is signaled via callback or poll signal.

### spi_transceive_cb

```c
int spi_transceive_cb(const struct device *dev,
                      const struct spi_config *config,
                      const struct spi_buf_set *tx_bufs,
                      const struct spi_buf_set *rx_bufs,
                      spi_callback_t callback,
                      void *userdata);
```

Async transfer with callback notification.

**Callback signature:**
```c
typedef void (*spi_callback_t)(const struct device *dev,
                               int result,
                               void *data);
```

- `result`: 0 on success, -errno on failure
- `data`: userdata passed to transceive_cb

**Returns:**
- `0`: Transfer started successfully
- `-EBUSY`: Bus busy (previous transfer in progress)
- `-errno`: Other failure

### spi_transceive_signal

```c
int spi_transceive_signal(const struct device *dev,
                          const struct spi_config *config,
                          const struct spi_buf_set *tx_bufs,
                          const struct spi_buf_set *rx_bufs,
                          struct k_poll_signal *sig);
```

Async transfer with k_poll_signal notification. Requires `CONFIG_SPI_ASYNC=y` and `CONFIG_POLL=y`.

**Signal result:** The signal is raised with result code (0 = success, -errno = failure).

### spi_read_signal / spi_write_signal

```c
int spi_read_signal(const struct device *dev,
                    const struct spi_config *config,
                    const struct spi_buf_set *rx_bufs,
                    struct k_poll_signal *sig);

int spi_write_signal(const struct device *dev,
                     const struct spi_config *config,
                     const struct spi_buf_set *tx_bufs,
                     struct k_poll_signal *sig);
```

Async read/write with signal notification.

---

## Utility Functions

### spi_is_ready_dt

```c
bool spi_is_ready_dt(const struct spi_dt_spec *spec);
```

Check if SPI bus and CS GPIO (if used) are ready.

**Returns:** `true` if ready, `false` otherwise.

### spi_cs_is_gpio / spi_cs_is_gpio_dt

```c
bool spi_cs_is_gpio(const struct spi_config *config);
bool spi_cs_is_gpio_dt(const struct spi_dt_spec *spec);
```

Check if CS is controlled via GPIO.

---

## Devicetree Macros

### SPI_DT_SPEC_GET

```c
#define SPI_DT_SPEC_GET(node_id, operation_, ...)
```

Initialize `struct spi_dt_spec` from devicetree.

**Example:**
```c
static const struct spi_dt_spec my_spi = SPI_DT_SPEC_GET(
    DT_NODELABEL(my_device),
    SPI_OP_MODE_MASTER | SPI_WORD_SET(8)
);
```

### SPI_DT_SPEC_INST_GET

```c
#define SPI_DT_SPEC_INST_GET(inst, operation_, ...)
```

Same as `SPI_DT_SPEC_GET` but uses `DT_DRV_INST(inst)`.

### SPI_CONFIG_DT

```c
#define SPI_CONFIG_DT(node_id, operation_, ...)
```

Initialize `struct spi_config` from devicetree (without bus pointer).

### SPI_CS_CONTROL_INIT

```c
#define SPI_CS_CONTROL_INIT(node_id)
```

Initialize `struct spi_cs_control` from devicetree.

### SPI_CS_GPIOS_DT_SPEC_GET

```c
#define SPI_CS_GPIOS_DT_SPEC_GET(spi_dev)
```

Get GPIO spec for a SPI device's chip select.

---

## Operation Flags Reference

Combine with bitwise OR for `spi_config.operation`:

| Flag | Value | Description |
|------|-------|-------------|
| `SPI_OP_MODE_MASTER` | 0 | Controller mode (default) |
| `SPI_OP_MODE_SLAVE` | BIT(0) | Peripheral mode |
| `SPI_MODE_CPOL` | BIT(1) | Clock idle high |
| `SPI_MODE_CPHA` | BIT(2) | Sample on second edge |
| `SPI_MODE_LOOP` | BIT(3) | Loopback mode (testing) |
| `SPI_TRANSFER_LSB` | BIT(4) | LSB first |
| `SPI_WORD_SET(n)` | n << 5 | Word size (1-64 bits) |
| `SPI_HOLD_ON_CS` | BIT(12) | Keep CS active after transfer |
| `SPI_LOCK_ON` | BIT(13) | Lock bus for caller |
| `SPI_CS_ACTIVE_HIGH` | BIT(14) | CS active high |
| `SPI_LINES_DUAL` | 1 << 16 | Dual MISO (extended) |
| `SPI_LINES_QUAD` | 2 << 16 | Quad MISO (extended) |
| `SPI_LINES_OCTAL` | 3 << 16 | Octal MISO (extended) |

**Note:** `SPI_LINES_*` require `CONFIG_SPI_EXTENDED_MODES=y`.
