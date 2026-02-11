# Memory Slabs

## Overview

Memory slabs provide fixed-size block allocation with:
- Zero fragmentation
- O(1) constant-time allocation
- Blocking wait support
- ISR-safe allocation with `K_NO_WAIT`

Best for: protocol buffers, sensor samples, message queues, any fixed-size data structures.

## Definition

### Static (Compile-Time)

```c
// K_MEM_SLAB_DEFINE(name, block_size, num_blocks, align)
K_MEM_SLAB_DEFINE(my_slab, 64, 10, 4);

// Private scope
K_MEM_SLAB_DEFINE_STATIC(my_slab, 64, 10, 4);
```

### Runtime Initialization

```c
struct k_mem_slab my_slab;
char __aligned(4) my_buffer[10 * 64];  // num_blocks * block_size

k_mem_slab_init(&my_slab, my_buffer, 64, 10);
```

## Allocation

```c
void *block;

// Non-blocking (ISR-safe)
if (k_mem_slab_alloc(&my_slab, &block, K_NO_WAIT) == 0) {
    // Use block
} else {
    // No blocks available
}

// Blocking with timeout
int ret = k_mem_slab_alloc(&my_slab, &block, K_MSEC(100));
if (ret == 0) {
    memset(block, 0, 64);
}

// Blocking forever
k_mem_slab_alloc(&my_slab, &block, K_FOREVER);
```

## Deallocation

```c
k_mem_slab_free(&my_slab, block);
```

## Status Queries

```c
// Number of currently used blocks
uint32_t used = k_mem_slab_num_used_get(&my_slab);

// Number of free blocks
uint32_t free = k_mem_slab_num_free_get(&my_slab);

// Maximum utilization (requires CONFIG_MEM_SLAB_TRACE_MAX_UTILIZATION)
uint32_t max_used = k_mem_slab_max_used_get(&my_slab);
```

## Practical Example: Message Pool

```c
struct sensor_msg {
    uint32_t timestamp;
    int16_t  data[3];
    uint8_t  sensor_id;
};

K_MEM_SLAB_DEFINE(sensor_msg_pool, sizeof(struct sensor_msg), 20, 4);

// Producer (can be ISR)
void sensor_isr(void *arg) {
    struct sensor_msg *msg;

    if (k_mem_slab_alloc(&sensor_msg_pool, (void **)&msg, K_NO_WAIT) == 0) {
        msg->timestamp = k_uptime_get_32();
        msg->data[0] = read_sensor_x();
        msg->data[1] = read_sensor_y();
        msg->data[2] = read_sensor_z();
        msg->sensor_id = SENSOR_ACCEL;

        k_msgq_put(&sensor_msgq, &msg, K_NO_WAIT);
    }
}

// Consumer
void sensor_thread(void) {
    struct sensor_msg *msg;

    while (1) {
        k_msgq_get(&sensor_msgq, &msg, K_FOREVER);
        process_sensor_data(msg);
        k_mem_slab_free(&sensor_msg_pool, msg);
    }
}
```

## Alignment Requirements

- Block size must be at least 4 bytes (for internal linkage)
- Block size must be multiple of alignment
- Buffer must be aligned to specified alignment

```c
// 32-byte aligned blocks of 128 bytes each
K_MEM_SLAB_DEFINE(aligned_slab, 128, 8, 32);
```

## Internal Operation

Slabs use a free list stored in the first 4 bytes of each unused block:
- No separate metadata structure
- All bookkeeping within the buffer itself
- Constant-time alloc/free via list head manipulation

## Kconfig

```kconfig
# Enable max utilization tracking
CONFIG_MEM_SLAB_TRACE_MAX_UTILIZATION=y
```

## Common Pitfalls

1. **Block size too small**: Must be at least 4 bytes and multiple of alignment.

2. **Misaligned buffer**: Runtime init requires properly aligned buffer.

3. **Blocking in ISR**: Use `K_NO_WAIT` in interrupt context.

4. **Wrong pointer to free**: Passing incorrect address corrupts the free list.

5. **Using freed block**: Block contents may be modified after free (free list linkage).
