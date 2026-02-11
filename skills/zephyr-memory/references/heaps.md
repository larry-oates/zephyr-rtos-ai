# Heaps

## Overview

Zephyr provides three heap abstractions for variable-size dynamic memory allocation:
- **k_heap**: Kernel-synchronized heap with blocking support
- **sys_heap**: Low-level unsynchronized heap
- **System Heap**: Global malloc-like interface (`k_malloc`/`k_free`)

## k_heap (Recommended)

Thread-safe heap with blocking allocation support.

### Definition

```c
// Static definition
K_HEAP_DEFINE(my_heap, 4096);

// Runtime initialization
struct k_heap my_heap;
uint8_t __aligned(8) heap_buffer[4096];
k_heap_init(&my_heap, heap_buffer, sizeof(heap_buffer));
```

### Allocation

```c
// Non-blocking (ISR-safe)
void *ptr = k_heap_alloc(&my_heap, 256, K_NO_WAIT);
if (ptr == NULL) {
    // Handle allocation failure
}

// Blocking with timeout
void *ptr = k_heap_alloc(&my_heap, 256, K_MSEC(100));

// Blocking forever
void *ptr = k_heap_alloc(&my_heap, 256, K_FOREVER);

// Aligned allocation
void *ptr = k_heap_aligned_alloc(&my_heap, 64, 256, K_NO_WAIT);
```

### Deallocation

```c
k_heap_free(&my_heap, ptr);
```

## sys_heap (Low-Level)

Unsynchronized heap for custom synchronization or single-threaded contexts.

**Critical:** Caller must ensure serialization—concurrent access causes corruption.

### Usage

```c
#include <zephyr/sys/sys_heap.h>

struct sys_heap my_sys_heap;
uint8_t __aligned(8) buffer[4096];

// Initialize
sys_heap_init(&my_sys_heap, buffer, sizeof(buffer));

// Allocate (no synchronization!)
void *ptr = sys_heap_alloc(&my_sys_heap, 256);
void *aligned_ptr = sys_heap_aligned_alloc(&my_sys_heap, 64, 256);

// Free
sys_heap_free(&my_sys_heap, ptr);
```

### Reallocation

```c
void *new_ptr = sys_heap_realloc(&my_sys_heap, old_ptr, new_size);
```

## System Heap (k_malloc)

Global heap for simple malloc-style allocation. Configure size via Kconfig.

### Kconfig

```kconfig
CONFIG_HEAP_MEM_POOL_SIZE=8192
```

### Usage

```c
// Allocate (non-blocking, returns NULL on failure)
char *buf = k_malloc(200);
if (buf != NULL) {
    memset(buf, 0, 200);
}

// Free
k_free(buf);

// Calloc (zeroed memory)
char *buf = k_calloc(10, sizeof(struct my_struct));

// Aligned allocation
void *ptr = k_aligned_alloc(64, 256);
```

**Note:** `k_malloc` cannot block—it returns NULL immediately if memory is unavailable.

## Multi-Heap

Manage multiple discontiguous memory regions as a unified allocator.

### Setup

```c
#include <zephyr/sys/multi_heap.h>

struct sys_multi_heap multi_heap;
struct sys_heap heap1, heap2;

// Choice function selects which heap to use
sys_heap_t *my_choice(struct sys_multi_heap *mheap, void *cfg,
                       size_t align, size_t size) {
    // Custom logic based on cfg, size, etc.
    return &heap1;
}

// Initialize
sys_multi_heap_init(&multi_heap, my_choice);
sys_multi_heap_add_heap(&multi_heap, &heap1, NULL);
sys_multi_heap_add_heap(&multi_heap, &heap2, NULL);
```

### Allocation

```c
void *ptr = sys_multi_heap_alloc(&multi_heap, cfg, size);
void *ptr = sys_multi_heap_aligned_alloc(&multi_heap, cfg, align, size);
sys_multi_heap_free(&multi_heap, ptr);
```

## Shared Multi-Heap

Attribute-based allocation from devicetree-defined memory regions.

### Devicetree

```dts
mem_cacheable: memory@10000000 {
    compatible = "mmio-sram";
    reg = <0x10000000 0x1000>;
    zephyr,memory-attr = <( DT_MEM_CACHEABLE | DT_MEM_SW_ALLOC_CACHE )>;
};

mem_dma: memory@20000000 {
    compatible = "mmio-sram";
    reg = <0x20000000 0x1000>;
    zephyr,memory-attr = <( DT_MEM_DMA | DT_MEM_SW_ALLOC_DMA )>;
};
```

### Usage

```c
#include <zephyr/mem_mgmt/mem_attr_heap.h>

// Initialize at boot
mem_attr_heap_pool_init();

// Allocate by attribute
void *cached = mem_attr_heap_alloc(DT_MEM_SW_ALLOC_CACHE, 256);
void *dma_buf = mem_attr_heap_alloc(DT_MEM_SW_ALLOC_DMA, 512);

// Free
mem_attr_heap_free(cached);
```

## Heap Listener (Debugging)

Monitor heap allocations for debugging memory leaks.

### Kconfig

```kconfig
CONFIG_HEAP_LISTENER=y
```

### Usage

```c
#include <zephyr/sys/heap_listener.h>

void alloc_cb(uintptr_t heap_id, void *mem, size_t bytes) {
    printk("Alloc %zu bytes at %p\n", bytes, mem);
}

void free_cb(uintptr_t heap_id, void *mem, size_t bytes) {
    printk("Free %zu bytes at %p\n", bytes, mem);
}

HEAP_LISTENER_ALLOC_DEFINE(my_listener, HEAP_ID_FROM_POINTER(&my_heap),
                            alloc_cb);
HEAP_LISTENER_FREE_DEFINE(my_free_listener, HEAP_ID_FROM_POINTER(&my_heap),
                           free_cb);

// Register
heap_listener_register(&my_listener);
heap_listener_register(&my_free_listener);
```

## Common Pitfalls

1. **Using k_malloc in ISR**: Never works—always returns NULL. Use `k_heap_alloc` with `K_NO_WAIT`.

2. **Forgetting to check NULL**: Always check allocation result before use.

3. **sys_heap without synchronization**: Concurrent access corrupts the heap.

4. **Single large system heap**: Causes fragmentation. Use multiple purpose-specific heaps.

5. **Blocking forever on low memory**: `K_FOREVER` can deadlock if no memory is ever freed.
