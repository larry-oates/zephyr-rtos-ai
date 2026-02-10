# Virtual Memory & Demand Paging

## Overview

Virtual memory in Zephyr provides:
- Address space isolation
- Fine-grained access control
- Memory-mapped regions
- Optional demand paging for memory overcommit

Requires: MMU hardware and `CONFIG_MMU=y`

## Virtual Memory Basics

### Key Concepts

- **Virtual Address**: Address used by software
- **Physical Address**: Actual RAM location
- **Page**: Smallest mappable unit (typically 4KB)
- **Page Table**: Maps virtual to physical addresses

### Default Mapping

By default, Zephyr uses 1:1 identity mapping:
- Virtual address == Physical address
- Simplifies embedded development
- Kernel image mapped at boot

## Memory Mapping

### Map Anonymous Memory

Allocate virtual memory backed by physical RAM:

```c
#include <zephyr/kernel.h>

// Map 4 pages of read-write memory
void *vaddr = k_mem_map(4 * CONFIG_MMU_PAGE_SIZE,
                         K_MEM_PERM_RW);

if (vaddr != NULL) {
    // Use memory
    memset(vaddr, 0, 4 * CONFIG_MMU_PAGE_SIZE);
}

// Unmap when done
k_mem_unmap(vaddr, 4 * CONFIG_MMU_PAGE_SIZE);
```

### Map Physical Address

Map specific physical memory (MMIO, shared memory):

```c
// Map device registers
void *regs = k_mem_map_phys_bare((uint8_t *)0x40000000,
                                  0x1000,
                                  K_MEM_PERM_RW | K_MEM_CACHE_NONE);
```

### Permission Flags

```c
K_MEM_PERM_RW     // Read-write
K_MEM_PERM_RO     // Read-only
K_MEM_PERM_EXEC   // Executable
K_MEM_PERM_USER   // User-mode accessible
K_MEM_CACHE_NONE  // Uncached (for MMIO)
K_MEM_CACHE_WB    // Write-back cache
K_MEM_CACHE_WT    // Write-through cache
```

## Kconfig

```kconfig
# Enable MMU support
CONFIG_MMU=y

# Page size (default 4096)
CONFIG_MMU_PAGE_SIZE=4096

# Virtual address space base
CONFIG_KERNEL_VM_BASE=0x80000000

# Virtual address space size
CONFIG_KERNEL_VM_SIZE=0x800000  # 8MB

# Allow direct physical mappings
CONFIG_KERNEL_DIRECT_MAP=y
```

## Demand Paging

Allows virtual memory larger than physical RAM by paging to backing store.

### Enable

```kconfig
CONFIG_DEMAND_PAGING=y
CONFIG_DEMAND_PAGING_ALLOW_IRQ=y  # Allow paging in ISR context
```

### Manual Page Control

```c
// Page in memory proactively
k_mem_page_in(addr, size);

// Page out memory (hint to free physical pages)
k_mem_page_out(addr, size);

// Pin memory (prevent paging out)
k_mem_pin(addr, size);

// Unpin memory
k_mem_unpin(addr, size);
```

### Statistics

```c
#include <zephyr/kernel.h>

struct k_mem_paging_stats stats;
k_mem_paging_stats_get(&stats);

printk("Page faults: %llu\n", stats.pagefaults);
printk("Pages evicted: %llu\n", stats.eviction);
```

### Eviction Algorithms

```kconfig
# NRU: Not-Recently-Used (simple)
CONFIG_DEMAND_PAGING_EVICTION_NRU=y

# LRU: Least-Recently-Used (recommended for production)
CONFIG_DEMAND_PAGING_EVICTION_LRU=y
```

### Backing Store

Storage for paged-out memory:

```kconfig
# RAM-based backing store (for testing)
CONFIG_BACKING_STORE_RAM=y
CONFIG_BACKING_STORE_RAM_PAGES=64
```

Custom backing store requires implementing:
- `k_mem_paging_backing_store_init()`
- `k_mem_paging_backing_store_page_in()`
- `k_mem_paging_backing_store_page_out()`

## Memory Map Layout

```
+--------------+ <- K_MEM_VIRT_RAM_START
| Reserved     |
+--------------+ <- K_MEM_KERNEL_VIRT_START
| Kernel Image |
| .text        |
| .rodata      |
| .data/.bss   |
+--------------+ <- K_MEM_VM_FREE_START
| Available    |
| Virtual      |
| Address      |
| Space        |
|..............| <- grows downward
| Mappings     |
+--------------+
| Reserved     |
+--------------+ <- K_MEM_VIRT_RAM_END
```

## Boot-Time Memory Regions

Set up in device tree or architecture code:

```dts
/ {
    sram0: memory@20000000 {
        compatible = "mmio-sram";
        reg = <0x20000000 0x40000>;
    };
};
```

## Section Permissions

At boot, Zephyr sets up:
- `.text`: Read-only, executable, user-accessible
- `.rodata`: Read-only, non-executable, user-accessible
- `.data`, `.bss`: Read-write, non-executable, kernel-only

## Practical Example: Large Buffer

```c
// Allocate large buffer that may exceed physical RAM
void *large_buf = k_mem_map(1024 * 1024,  // 1MB
                             K_MEM_PERM_RW);

if (large_buf == NULL) {
    LOG_ERR("Failed to map virtual memory");
    return -ENOMEM;
}

// Pin critical sections
k_mem_pin(large_buf, 4096);  // Keep first page always resident

// Use buffer - page faults will bring in pages as needed
process_data(large_buf);

// Unmap when done
k_mem_unmap(large_buf, 1024 * 1024);
```

## Common Pitfalls

1. **No MMU hardware**: Virtual memory requires MMU; most MCUs only have MPU.

2. **Page fault in ISR**: Default config disallows; enable `CONFIG_DEMAND_PAGING_ALLOW_IRQ` carefully.

3. **Backing store latency**: Page faults are slow; pin performance-critical memory.

4. **Memory overcommit**: Don't allocate more virtual memory than physical + backing store.

5. **Alignment**: All addresses and sizes must be page-aligned.
