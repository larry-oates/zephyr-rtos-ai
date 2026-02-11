# API Reference

## Contents

- [Heaps](#heaps)
- [Memory Slabs](#memory-slabs)
- [Memory Blocks](#memory-blocks)
- [Memory Domains](#memory-domains)
- [Virtual Memory](#virtual-memory)
- [Kconfig Options](#kconfig-options)

---

## Heaps

### k_heap

```c
#include <zephyr/kernel.h>

// Static definition
K_HEAP_DEFINE(name, size)

// Runtime init
void k_heap_init(struct k_heap *heap, void *mem, size_t bytes);

// Allocation
void *k_heap_alloc(struct k_heap *heap, size_t bytes, k_timeout_t timeout);
void *k_heap_aligned_alloc(struct k_heap *heap, size_t align, size_t bytes,
                            k_timeout_t timeout);
void *k_heap_realloc(struct k_heap *heap, void *ptr, size_t bytes,
                      k_timeout_t timeout);

// Deallocation
void k_heap_free(struct k_heap *heap, void *mem);
```

### System Heap (k_malloc)

```c
#include <zephyr/kernel.h>

void *k_malloc(size_t size);
void *k_calloc(size_t nmemb, size_t size);
void *k_aligned_alloc(size_t align, size_t size);
void *k_realloc(void *ptr, size_t size);
void k_free(void *ptr);
```

### sys_heap

```c
#include <zephyr/sys/sys_heap.h>

void sys_heap_init(struct sys_heap *heap, void *mem, size_t bytes);
void *sys_heap_alloc(struct sys_heap *heap, size_t bytes);
void *sys_heap_aligned_alloc(struct sys_heap *heap, size_t align, size_t bytes);
void *sys_heap_realloc(struct sys_heap *heap, void *ptr, size_t bytes);
void sys_heap_free(struct sys_heap *heap, void *mem);
size_t sys_heap_usable_size(struct sys_heap *heap, void *ptr);
```

### Multi-Heap

```c
#include <zephyr/sys/multi_heap.h>

void sys_multi_heap_init(struct sys_multi_heap *heap,
                          sys_multi_heap_fn_t choice_fn);
void sys_multi_heap_add_heap(struct sys_multi_heap *mheap,
                              struct sys_heap *heap, void *user_data);
void *sys_multi_heap_alloc(struct sys_multi_heap *mheap, void *cfg, size_t bytes);
void *sys_multi_heap_aligned_alloc(struct sys_multi_heap *mheap, void *cfg,
                                    size_t align, size_t bytes);
void *sys_multi_heap_realloc(struct sys_multi_heap *mheap, void *cfg,
                              void *ptr, size_t bytes);
void sys_multi_heap_free(struct sys_multi_heap *mheap, void *mem);
```

### Shared Multi-Heap

```c
#include <zephyr/multi_heap/shared_multi_heap.h>

int shared_multi_heap_pool_init(void);
int shared_multi_heap_add(struct shared_multi_heap_region *region, void *user_data);
void *shared_multi_heap_alloc(enum shared_multi_heap_attr attr, size_t bytes);
void *shared_multi_heap_aligned_alloc(enum shared_multi_heap_attr attr,
                                       size_t align, size_t bytes);
void shared_multi_heap_free(void *block);
```

### Memory Attribute Heap

```c
#include <zephyr/mem_mgmt/mem_attr_heap.h>

int mem_attr_heap_pool_init(void);
void *mem_attr_heap_alloc(uint32_t attr, size_t bytes);
void *mem_attr_heap_aligned_alloc(uint32_t attr, size_t align, size_t bytes);
void mem_attr_heap_free(void *block);
```

---

## Memory Slabs

```c
#include <zephyr/kernel.h>

// Static definition
K_MEM_SLAB_DEFINE(name, block_size, num_blocks, align)
K_MEM_SLAB_DEFINE_STATIC(name, block_size, num_blocks, align)

// Runtime init
int k_mem_slab_init(struct k_mem_slab *slab, void *buffer,
                     size_t block_size, uint32_t num_blocks);

// Allocation
int k_mem_slab_alloc(struct k_mem_slab *slab, void **mem, k_timeout_t timeout);

// Deallocation
void k_mem_slab_free(struct k_mem_slab *slab, void *mem);

// Status
uint32_t k_mem_slab_num_used_get(struct k_mem_slab *slab);
uint32_t k_mem_slab_num_free_get(struct k_mem_slab *slab);
uint32_t k_mem_slab_max_used_get(struct k_mem_slab *slab);  // Needs CONFIG
```

---

## Memory Blocks

```c
#include <zephyr/sys/mem_blocks.h>

// Static definition
SYS_MEM_BLOCKS_DEFINE(name, block_size, num_blocks, align)
SYS_MEM_BLOCKS_DEFINE_STATIC(name, block_size, num_blocks, align)
SYS_MEM_BLOCKS_DEFINE_WITH_EXT_BUF(name, block_size, num_blocks, buffer)

// Allocation
int sys_mem_blocks_alloc(sys_mem_blocks_t *mem_block, size_t count,
                          void **out_blocks);
int sys_mem_blocks_alloc_contiguous(sys_mem_blocks_t *mem_block, size_t count,
                                     void **out_block);

// Deallocation
int sys_mem_blocks_free(sys_mem_blocks_t *mem_block, size_t count,
                         void **in_blocks);
int sys_mem_blocks_free_contiguous(sys_mem_blocks_t *mem_block, void *block,
                                    size_t count);

// Multi-block group
void sys_multi_mem_blocks_init(struct sys_multi_mem_blocks *group,
                                sys_multi_mem_blocks_choice_fn_t choice_fn);
void sys_multi_mem_blocks_add_allocator(struct sys_multi_mem_blocks *group,
                                         sys_mem_blocks_t *alloc);
int sys_multi_mem_blocks_alloc(struct sys_multi_mem_blocks *group, void *cfg,
                                size_t count, void **out_blocks, size_t *blk_size);
int sys_multi_mem_blocks_free(struct sys_multi_mem_blocks *group, size_t count,
                               void **in_blocks);
```

---

## Memory Domains

```c
#include <zephyr/kernel.h>
#include <zephyr/app_memory/app_memdomain.h>

// Partition definition
K_MEM_PARTITION_DEFINE(name, start, size, attr)
K_APPMEM_PARTITION_DEFINE(name)

// Variable routing
K_APP_DMEM(partition) type var = init;  // Initialized data
K_APP_BMEM(partition) type var;          // BSS (zeroed)

// Domain management
int k_mem_domain_init(struct k_mem_domain *domain, uint8_t num_parts,
                       struct k_mem_partition *parts[]);
int k_mem_domain_add_partition(struct k_mem_domain *domain,
                                struct k_mem_partition *part);
int k_mem_domain_remove_partition(struct k_mem_domain *domain,
                                   struct k_mem_partition *part);
int k_mem_domain_add_thread(struct k_mem_domain *domain, k_tid_t thread);

// Thread resource pool
void k_thread_heap_assign(struct k_thread *thread, struct k_heap *heap);
void k_thread_system_pool_assign(struct k_thread *thread);
```

---

## Virtual Memory

```c
#include <zephyr/kernel.h>

// Memory mapping
void *k_mem_map(size_t size, uint32_t flags);
void k_mem_unmap(void *addr, size_t size);
void *k_mem_map_phys_bare(uint8_t *phys, size_t size, uint32_t flags);

// Demand paging
void k_mem_page_in(void *addr, size_t size);
void k_mem_page_out(void *addr, size_t size);
void k_mem_pin(void *addr, size_t size);
void k_mem_unpin(void *addr, size_t size);

// Statistics
void k_mem_paging_stats_get(struct k_mem_paging_stats *stats);
void k_mem_paging_thread_stats_get(k_tid_t thread,
                                    struct k_mem_paging_stats *stats);
```

---

## Kconfig Options

### System Heap

| Option | Description | Default |
|--------|-------------|---------|
| `CONFIG_HEAP_MEM_POOL_SIZE` | System heap size (0 disables) | 0 |
| `CONFIG_HEAP_MEM_POOL_IGNORE_MIN` | Ignore minimum size requirements | n |

### Memory Slabs

| Option | Description | Default |
|--------|-------------|---------|
| `CONFIG_MEM_SLAB_TRACE_MAX_UTILIZATION` | Track peak usage | n |

### Heap Debugging

| Option | Description | Default |
|--------|-------------|---------|
| `CONFIG_HEAP_LISTENER` | Enable heap allocation callbacks | n |
| `CONFIG_SYS_HEAP_RUNTIME_STATS` | Enable runtime statistics | n |
| `CONFIG_SYS_HEAP_ALLOC_LOOPS` | Allocation search iterations | 3 |

### Userspace & Memory Protection

| Option | Description | Default |
|--------|-------------|---------|
| `CONFIG_USERSPACE` | Enable userspace support | n |
| `CONFIG_MAX_DOMAIN_PARTITIONS` | Max partitions per domain | 8 |
| `CONFIG_MEM_DOMAIN_ISOLATED_STACKS` | Isolate stacks between threads | y (if supported) |
| `CONFIG_HW_STACK_PROTECTION` | Hardware stack overflow detection | n |

### Virtual Memory

| Option | Description | Default |
|--------|-------------|---------|
| `CONFIG_MMU` | Enable MMU support | n |
| `CONFIG_MMU_PAGE_SIZE` | Page size in bytes | 4096 |
| `CONFIG_KERNEL_VM_BASE` | Virtual address space base | arch-specific |
| `CONFIG_KERNEL_VM_SIZE` | Virtual address space size | 8MB |
| `CONFIG_KERNEL_DIRECT_MAP` | Allow 1:1 physical mappings | n |

### Demand Paging

| Option | Description | Default |
|--------|-------------|---------|
| `CONFIG_DEMAND_PAGING` | Enable demand paging | n |
| `CONFIG_DEMAND_PAGING_ALLOW_IRQ` | Allow page faults in ISR | n |
| `CONFIG_DEMAND_PAGING_EVICTION_NRU` | NRU eviction algorithm | n |
| `CONFIG_DEMAND_PAGING_EVICTION_LRU` | LRU eviction algorithm | n |
| `CONFIG_DEMAND_PAGING_THREAD_STATS` | Per-thread paging stats | n |

### Memory Attributes

| Option | Description | Default |
|--------|-------------|---------|
| `CONFIG_MEM_ATTR` | Enable memory attributes helper | n |
| `CONFIG_MEM_ATTR_HEAP` | Enable attribute-based heaps | n |

---

## Header Locations

| API | Header |
|-----|--------|
| k_heap, k_malloc, k_mem_slab | `<zephyr/kernel.h>` |
| sys_heap | `<zephyr/sys/sys_heap.h>` |
| sys_multi_heap | `<zephyr/sys/multi_heap.h>` |
| sys_mem_blocks | `<zephyr/sys/mem_blocks.h>` |
| heap_listener | `<zephyr/sys/heap_listener.h>` |
| k_mem_domain | `<zephyr/kernel.h>` |
| K_APP_DMEM, K_APPMEM_PARTITION_DEFINE | `<zephyr/app_memory/app_memdomain.h>` |
| partitions (z_libc_partition, etc.) | `<zephyr/app_memory/partitions.h>` |
| mem_attr_heap | `<zephyr/mem_mgmt/mem_attr_heap.h>` |
| shared_multi_heap | `<zephyr/multi_heap/shared_multi_heap.h>` |
