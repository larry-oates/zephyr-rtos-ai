# API Reference

## Table of Contents
- [Thread Creation & Control](#thread-creation--control)
- [Thread Information](#thread-information)
- [Scheduling Control](#scheduling-control)
- [Stack Management](#stack-management)
- [Workqueue API](#workqueue-api)
- [Kconfig Options](#kconfig-options)
- [Header Files](#header-files)

## Thread Creation & Control

### k_thread_create

```c
k_tid_t k_thread_create(struct k_thread *new_thread,
                        k_thread_stack_t *stack,
                        size_t stack_size,
                        k_thread_entry_t entry,
                        void *p1, void *p2, void *p3,
                        int prio,
                        uint32_t options,
                        k_timeout_t delay);
```

| Parameter | Description |
| :--- | :--- |
| `new_thread` | Uninitialized `struct k_thread` |
| `stack` | Stack area from `K_THREAD_STACK_DEFINE` |
| `stack_size` | Stack size via `K_THREAD_STACK_SIZEOF()` |
| `entry` | Entry point function `void entry(void*, void*, void*)` |
| `p1, p2, p3` | Arguments passed to entry function |
| `prio` | Thread priority (negative=cooperative, non-negative=preemptive) |
| `options` | Bitwise OR of `K_ESSENTIAL`, `K_FP_REGS`, `K_USER`, etc. |
| `delay` | Start delay (`K_NO_WAIT`, `K_FOREVER`, or `K_MSEC(n)`) |

**Returns**: `k_tid_t` thread ID

### K_THREAD_DEFINE

```c
K_THREAD_DEFINE(name, stack_size, entry, p1, p2, p3, prio, options, delay);
```

Statically defines thread, stack, and control block at compile time.

| Parameter | Description |
| :--- | :--- |
| `name` | Thread identifier (creates `k_tid_t name`) |
| `stack_size` | Stack size in bytes |
| `entry` | Entry point function |
| `p1, p2, p3` | Entry function arguments |
| `prio` | Priority |
| `options` | Thread options |
| `delay` | Start delay in **milliseconds** (integer, not `k_timeout_t`) |

### Thread Lifecycle

```c
void k_thread_start(k_tid_t thread);           /* Start delayed thread */
void k_thread_abort(k_tid_t thread);           /* Abort thread */
int k_thread_join(k_tid_t thread, k_timeout_t timeout);  /* Wait for termination */
void k_thread_suspend(k_tid_t thread);         /* Suspend thread */
void k_thread_resume(k_tid_t thread);          /* Resume suspended thread */
```

**k_thread_join returns**:
- `0`: Thread terminated
- `-EAGAIN`: Timeout expired
- `-EBUSY`: Thread is essential or unjoinable
- `-EDEADLK`: Thread trying to join itself

## Thread Information

```c
k_tid_t k_current_get(void);                           /* Get current thread ID */
const char *k_thread_name_get(k_tid_t thread);         /* Get thread name */
int k_thread_name_set(k_tid_t thread, const char *name); /* Set thread name */
int k_thread_name_copy(k_tid_t thread, char *buf, size_t size); /* Copy name to buffer */
```

### Custom Data

```c
void k_thread_custom_data_set(void *value);    /* Set current thread's custom data */
void *k_thread_custom_data_get(void);          /* Get current thread's custom data */
```

Requires `CONFIG_THREAD_CUSTOM_DATA=y`.

### Runtime Statistics

```c
int k_thread_runtime_stats_get(k_tid_t thread, k_thread_runtime_stats_t *stats);
int k_thread_runtime_stats_all_get(k_thread_runtime_stats_t *stats);
```

Requires `CONFIG_THREAD_RUNTIME_STATS=y`.

## Scheduling Control

### Sleep & Wait

```c
int32_t k_sleep(k_timeout_t timeout);   /* Sleep, returns remaining time if woken */
int32_t k_msleep(int32_t ms);           /* Sleep milliseconds */
int32_t k_usleep(int32_t us);           /* Sleep microseconds */
void k_wakeup(k_tid_t thread);          /* Wake sleeping thread early */
void k_busy_wait(uint32_t usec_to_wait); /* Busy wait (no yield) */
void k_yield(void);                      /* Yield to equal/higher priority */
```

### Priority

```c
void k_thread_priority_set(k_tid_t thread, int prio);  /* Set priority */
int k_thread_priority_get(k_tid_t thread);             /* Get priority */
```

### Priority Macros

```c
K_PRIO_COOP(x)     /* Cooperative priority (0=highest coop) */
K_PRIO_PREEMPT(x)  /* Preemptive priority (0=highest preempt) */
K_HIGHEST_THREAD_PRIO   /* Highest possible priority */
K_LOWEST_THREAD_PRIO    /* Lowest possible priority (idle) */
```

### Scheduler Lock

```c
void k_sched_lock(void);    /* Prevent preemption */
void k_sched_unlock(void);  /* Re-enable preemption */
```

### Time Slicing

```c
void k_thread_time_slice_set(struct k_thread *th,
                             int32_t slice_ticks,
                             void (*expired)(struct k_thread *th, void *data),
                             void *data);
```

### SMP / CPU Affinity

```c
int k_thread_cpu_pin(k_tid_t thread, int cpu);         /* Pin to specific CPU */
int k_thread_cpu_mask_clear(k_tid_t thread);           /* Clear CPU mask */
int k_thread_cpu_mask_enable_all(k_tid_t thread);      /* Enable all CPUs */
int k_thread_cpu_mask_enable(k_tid_t thread, int cpu); /* Enable specific CPU */
int k_thread_cpu_mask_disable(k_tid_t thread, int cpu);/* Disable specific CPU */
```

## Stack Management

### Stack Definition Macros

```c
/* User-mode capable stack */
K_THREAD_STACK_DEFINE(name, size);
K_THREAD_STACK_ARRAY_DEFINE(name, num_stacks, size);
K_THREAD_STACK_SIZEOF(sym);  /* Get usable size */

/* Kernel-only stack (smaller footprint) */
K_KERNEL_STACK_DEFINE(name, size);
K_KERNEL_STACK_ARRAY_DEFINE(name, num_stacks, size);
K_KERNEL_STACK_SIZEOF(sym);  /* Get usable size */
```

### Dynamic Stack Allocation

```c
k_thread_stack_t *k_thread_stack_alloc(size_t size);
int k_thread_stack_free(k_thread_stack_t *stack);
```

Requires `CONFIG_DYNAMIC_THREAD=y`.

## Workqueue API

### Work Items

```c
/* Definition */
K_WORK_DEFINE(name, handler);
void k_work_init(struct k_work *work, k_work_handler_t handler);

/* Submission */
int k_work_submit(struct k_work *work);                    /* System workqueue */
int k_work_submit_to_queue(struct k_work_q *queue, struct k_work *work);

/* Status */
int k_work_busy_get(const struct k_work *work);            /* Get busy state flags */
bool k_work_is_pending(const struct k_work *work);         /* Check if pending */

/* Cancellation */
int k_work_cancel(struct k_work *work);                    /* Non-blocking cancel */
bool k_work_cancel_sync(struct k_work *work, struct k_work_sync *sync);

/* Synchronization */
bool k_work_flush(struct k_work *work, struct k_work_sync *sync);
```

### Delayable Work

```c
/* Definition */
K_WORK_DELAYABLE_DEFINE(name, handler);
void k_work_init_delayable(struct k_work_delayable *dwork, k_work_handler_t handler);

/* Scheduling */
int k_work_schedule(struct k_work_delayable *dwork, k_timeout_t delay);
int k_work_schedule_for_queue(struct k_work_q *queue,
                               struct k_work_delayable *dwork,
                               k_timeout_t delay);
int k_work_reschedule(struct k_work_delayable *dwork, k_timeout_t delay);
int k_work_reschedule_for_queue(struct k_work_q *queue,
                                 struct k_work_delayable *dwork,
                                 k_timeout_t delay);

/* Utilities */
struct k_work_delayable *k_work_delayable_from_work(struct k_work *work);
k_ticks_t k_work_delayable_remaining_get(const struct k_work_delayable *dwork);
bool k_work_delayable_is_pending(const struct k_work_delayable *dwork);

/* Cancellation */
int k_work_cancel_delayable(struct k_work_delayable *dwork);
bool k_work_cancel_delayable_sync(struct k_work_delayable *dwork,
                                   struct k_work_sync *sync);
```

### Custom Workqueue

```c
void k_work_queue_init(struct k_work_q *queue);
void k_work_queue_start(struct k_work_q *queue,
                        k_thread_stack_t *stack,
                        size_t stack_size,
                        int prio,
                        const struct k_work_queue_config *cfg);

int k_work_queue_drain(struct k_work_q *queue, bool plug);
int k_work_queue_unplug(struct k_work_q *queue);
```

### Triggered Work

```c
void k_work_poll_init(struct k_work_poll *work, k_work_handler_t handler);
int k_work_poll_submit(struct k_work_poll *work,
                       struct k_poll_event *events,
                       int num_events,
                       k_timeout_t timeout);
int k_work_poll_submit_to_queue(struct k_work_q *queue,
                                struct k_work_poll *work,
                                struct k_poll_event *events,
                                int num_events,
                                k_timeout_t timeout);
int k_work_poll_cancel(struct k_work_poll *work);
```

## Kconfig Options

### Thread Configuration

| Option | Description | Default |
| :--- | :--- | :--- |
| `CONFIG_NUM_COOP_PRIORITIES` | Number of cooperative priorities | 16 |
| `CONFIG_NUM_PREEMPT_PRIORITIES` | Number of preemptive priorities | 15 |
| `CONFIG_NUM_METAIRQ_PRIORITIES` | Meta-IRQ priority levels | 0 |
| `CONFIG_MAIN_THREAD_PRIORITY` | Main thread priority | 0 |
| `CONFIG_MAIN_STACK_SIZE` | Main thread stack size | 1024 |
| `CONFIG_IDLE_STACK_SIZE` | Idle thread stack size | 256 |

### Time Slicing

| Option | Description | Default |
| :--- | :--- | :--- |
| `CONFIG_TIMESLICING` | Enable time slicing | y |
| `CONFIG_TIMESLICE_SIZE` | Time slice duration (ms) | 0 |
| `CONFIG_TIMESLICE_PRIORITY` | Priority threshold for slicing | 0 |

### Scheduler Implementation

| Option | Description |
| :--- | :--- |
| `CONFIG_SCHED_SIMPLE` | Simple linked list (few threads) |
| `CONFIG_SCHED_MULTIQ` | Multi-queue (default) |
| `CONFIG_SCHED_SCALABLE` | Red-black tree (many threads) |
| `CONFIG_WAITQ_SIMPLE` | Simple linked list wait queues |
| `CONFIG_WAITQ_SCALABLE` | Scalable wait queues |

### Thread Features

| Option | Description | Default |
| :--- | :--- | :--- |
| `CONFIG_THREAD_CUSTOM_DATA` | Per-thread custom data | n |
| `CONFIG_THREAD_MONITOR` | Thread list tracking | n |
| `CONFIG_THREAD_NAME` | Thread naming | n |
| `CONFIG_THREAD_STACK_INFO` | Stack usage tracking | n |
| `CONFIG_THREAD_RUNTIME_STATS` | Runtime statistics | n |
| `CONFIG_THREAD_ANALYZER` | Thread analysis tool | n |
| `CONFIG_USERSPACE` | User mode support | n |

### Workqueue Configuration

| Option | Description | Default |
| :--- | :--- | :--- |
| `CONFIG_SYSTEM_WORKQUEUE_STACK_SIZE` | System workqueue stack | 1024 |
| `CONFIG_SYSTEM_WORKQUEUE_PRIORITY` | System workqueue priority | -1 (coop) |
| `CONFIG_SYSTEM_WORKQUEUE_NO_YIELD` | Disable yield between items | n |

### Dynamic Threads

| Option | Description | Default |
| :--- | :--- | :--- |
| `CONFIG_DYNAMIC_THREAD` | Enable dynamic thread creation | n |
| `CONFIG_DYNAMIC_THREAD_STACK_SIZE` | Default dynamic stack size | 1024 |
| `CONFIG_DYNAMIC_THREAD_ALLOC` | Stack allocation method | n |

### SMP

| Option | Description |
| :--- | :--- |
| `CONFIG_SMP` | Symmetric multiprocessing |
| `CONFIG_MP_NUM_CPUS` | Number of CPUs |
| `CONFIG_SCHED_CPU_MASK` | Per-thread CPU affinity |

## Header Files

```c
#include <zephyr/kernel.h>           /* All thread/workqueue APIs */
#include <zephyr/sys/atomic.h>       /* Atomic operations */
#include <zephyr/debug/thread_analyzer.h>  /* Thread analyzer */
```

## Common Type Definitions

```c
typedef struct k_thread *k_tid_t;    /* Thread ID */
typedef void (*k_thread_entry_t)(void *p1, void *p2, void *p3);  /* Entry function */
typedef void (*k_work_handler_t)(struct k_work *work);  /* Work handler */
```

## Timeout Values

```c
K_NO_WAIT      /* Don't wait, return immediately */
K_FOREVER      /* Wait indefinitely */
K_MSEC(ms)     /* Milliseconds */
K_USEC(us)     /* Microseconds */
K_SECONDS(s)   /* Seconds */
K_MINUTES(m)   /* Minutes */
K_HOURS(h)     /* Hours */
K_TICKS(t)     /* Raw tick count */
```

## Work Item State Flags

```c
K_WORK_QUEUED     /* In workqueue, waiting to run */
K_WORK_RUNNING    /* Currently executing */
K_WORK_CANCELING  /* Cancel requested while running */
K_WORK_DELAYED    /* Scheduled for future submission */
```

## Thread Options

```c
K_ESSENTIAL       /* Abort triggers system error */
K_FP_REGS         /* Uses floating point */
K_SSE_REGS        /* Uses SSE (x86) */
K_USER            /* User mode thread */
K_INHERIT_PERMS   /* Inherit parent permissions */
```
