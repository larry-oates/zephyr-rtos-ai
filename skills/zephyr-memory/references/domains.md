# Memory Domains

## Overview

Memory domains provide memory protection for userspace threads using MPU or MMU hardware:
- Group memory partitions accessible to threads
- Isolate threads from each other and kernel
- Share specific memory regions between thread groups

Requires: `CONFIG_USERSPACE=y`

## Concepts

### Memory Partition
A contiguous memory region with defined access attributes (read, write, execute).

### Memory Domain
A collection of memory partitions. Threads in the same domain share access to those partitions.

### Default Behavior
- All threads start in `k_mem_domain_default`
- Threads always have access to their own stack
- Kernel memory is never accessible from userspace

## Partition Definition

### Manual Partition

```c
uint8_t __aligned(32) my_buffer[1024];

K_MEM_PARTITION_DEFINE(my_partition, my_buffer, sizeof(my_buffer),
                        K_MEM_PARTITION_P_RW_U_RW);
```

### Automatic Partition (Build System)

```c
#include <zephyr/app_memory/app_memdomain.h>

// Declare partition (no base/size—computed by linker)
K_APPMEM_PARTITION_DEFINE(app_partition);

// Route variables to partition
K_APP_DMEM(app_partition) int initialized_var = 42;
K_APP_BMEM(app_partition) int bss_var;  // zeroed at boot
```

## Domain Creation

```c
struct k_mem_domain my_domain;

// Empty domain
k_mem_domain_init(&my_domain, 0, NULL);

// Domain with initial partitions
struct k_mem_partition *parts[] = { &part1, &part2 };
k_mem_domain_init(&my_domain, ARRAY_SIZE(parts), parts);
```

## Managing Partitions

```c
// Add partition to domain
k_mem_domain_add_partition(&my_domain, &my_partition);

// Remove partition from domain
k_mem_domain_remove_partition(&my_domain, &my_partition);
```

## Thread Assignment

```c
// Assign thread to domain
k_mem_domain_add_thread(&my_domain, my_thread);

// Child threads inherit parent's domain
```

## Partition Attributes

Common attributes (architecture-specific availability):

```c
K_MEM_PARTITION_P_RW_U_RW   // Privileged RW, User RW (most common)
K_MEM_PARTITION_P_RW_U_RO   // Privileged RW, User RO
K_MEM_PARTITION_P_RW_U_NA   // Privileged RW, User No Access
K_MEM_PARTITION_P_RO_U_RO   // Both RO
```

## Pre-defined Partitions

```c
// C library globals (required for libc usage)
extern struct k_mem_partition z_libc_partition;

// System malloc pool
extern struct k_mem_partition z_malloc_partition;

// Include library-specific partitions
#include <zephyr/app_memory/partitions.h>
```

## Complete Example

```c
#include <zephyr/kernel.h>
#include <zephyr/app_memory/app_memdomain.h>

// Application memory partition
K_APPMEM_PARTITION_DEFINE(app_part);
K_APP_DMEM(app_part) struct app_data shared_data = {0};

// Shared buffer
uint8_t __aligned(32) shared_buf[256];
K_MEM_PARTITION_DEFINE(shared_part, shared_buf, sizeof(shared_buf),
                        K_MEM_PARTITION_P_RW_U_RW);

// Domain for worker threads
struct k_mem_domain worker_domain;

K_THREAD_STACK_DEFINE(worker_stack, 1024);
struct k_thread worker_thread;

void worker_entry(void *p1, void *p2, void *p3) {
    // Can access shared_buf and app_part variables
    shared_data.counter++;
}

void setup_workers(void) {
    // Create domain with partitions
    struct k_mem_partition *parts[] = { &app_part, &shared_part };
    k_mem_domain_init(&worker_domain, ARRAY_SIZE(parts), parts);

    // Create userspace thread
    k_thread_create(&worker_thread, worker_stack,
                    K_THREAD_STACK_SIZEOF(worker_stack),
                    worker_entry, NULL, NULL, NULL,
                    WORKER_PRIORITY, K_USER, K_NO_WAIT);

    // Assign to domain
    k_mem_domain_add_thread(&worker_domain, &worker_thread);
}
```

## Thread Resource Pools

Userspace threads need heap for some kernel operations:

```c
K_HEAP_DEFINE(worker_heap, 4096);

void setup_thread(void) {
    // Assign heap for kernel allocations on behalf of thread
    k_thread_heap_assign(&worker_thread, &worker_heap);

    // Or use system heap
    k_thread_system_pool_assign(&worker_thread);
}
```

## MPU/MMU Considerations

- Maximum partitions limited by MPU region count
- Partitions must meet alignment requirements (power of 2 on many MPUs)
- Overlapping partitions within a domain not allowed
- Same partition can exist in multiple domains

## Stack Isolation

By default, user threads can access stacks of other threads in same domain. For stricter isolation:

```kconfig
CONFIG_MEM_DOMAIN_ISOLATED_STACKS=y  # If supported by arch
```

## Kconfig

```kconfig
CONFIG_USERSPACE=y
CONFIG_MAX_DOMAIN_PARTITIONS=8  # Limit partitions per domain
```

## Common Pitfalls

1. **MPU region limit**: Too many partitions exceeds hardware capability.

2. **Alignment violations**: Partitions must meet MPU alignment requirements.

3. **Forgetting libc partition**: Userspace threads using libc need `z_libc_partition`.

4. **Kernel memory exposure**: Never put kernel data in user-accessible partitions.

5. **Missing resource pool**: Some syscalls need thread heap assignment.
