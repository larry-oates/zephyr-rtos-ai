# Kernel Data Passing Objects

This reference details the specific implementation and usage of Zephyr kernel data passing objects.

## FIFO (First-In, First-Out)

A FIFO implements a traditional queue, allowing threads and ISRs to add and remove data items of any size.

### Key Concepts
*   **Structure**: Linked list of data items.
*   **Memory**: Caller usually provides memory. 1st word of data item reserved for kernel use (pointer to next).
*   **Alignment**: Data items must be aligned on word boundary.
*   **Allocation**: `k_fifo_alloc_put` can be used to use a resource pool instead of embedded pointers.

### Implementation

**Definition**:
```c
struct k_fifo my_fifo;
k_fifo_init(&my_fifo);
// OR
K_FIFO_DEFINE(my_fifo);
```

**Writing (Producer)**:
```c
struct data_item_t {
    void *fifo_reserved; /* 1st word reserved */
    uint32_t value;
};
struct data_item_t tx_data;
k_fifo_put(&my_fifo, &tx_data);
```

**Reading (Consumer)**:
```c
struct data_item_t *rx_data;
rx_data = k_fifo_get(&my_fifo, K_FOREVER);
```

---

## LIFO (Last-In, First-Out)

A LIFO is similar to a FIFO but processes data in reverse order (stack-like behavior for arbitrary data).

### Implementation

**Definition**:
```c
struct k_lifo my_lifo;
k_lifo_init(&my_lifo);
// OR
K_LIFO_DEFINE(my_lifo);
```

**Writing**: `k_lifo_put(&my_lifo, &data);`
**Reading**: `rx_data = k_lifo_get(&my_lifo, K_FOREVER);`

---

## Stack

A Stack allows threads and ISRs to exchange integer-sized values (machine words) in a LIFO manner.

### Key Concepts
*   **Structure**: Array of machine words.
*   **Limit**: Fixed capacity. Overrun causes undefined behavior.

### Implementation

**Definition**:
```c
k_stack_stack_t my_stack_data[20]; // Array to hold data
struct k_stack my_stack;
k_stack_init(&my_stack, my_stack_data, 20);
// OR
K_STACK_DEFINE(my_stack, 20);
```

**Writing**: `k_stack_push(&my_stack, data_val);`
**Reading**: `k_stack_pop(&my_stack, &rx_val, K_FOREVER);`

---

## Message Queue

A Message Queue allows asynchronous exchange of fixed-size data items via a ring buffer.

### Key Concepts
*   **Structure**: Ring buffer.
*   **Data**: Fixed size per item.
*   **Copying**: Data is copied into the buffer (put) and out of it (get). No internal pointers exposed.

### Implementation

**Definition**:
```c
struct k_msgq my_msgq;
char my_msgq_buffer[10 * sizeof(struct data_item)];
k_msgq_init(&my_msgq, my_msgq_buffer, sizeof(struct data_item), 10);
// OR
K_MSGQ_DEFINE(my_msgq, sizeof(struct data_item), 10, 4); // 4 is alignment
```

**Writing**: `k_msgq_put(&my_msgq, &data, K_NO_WAIT);` (returns non-zero if full)
**Reading**: `k_msgq_get(&my_msgq, &data, K_FOREVER);`
**Peeking**: `k_msgq_peek(&my_msgq, &data);`
**Purging**: `k_msgq_purge(&my_msgq);` (clears queue)

---

## Mailbox

A Mailbox provides synchronous or asynchronous exchange of variable-sized messages.

### Key Concepts
*   **Bidirectional**: Sender can get info back.
*   **Flow Control**: Synchronous mode blocks sender until received.
*   **Efficiency**: Can transfer large data by reference (pointer) to avoid copying.
*   **No ISRs**: Only threads can use mailboxes.

### Implementation

**Definition**:
```c
struct k_mbox my_mbox;
k_mbox_init(&my_mbox);
// OR
K_MBOX_DEFINE(my_mbox);
```

**Sending**:
```c
struct k_mbox_msg send_msg;
send_msg.info = 123; // App-specific info
send_msg.size = size;
send_msg.tx_data = buffer;
send_msg.tx_target_thread = K_ANY;
k_mbox_put(&my_mbox, &send_msg, K_FOREVER);
```

**Receiving**:
```c
struct k_mbox_msg recv_msg;
recv_msg.size = max_size;
recv_msg.rx_source_thread = K_ANY;
k_mbox_get(&my_mbox, &recv_msg, buffer, K_FOREVER);
```

---

## Pipe

A Pipe allows a byte stream (chunks of data) to be sent between threads.

### Key Concepts
*   **Stream**: Data is treated as a stream of bytes, not discrete messages.
*   **Partial Access**: Can read/write fewer bytes than requested if buffer full/empty.
*   **Ring Buffer**: Optional internal buffer. If 0 size, pipe is purely synchronous (direct copy from sender to receiver).

### Implementation

**Definition**:
```c
unsigned char my_ring_buffer[100];
struct k_pipe my_pipe;
k_pipe_init(&my_pipe, my_ring_buffer, sizeof(my_ring_buffer));
// OR
K_PIPE_DEFINE(my_pipe, 100, 4);
```

**Writing**:
```c
size_t bytes_written;
int ret = k_pipe_write(&my_pipe, data, total_size, &bytes_written, min_xfer, K_NO_WAIT);
```

**Reading**:
```c
size_t bytes_read;
int ret = k_pipe_read(&my_pipe, buffer, bytes_to_read, &bytes_read, min_xfer, K_FOREVER);
```
