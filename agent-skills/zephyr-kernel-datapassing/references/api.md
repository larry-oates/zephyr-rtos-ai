# API Reference

## Header Files

| Object | Header |
| :--- | :--- |
| FIFO, LIFO, Stack, Message Queue, Mailbox, Pipe | `<zephyr/kernel.h>` |
| ZBus | `<zephyr/zbus/zbus.h>` |
| Ring Buffer | `<zephyr/sys/ring_buffer.h>` |

## Kconfig Options

### FIFO / LIFO

No specific Kconfig required. Always available.

### Stack

No specific config, always available.

### Message Queue

```kconfig
CONFIG_NUM_MBOX_ASYNC_MSGS=10  # Max async mailbox messages (if using async)
```

### Mailbox

```kconfig
CONFIG_NUM_MBOX_ASYNC_MSGS=10  # Number of async message descriptors
```

### Pipe

No specific config, always available.

### ZBus

```kconfig
CONFIG_ZBUS=y                    # Enable ZBus subsystem
CONFIG_ZBUS_CHANNEL_NAME=y       # Include channel names (debugging)
CONFIG_ZBUS_RUNTIME_OBSERVERS=y  # Allow runtime observer add/remove
CONFIG_ZBUS_ASSERT_MOCK=y        # Enable mocking for tests
```

### Ring Buffer

Part of core, always available.

---

## Key API Functions

### FIFO

```c
void k_fifo_init(struct k_fifo *fifo);
void k_fifo_put(struct k_fifo *fifo, void *data);
void *k_fifo_get(struct k_fifo *fifo, k_timeout_t timeout);
void *k_fifo_peek_head(struct k_fifo *fifo);
void *k_fifo_peek_tail(struct k_fifo *fifo);
int k_fifo_alloc_put(struct k_fifo *fifo, void *data);  /* Uses heap */
void k_fifo_cancel_wait(struct k_fifo *fifo);
```

**Macros:**
- `K_FIFO_DEFINE(name)` - Static definition

### LIFO

```c
void k_lifo_init(struct k_lifo *lifo);
void k_lifo_put(struct k_lifo *lifo, void *data);
void *k_lifo_get(struct k_lifo *lifo, k_timeout_t timeout);
int k_lifo_alloc_put(struct k_lifo *lifo, void *data);  /* Uses heap */
```

**Macros:**
- `K_LIFO_DEFINE(name)` - Static definition

### Stack

```c
void k_stack_init(struct k_stack *stack, stack_data_t *buffer, uint32_t num_entries);
int k_stack_push(struct k_stack *stack, stack_data_t data);
int k_stack_pop(struct k_stack *stack, stack_data_t *data, k_timeout_t timeout);
int k_stack_alloc_init(struct k_stack *stack, uint32_t num_entries);  /* Uses heap */
int k_stack_cleanup(struct k_stack *stack);
```

**Macros:**
- `K_STACK_DEFINE(name, stack_num_entries)` - Static definition

### Message Queue

```c
void k_msgq_init(struct k_msgq *msgq, char *buffer, size_t msg_size, uint32_t max_msgs);
int k_msgq_put(struct k_msgq *msgq, const void *data, k_timeout_t timeout);
int k_msgq_get(struct k_msgq *msgq, void *data, k_timeout_t timeout);
int k_msgq_peek(struct k_msgq *msgq, void *data);
int k_msgq_peek_at(struct k_msgq *msgq, void *data, uint32_t idx);
void k_msgq_purge(struct k_msgq *msgq);
uint32_t k_msgq_num_free_get(struct k_msgq *msgq);
uint32_t k_msgq_num_used_get(struct k_msgq *msgq);
int k_msgq_alloc_init(struct k_msgq *msgq, size_t msg_size, uint32_t max_msgs);
int k_msgq_cleanup(struct k_msgq *msgq);
```

**Macros:**
- `K_MSGQ_DEFINE(name, msg_size, max_msgs, align)` - Static definition

### Mailbox

```c
void k_mbox_init(struct k_mbox *mbox);
int k_mbox_put(struct k_mbox *mbox, struct k_mbox_msg *tx_msg, k_timeout_t timeout);
void k_mbox_async_put(struct k_mbox *mbox, struct k_mbox_msg *tx_msg, struct k_sem *sem);
int k_mbox_get(struct k_mbox *mbox, struct k_mbox_msg *rx_msg, void *buffer, k_timeout_t timeout);
void k_mbox_data_get(struct k_mbox_msg *rx_msg, void *buffer);
```

**Macros:**
- `K_MBOX_DEFINE(name)` - Static definition

### Pipe

```c
void k_pipe_init(struct k_pipe *pipe, unsigned char *buffer, size_t size);
int k_pipe_put(struct k_pipe *pipe, const void *data, size_t bytes_to_write,
               size_t *bytes_written, size_t min_xfer, k_timeout_t timeout);
int k_pipe_get(struct k_pipe *pipe, void *data, size_t bytes_to_read,
               size_t *bytes_read, size_t min_xfer, k_timeout_t timeout);
int k_pipe_alloc_init(struct k_pipe *pipe, size_t size);
int k_pipe_cleanup(struct k_pipe *pipe);
size_t k_pipe_read_avail(struct k_pipe *pipe);
size_t k_pipe_write_avail(struct k_pipe *pipe);
void k_pipe_flush(struct k_pipe *pipe);
void k_pipe_buffer_flush(struct k_pipe *pipe);
```

**Macros:**
- `K_PIPE_DEFINE(name, pipe_buffer_size, pipe_align)` - Static definition

### ZBus

```c
int zbus_chan_pub(const struct zbus_channel *chan, const void *msg, k_timeout_t timeout);
int zbus_chan_read(const struct zbus_channel *chan, void *msg, k_timeout_t timeout);
int zbus_chan_claim(const struct zbus_channel *chan, k_timeout_t timeout);
int zbus_chan_finish(const struct zbus_channel *chan);
int zbus_chan_add_obs(const struct zbus_channel *chan, const struct zbus_observer *obs, k_timeout_t timeout);
int zbus_chan_rm_obs(const struct zbus_channel *chan, const struct zbus_observer *obs, k_timeout_t timeout);
int zbus_sub_wait(const struct zbus_observer *sub, const struct zbus_channel **chan, k_timeout_t timeout);
```

**Macros:**
- `ZBUS_CHAN_DEFINE(name, type, validator, user_data, observers, init_val)`
- `ZBUS_LISTENER_DEFINE(name, cb)`
- `ZBUS_MSG_SUBSCRIBER_DEFINE(name)`
- `ZBUS_SUBSCRIBER_DEFINE(name, queue_size)` (deprecated, use MSG_SUBSCRIBER)

### Ring Buffer

```c
void ring_buf_init(struct ring_buf *buf, uint32_t size, uint8_t *data);
uint32_t ring_buf_put(struct ring_buf *buf, const uint8_t *data, uint32_t size);
uint32_t ring_buf_get(struct ring_buf *buf, uint8_t *data, uint32_t size);
uint32_t ring_buf_peek(struct ring_buf *buf, uint8_t *data, uint32_t size);
uint32_t ring_buf_put_claim(struct ring_buf *buf, uint8_t **data, uint32_t size);
int ring_buf_put_finish(struct ring_buf *buf, uint32_t size);
uint32_t ring_buf_get_claim(struct ring_buf *buf, uint8_t **data, uint32_t size);
int ring_buf_get_finish(struct ring_buf *buf, uint32_t size);
uint32_t ring_buf_space_get(struct ring_buf *buf);
uint32_t ring_buf_size_get(struct ring_buf *buf);
bool ring_buf_is_empty(struct ring_buf *buf);
void ring_buf_reset(struct ring_buf *buf);
```

**Macros:**
- `RING_BUF_DECLARE(name, size)` - Static definition

---

## Sample Directories

| Sample | Path |
| :--- | :--- |
| Message Queue | `<zephyr-ws-dir>/zephyr/samples/kernel/msg_queue` |
| Philosophers | `<zephyr-ws-dir>/zephyr/samples/philosophers` |
| ZBus Samples | `<zephyr-ws-dir>/zephyr/samples/subsys/zbus/` |

## Documentation Paths

| Topic | Path |
| :--- | :--- |
| Data Passing | `<zephyr-ws-dir>/zephyr/doc/kernel/services/data_passing/` |
| ZBus | `<zephyr-ws-dir>/zephyr/doc/services/zbus/` |
