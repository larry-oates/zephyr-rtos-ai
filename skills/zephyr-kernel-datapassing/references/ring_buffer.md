# Ring Buffer

A Ring Buffer (circular buffer) is a lower-level data structure for efficient byte-stream handling, commonly used in drivers and protocol stacks.

## Concepts

-   **Structure**: Fixed-size byte array with head and tail pointers.
-   **Library-level**: Part of `sys/` utilities, not a kernel object (no built-in blocking).
-   **Lock-free**: Single-producer/single-consumer (SPSC) operations are lock-free.
-   **No Waiting**: Does not support thread blocking; use with semaphores/events for synchronization.

## When to Use Ring Buffer

-   **Driver buffers**: UART RX/TX, SPI, I2C byte streams.
-   **Protocol parsing**: Accumulate incoming bytes until a complete frame.
-   **Performance-critical paths**: Lower overhead than kernel message queues.
-   **ISR-to-thread**: Buffer data in ISR, process in thread (with separate signaling).

## Kconfig

Ring buffers are always available (part of core library). No specific Kconfig needed.

## Implementation

### Including

```c
#include <zephyr/sys/ring_buffer.h>
```

### Defining

```c
/* Static definition with compile-time buffer */
RING_BUF_DECLARE(my_ring_buf, 256);

/* OR runtime initialization */
uint8_t buffer[256];
struct ring_buf my_ring_buf;
ring_buf_init(&my_ring_buf, sizeof(buffer), buffer);
```

### Writing (Producer)

```c
uint8_t data[] = {0x01, 0x02, 0x03};
uint32_t written = ring_buf_put(&my_ring_buf, data, sizeof(data));
if (written < sizeof(data)) {
    /* Buffer full, only partial write */
}
```

### Reading (Consumer)

```c
uint8_t rx_data[64];
uint32_t read = ring_buf_get(&my_ring_buf, rx_data, sizeof(rx_data));
/* read contains number of bytes actually retrieved */
```

### Zero-Copy Access (Advanced)

For high-performance scenarios, claim buffer space directly:

```c
/* Producer: claim space */
uint8_t *ptr;
uint32_t space = ring_buf_put_claim(&my_ring_buf, &ptr, 100);
/* Write directly to ptr (up to 'space' bytes) */
memcpy(ptr, source_data, actual_len);
ring_buf_put_finish(&my_ring_buf, actual_len);

/* Consumer: get data pointer */
uint8_t *ptr;
uint32_t available = ring_buf_get_claim(&my_ring_buf, &ptr, 100);
/* Read directly from ptr */
process_data(ptr, available);
ring_buf_get_finish(&my_ring_buf, available);
```

### Querying State

```c
uint32_t free_space = ring_buf_space_get(&my_ring_buf);
uint32_t used_space = ring_buf_size_get(&my_ring_buf);
bool is_empty = ring_buf_is_empty(&my_ring_buf);
ring_buf_reset(&my_ring_buf);  /* Clear buffer */
```

## Key APIs

| Function | Description |
| :--- | :--- |
| `RING_BUF_DECLARE` | Static buffer definition |
| `ring_buf_init` | Runtime initialization |
| `ring_buf_put` | Write bytes (copy) |
| `ring_buf_get` | Read bytes (copy) |
| `ring_buf_put_claim` / `ring_buf_put_finish` | Zero-copy write |
| `ring_buf_get_claim` / `ring_buf_get_finish` | Zero-copy read |
| `ring_buf_peek` | Read without consuming |
| `ring_buf_space_get` | Get free space |
| `ring_buf_size_get` | Get used space |
| `ring_buf_reset` | Clear the buffer |
| `ring_buf_is_empty` | Check if empty |

## Comparison with Kernel Pipe

| Aspect | Ring Buffer | Pipe |
| :--- | :--- | :--- |
| **Blocking** | No (manual sync needed) | Yes (kernel-managed) |
| **ISR Safe** | Yes (no blocking calls) | Yes (with K_NO_WAIT) |
| **Overhead** | Minimal | Higher (kernel object) |
| **Use Case** | Drivers, low-level | Application-level streams |
| **Zero-Copy** | Yes (claim/finish) | No |
| **Thread Safety** | SPSC lock-free; MPMC needs external lock | Built-in |

## Common Patterns

### UART RX with Ring Buffer

```c
RING_BUF_DECLARE(uart_rx_buf, 512);
K_SEM_DEFINE(uart_rx_sem, 0, 1);

/* ISR callback */
void uart_isr_callback(const struct device *dev, void *user_data)
{
    uint8_t byte;
    while (uart_fifo_read(dev, &byte, 1) > 0) {
        ring_buf_put(&uart_rx_buf, &byte, 1);
    }
    k_sem_give(&uart_rx_sem);  /* Signal data available */
}

/* Thread */
void uart_thread(void)
{
    uint8_t data[64];
    while (1) {
        k_sem_take(&uart_rx_sem, K_FOREVER);
        uint32_t len = ring_buf_get(&uart_rx_buf, data, sizeof(data));
        process_uart_data(data, len);
    }
}
```

## Best Practices

1.  **Size appropriately**: Buffer should handle worst-case burst without overflow.
2.  **Use zero-copy for performance**: Avoid memcpy when possible.
3.  **Add synchronization for MPMC**: Use mutex for multiple producers/consumers.
4.  **Pair with semaphore/event**: For thread blocking on data availability.
5.  **Check return values**: Partial reads/writes are common.
