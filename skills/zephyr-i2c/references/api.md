# I2C API Reference

Complete API reference for Zephyr I2C driver subsystem.

## Table of Contents

1. [Data Structures](#data-structures)
2. [Macros and Flags](#macros-and-flags)
3. [Synchronous API](#synchronous-api)
4. [Async API](#async-api)
5. [Target Mode API](#target-mode-api)
6. [RTIO API](#rtio-api)
7. [SMBus API](#smbus-api)

---

## Data Structures

### struct i2c_dt_spec

Devicetree-resolved I2C device specification.

```c
struct i2c_dt_spec {
    const struct device *bus;  /* I2C bus device */
    uint16_t addr;             /* Device address */
};
```

**Initialization macros:**
- `I2C_DT_SPEC_GET(node_id)` - Get spec from DT node
- `I2C_DT_SPEC_GET_BY_IDX(node_id, idx)` - Get spec by index
- `I2C_DT_SPEC_INST_GET(inst)` - Get spec from instance

### struct i2c_msg

Single I2C message for transfers.

```c
struct i2c_msg {
    uint8_t *buf;    /* Data buffer */
    uint32_t len;    /* Buffer length in bytes */
    uint8_t flags;   /* Message flags (I2C_MSG_*) */
};
```

### struct i2c_target_config

Configuration for I2C target (slave) mode.

```c
struct i2c_target_config {
    sys_snode_t node;
    uint8_t flags;
    uint16_t address;
    const struct i2c_target_callbacks *callbacks;
};
```

### struct i2c_target_callbacks

Callback functions for target mode operations.

```c
struct i2c_target_callbacks {
    i2c_target_write_requested_cb_t write_requested;
    i2c_target_read_requested_cb_t read_requested;
    i2c_target_write_received_cb_t write_received;
    i2c_target_read_processed_cb_t read_processed;
    i2c_target_stop_cb_t stop;
    i2c_target_error_cb_t error;
    /* Buffer mode (CONFIG_I2C_TARGET_BUFFER_MODE) */
    i2c_target_buf_write_received_cb_t buf_write_received;
    i2c_target_buf_read_requested_cb_t buf_read_requested;
};
```

---

## Macros and Flags

### Speed Configuration

| Macro | Value | Description |
|-------|-------|-------------|
| `I2C_SPEED_STANDARD` | 0x1 | 100 kHz |
| `I2C_SPEED_FAST` | 0x2 | 400 kHz |
| `I2C_SPEED_FAST_PLUS` | 0x3 | 1 MHz |
| `I2C_SPEED_HIGH` | 0x4 | 3.4 MHz |
| `I2C_SPEED_ULTRA` | 0x5 | 5 MHz |
| `I2C_SPEED_DT` | 0x6 | Use devicetree value |

**Speed macros:**
- `I2C_SPEED_SET(speed)` - Set speed in config
- `I2C_SPEED_GET(cfg)` - Get speed from config

### Message Flags

| Flag | Value | Description |
|------|-------|-------------|
| `I2C_MSG_WRITE` | 0 | Write operation |
| `I2C_MSG_READ` | BIT(0) | Read operation |
| `I2C_MSG_STOP` | BIT(1) | Send STOP after message |
| `I2C_MSG_RESTART` | BIT(2) | Send RESTART before message |
| `I2C_MSG_ADDR_10_BITS` | BIT(3) | Use 10-bit addressing |

### Mode Configuration

| Flag | Description |
|------|-------------|
| `I2C_MODE_CONTROLLER` | Controller (master) mode |

### Target Flags

| Flag | Description |
|------|-------------|
| `I2C_TARGET_FLAGS_ADDR_10_BITS` | 10-bit target address |

### Error Reasons

```c
enum i2c_error_reason {
    I2C_ERROR_TIMEOUT,
    I2C_ERROR_ARBITRATION,
    I2C_ERROR_SIZE,
    I2C_ERROR_DMA,
    I2C_ERROR_GENERIC
};
```

---

## Synchronous API

### Configuration

```c
int i2c_configure(const struct device *dev, uint32_t dev_config);
```
Configure I2C controller speed and mode.

```c
int i2c_get_config(const struct device *dev, uint32_t *dev_config);
```
Get current controller configuration.

### Core Transfer

```c
int i2c_transfer(const struct device *dev, struct i2c_msg *msgs,
                 uint8_t num_msgs, uint16_t addr);
```
Generic transfer with scatter-gather support.

```c
int i2c_transfer_dt(const struct i2c_dt_spec *spec, struct i2c_msg *msgs,
                    uint8_t num_msgs);
```
Transfer using devicetree spec (address from spec).

### Simple Read/Write

```c
int i2c_write(const struct device *dev, const uint8_t *buf,
              uint32_t num_bytes, uint16_t addr);
int i2c_write_dt(const struct i2c_dt_spec *spec, const uint8_t *buf,
                 uint32_t num_bytes);
```
Single write transaction.

```c
int i2c_read(const struct device *dev, uint8_t *buf,
             uint32_t num_bytes, uint16_t addr);
int i2c_read_dt(const struct i2c_dt_spec *spec, uint8_t *buf,
                uint32_t num_bytes);
```
Single read transaction.

```c
int i2c_write_read(const struct device *dev, uint16_t addr,
                   const void *write_buf, size_t num_write,
                   void *read_buf, size_t num_read);
int i2c_write_read_dt(const struct i2c_dt_spec *spec,
                      const void *write_buf, size_t num_write,
                      void *read_buf, size_t num_read);
```
Combined write-then-read with RESTART.

### Burst Access (Register-Based)

```c
int i2c_burst_read(const struct device *dev, uint16_t dev_addr,
                   uint8_t start_addr, uint8_t *buf, uint32_t num_bytes);
int i2c_burst_read_dt(const struct i2c_dt_spec *spec,
                      uint8_t start_addr, uint8_t *buf, uint32_t num_bytes);
```
Read multiple bytes from register address.

```c
int i2c_burst_write(const struct device *dev, uint16_t dev_addr,
                    uint8_t start_addr, const uint8_t *buf, uint32_t num_bytes);
int i2c_burst_write_dt(const struct i2c_dt_spec *spec,
                       uint8_t start_addr, const uint8_t *buf, uint32_t num_bytes);
```
Write multiple bytes to register address.

### Single Register Access

```c
int i2c_reg_read_byte(const struct device *dev, uint16_t dev_addr,
                      uint8_t reg_addr, uint8_t *value);
int i2c_reg_read_byte_dt(const struct i2c_dt_spec *spec,
                         uint8_t reg_addr, uint8_t *value);
```
Read single byte from register.

```c
int i2c_reg_write_byte(const struct device *dev, uint16_t dev_addr,
                       uint8_t reg_addr, uint8_t value);
int i2c_reg_write_byte_dt(const struct i2c_dt_spec *spec,
                          uint8_t reg_addr, uint8_t value);
```
Write single byte to register.

```c
int i2c_reg_update_byte(const struct device *dev, uint8_t dev_addr,
                        uint8_t reg_addr, uint8_t mask, uint8_t value);
int i2c_reg_update_byte_dt(const struct i2c_dt_spec *spec,
                           uint8_t reg_addr, uint8_t mask, uint8_t value);
```
Read-modify-write with mask.

### Utility Functions

```c
bool i2c_is_ready_dt(const struct i2c_dt_spec *spec);
```
Check if I2C device is ready.

```c
int i2c_recover_bus(const struct device *dev);
```
Attempt bus recovery (9 clock pulses).

```c
void i2c_dump_msgs(const struct device *dev, const struct i2c_msg *msgs,
                   uint8_t num_msgs, uint16_t addr);
```
Debug dump of I2C messages.

---

## Async API

Requires `CONFIG_I2C_CALLBACK=y`.

### Callback Type

```c
typedef void (*i2c_callback_t)(const struct device *dev, int result, void *data);
```

### Transfer Functions

```c
int i2c_transfer_cb(const struct device *dev, struct i2c_msg *msgs,
                    uint8_t num_msgs, uint16_t addr,
                    i2c_callback_t cb, void *userdata);
int i2c_transfer_cb_dt(const struct i2c_dt_spec *spec, struct i2c_msg *msgs,
                       uint8_t num_msgs, i2c_callback_t cb, void *userdata);
```
Async transfer with callback on completion.

```c
int i2c_write_read_cb(const struct device *dev, struct i2c_msg *msgs,
                      uint8_t num_msgs, uint16_t addr,
                      const void *write_buf, size_t num_write,
                      void *read_buf, size_t num_read,
                      i2c_callback_t cb, void *userdata);
int i2c_write_read_cb_dt(const struct i2c_dt_spec *spec, struct i2c_msg *msgs,
                         uint8_t num_msgs, const void *write_buf, size_t num_write,
                         void *read_buf, size_t num_read,
                         i2c_callback_t cb, void *userdata);
```
Async write-read with callback.

### Signal-Based Async

Requires `CONFIG_POLL=y`:

```c
int i2c_transfer_signal(const struct device *dev, struct i2c_msg *msgs,
                        uint8_t num_msgs, uint16_t addr,
                        struct k_poll_signal *sig);
```
Async transfer with k_poll_signal notification.

---

## Target Mode API

Requires `CONFIG_I2C_TARGET=y`.

### Registration

```c
int i2c_target_register(const struct device *dev,
                        struct i2c_target_config *cfg);
```
Register target device with callbacks on controller.

```c
int i2c_target_unregister(const struct device *dev,
                          struct i2c_target_config *cfg);
```
Unregister target device.

### Driver Registration

For target drivers (e.g., EEPROM emulation):

```c
int i2c_target_driver_register(const struct device *dev);
int i2c_target_driver_unregister(const struct device *dev);
```

### Callback Signatures

```c
/* Write request from controller */
typedef int (*i2c_target_write_requested_cb_t)(struct i2c_target_config *config);

/* Byte received from controller */
typedef int (*i2c_target_write_received_cb_t)(struct i2c_target_config *config,
                                               uint8_t val);

/* Read request from controller */
typedef int (*i2c_target_read_requested_cb_t)(struct i2c_target_config *config,
                                               uint8_t *val);

/* Byte sent to controller, provide next */
typedef int (*i2c_target_read_processed_cb_t)(struct i2c_target_config *config,
                                               uint8_t *val);

/* STOP condition received */
typedef int (*i2c_target_stop_cb_t)(struct i2c_target_config *config);

/* Error occurred */
typedef int (*i2c_target_error_cb_t)(struct i2c_target_config *config,
                                      enum i2c_error_reason reason);
```

### Buffer Mode Callbacks

Requires `CONFIG_I2C_TARGET_BUFFER_MODE=y`:

```c
typedef int (*i2c_target_buf_write_received_cb_t)(
    struct i2c_target_config *config,
    uint8_t *ptr, uint32_t len);

typedef int (*i2c_target_buf_read_requested_cb_t)(
    struct i2c_target_config *config,
    uint8_t **ptr, uint32_t *len);
```

---

## RTIO API

Requires `CONFIG_I2C_RTIO=y`. Real-time I/O subsystem integration.

### Device Definition

```c
I2C_DT_IODEV_DEFINE(name, node_id, addr);
I2C_IODEV_DEFINE(name, bus, addr);
```

### Transfer Functions

```c
struct rtio_sqe *i2c_rtio_copy(struct rtio *r, struct rtio_iodev *iodev,
                                const struct i2c_msg *msgs, uint8_t num_msgs);
```
Copy messages to RTIO submission queue.

```c
struct rtio_sqe *i2c_rtio_copy_reg_write_byte(struct rtio *r,
                                               struct rtio_iodev *iodev,
                                               uint8_t reg_addr, uint8_t data);
```
Queue single register write.

```c
struct rtio_sqe *i2c_rtio_copy_reg_burst_read(struct rtio *r,
                                               struct rtio_iodev *iodev,
                                               uint8_t start_addr,
                                               void *buf, size_t num_bytes);
```
Queue burst register read.

### Submission

```c
void i2c_iodev_submit(struct rtio_iodev_sqe *iodev_sqe);
```

---

## SMBus API

SMBus protocol functions in `<zephyr/drivers/smbus.h>`.

### Configuration

```c
int smbus_configure(const struct device *dev, uint32_t dev_config);
int smbus_get_config(const struct device *dev, uint32_t *dev_config);
```

### SMBus Commands

```c
int smbus_quick(const struct device *dev, uint16_t addr,
                enum smbus_direction direction);
```
Quick command (address only).

```c
int smbus_byte_write(const struct device *dev, uint16_t addr, uint8_t byte);
int smbus_byte_read(const struct device *dev, uint16_t addr, uint8_t *byte);
```
Send/receive byte (no command).

```c
int smbus_byte_data_write(const struct device *dev, uint16_t addr,
                          uint8_t cmd, uint8_t byte);
int smbus_byte_data_read(const struct device *dev, uint16_t addr,
                         uint8_t cmd, uint8_t *byte);
```
Write/read byte with command.

```c
int smbus_word_data_write(const struct device *dev, uint16_t addr,
                          uint8_t cmd, uint16_t word);
int smbus_word_data_read(const struct device *dev, uint16_t addr,
                         uint8_t cmd, uint16_t *word);
```
Write/read word with command.

```c
int smbus_pcall(const struct device *dev, uint16_t addr, uint8_t cmd,
                uint16_t send_word, uint16_t *recv_word);
```
Process call (send word, receive word).

```c
int smbus_block_write(const struct device *dev, uint16_t addr, uint8_t cmd,
                      uint8_t count, uint8_t *buf);
int smbus_block_read(const struct device *dev, uint16_t addr, uint8_t cmd,
                     uint8_t *count, uint8_t *buf);
```
Block write/read (up to 32 bytes).

```c
int smbus_block_pcall(const struct device *dev, uint16_t addr, uint8_t cmd,
                      uint8_t snd_count, uint8_t *snd_buf,
                      uint8_t *rcv_count, uint8_t *rcv_buf);
```
Block process call.

### SMBus Mode Flags

| Flag | Description |
|------|-------------|
| `SMBUS_MODE_CONTROLLER` | Controller mode |
| `SMBUS_MODE_PEC` | Packet error checking |
| `SMBUS_MODE_HOST_NOTIFY` | Host notify support |
| `SMBUS_MODE_SMBALERT` | SMBus alert support |

### SMBus Alert/Notify Callbacks

```c
int smbus_smbalert_set_cb(const struct device *dev, struct smbus_callback *cb);
int smbus_smbalert_remove_cb(const struct device *dev, struct smbus_callback *cb);
int smbus_host_notify_set_cb(const struct device *dev, struct smbus_callback *cb);
int smbus_host_notify_remove_cb(const struct device *dev, struct smbus_callback *cb);
```
