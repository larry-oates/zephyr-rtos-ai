# Memory Blocks (sys_mem_blocks)

## Overview

`sys_mem_blocks` is a fixed-size block allocator with:
- External bookkeeping (bitmap stored separately from buffer)
- Multi-block atomic allocation
- Support for non-contiguous block results (scatter-gather)
- Buffer can reside in power-down memory regions

Best for: DMA scatter-gather, power-managed memory regions, multi-block allocations.

## Key Differences from k_mem_slab

| Feature | k_mem_slab | sys_mem_blocks |
|---------|------------|----------------|
| Bookkeeping | In-buffer (free list) | External (bitmap) |
| Multi-block alloc | No | Yes |
| Contiguous result | N/A | Not guaranteed |
| Blocking wait | Yes | No |
| Synchronized | Yes | No |
| Power-down buffer | No | Yes |

## Definition

### Static (Compile-Time)

```c
#include <zephyr/sys/mem_blocks.h>

// SYS_MEM_BLOCKS_DEFINE(name, block_size, num_blocks, align)
SYS_MEM_BLOCKS_DEFINE(my_blocks, 64, 16, 4);

// Private scope
SYS_MEM_BLOCKS_DEFINE_STATIC(my_blocks, 64, 16, 4);
```

### With External Buffer

```c
uint8_t __aligned(4) backing_buffer[64 * 16];
SYS_MEM_BLOCKS_DEFINE_WITH_EXT_BUF(my_blocks, 64, 16, backing_buffer);
```

## Single Block Allocation

```c
void *block;

int ret = sys_mem_blocks_alloc(&my_blocks, 1, &block);
if (ret == 0) {
    // Use block
}

// Free single block
sys_mem_blocks_free(&my_blocks, 1, &block);
```

## Multi-Block Allocation

Allocate multiple blocks atomically. Blocks may not be contiguous.

```c
uintptr_t blocks[4];

int ret = sys_mem_blocks_alloc(&my_blocks, 4, blocks);
if (ret == 0) {
    // blocks[0..3] contain addresses of allocated blocks
    // These may NOT be contiguous in memory
}

// Free all blocks
sys_mem_blocks_free(&my_blocks, 4, blocks);
```

## Contiguous Allocation

When contiguous memory is required:

```c
void *ptr;
int ret = sys_mem_blocks_alloc_contiguous(&my_blocks, 4, &ptr);
if (ret == 0) {
    // ptr points to 4 contiguous blocks
}
```

## Multi Memory Blocks Group

Manage multiple allocators as a group with custom selection logic.

### Setup

```c
sys_mem_blocks_t *choice_fn(struct sys_multi_mem_blocks *group, void *cfg) {
    uintptr_t attr = (uintptr_t)cfg;
    // Select allocator based on attributes
    if (attr & ATTR_DMA) {
        return &dma_blocks;
    }
    return &normal_blocks;
}

SYS_MEM_BLOCKS_DEFINE(normal_blocks, 64, 16, 4);
SYS_MEM_BLOCKS_DEFINE(dma_blocks, 64, 8, 4);

struct sys_multi_mem_blocks block_group;

void init(void) {
    sys_multi_mem_blocks_init(&block_group, choice_fn);
    sys_multi_mem_blocks_add_allocator(&block_group, &normal_blocks);
    sys_multi_mem_blocks_add_allocator(&block_group, &dma_blocks);
}
```

### Allocation

```c
uintptr_t blocks[2];
size_t block_size;

int ret = sys_multi_mem_blocks_alloc(&block_group,
                                      UINT_TO_POINTER(ATTR_DMA),
                                      2, blocks, &block_size);

// Free (no config needed—auto-detected)
sys_multi_mem_blocks_free(&block_group, 2, blocks);
```

## DMA Scatter-Gather Example

```c
SYS_MEM_BLOCKS_DEFINE(dma_pool, DMA_BLOCK_SIZE, 32, 4);

struct dma_block_config dma_cfg[MAX_DMA_BLOCKS];
uintptr_t blocks[MAX_DMA_BLOCKS];

int setup_dma_transfer(size_t total_size) {
    int num_blocks = DIV_ROUND_UP(total_size, DMA_BLOCK_SIZE);

    int ret = sys_mem_blocks_alloc(&dma_pool, num_blocks, blocks);
    if (ret != 0) {
        return ret;
    }

    // Configure scatter-gather DMA
    for (int i = 0; i < num_blocks; i++) {
        dma_cfg[i].source_address = blocks[i];
        dma_cfg[i].block_size = DMA_BLOCK_SIZE;
        if (i < num_blocks - 1) {
            dma_cfg[i].next_block = &dma_cfg[i + 1];
        }
    }

    return 0;
}
```

## Power-Down Memory Example

Buffer in external RAM that can be powered down:

```c
// Buffer in special memory section
uint8_t __aligned(4) __attribute__((section(".ext_ram")))
    ext_buffer[64 * 32];

// Bookkeeping stays in always-on RAM
SYS_MEM_BLOCKS_DEFINE_WITH_EXT_BUF(ext_blocks, 64, 32, ext_buffer);

// Before power-down: free all blocks or track allocations
// After power-up: buffer contents are lost but allocator state preserved
```

## Synchronization

**sys_mem_blocks is NOT synchronized**. Wrap with mutex if needed:

```c
K_MUTEX_DEFINE(blocks_mutex);

void *safe_alloc(void) {
    uintptr_t block;
    k_mutex_lock(&blocks_mutex, K_FOREVER);
    int ret = sys_mem_blocks_alloc(&my_blocks, 1, &block);
    k_mutex_unlock(&blocks_mutex);
    return (ret == 0) ? (void *)block : NULL;
}
```

## Common Pitfalls

1. **Assuming contiguity**: Multi-block alloc does NOT guarantee contiguous blocks.

2. **No synchronization**: Must protect concurrent access manually.

3. **Blocking expectation**: No blocking wait—returns error immediately if unavailable.

4. **Wrong block count to free**: Must free exact number of blocks allocated.
