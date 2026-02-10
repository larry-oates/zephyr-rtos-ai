# Memory Allocator Comparison

## Decision Matrix

| Feature | k_heap | k_malloc | k_mem_slab | sys_mem_blocks | Memory Domain |
|---------|--------|----------|------------|----------------|---------------|
| **Block Size** | Variable | Variable | Fixed | Fixed | N/A (protection) |
| **Fragmentation** | Possible | Possible | None | None | N/A |
| **Allocation Time** | O(1) | O(1) | O(1) | O(n) blocks | N/A |
| **ISR Safe (K_NO_WAIT)** | Yes | No | Yes | Yes | N/A |
| **Blocking Wait** | Yes | No | Yes | No | N/A |
| **Multiple Instances** | Yes | No (single) | Yes | Yes | Yes |
| **External Bookkeeping** | No | No | No | Yes | N/A |
| **Synchronized** | Yes | Yes | Yes | No | N/A |
| **Best For** | General dynamic | Simple malloc | Protocol buffers | DMA scatter-gather | Userspace isolation |

## Decision Flowchart

```
Need memory allocation?
│
├─ Fixed-size blocks?
│   ├─ Yes → Need external bookkeeping (power-down memory)?
│   │         ├─ Yes → sys_mem_blocks
│   │         └─ No  → k_mem_slab
│   │
│   └─ No → Variable-size blocks
│           ├─ Need multiple separate heaps? → k_heap
│           └─ Single global heap sufficient? → k_malloc/k_free
│
├─ Memory protection needed?
│   └─ Yes → Memory Domains + Partitions (see domains.md)
│
└─ MMU available & virtual memory needed?
    └─ Yes → k_mem_map / Demand Paging (see virtual.md)
```

## When to Use Each

### k_heap (Recommended Default)
- General-purpose dynamic allocation
- Variable-size allocations
- Need blocking with timeout
- Multiple isolated heaps for different subsystems

### k_malloc / k_free
- Simple malloc-like interface
- Single system-wide heap is acceptable
- Cannot wait for memory (returns NULL immediately if unavailable)

### k_mem_slab
- Fixed-size allocations (network packets, sensor samples)
- Zero fragmentation guarantee
- High-frequency alloc/free cycles
- Need blocking wait for available blocks

### sys_mem_blocks
- Fixed-size block allocation
- Need to allocate multiple blocks atomically
- External bookkeeping (buffer can be in power-down region)
- DMA scatter-gather operations with non-contiguous blocks

### Memory Domains
- Userspace thread isolation
- MPU/MMU-based memory protection
- Shared memory between specific thread groups

## Common Patterns

### Pattern: Per-Subsystem Heaps
Avoid one large system heap. Create dedicated heaps:

```c
K_HEAP_DEFINE(network_heap, 4096);
K_HEAP_DEFINE(sensor_heap, 2048);

// Allocate from specific heap
void *pkt = k_heap_alloc(&network_heap, 256, K_NO_WAIT);
```

### Pattern: Message Buffer Pool
Use slabs for fixed-size message buffers:

```c
K_MEM_SLAB_DEFINE(msg_pool, sizeof(struct msg), 10, 4);

struct msg *m;
k_mem_slab_alloc(&msg_pool, (void **)&m, K_FOREVER);
// Use message
k_mem_slab_free(&msg_pool, m);
```

### Pattern: DMA Buffer Allocation
Use attribute heaps for DMA-capable memory:

```c
// Allocate from DMA-capable region (requires devicetree setup)
void *dma_buf = mem_attr_heap_alloc(DT_MEM_SW_ALLOC_DMA, 512);
```
