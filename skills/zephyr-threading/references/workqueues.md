# Workqueues

## Table of Contents
- [Overview](#overview)
- [System Workqueue](#system-workqueue)
- [Custom Workqueues](#custom-workqueues)
- [Work Items](#work-items)
- [Delayable Work](#delayable-work)
- [Triggered Work](#triggered-work)
- [Best Practices](#best-practices)

## Overview

A **workqueue** is a kernel object with a dedicated thread that processes **work items** in FIFO order. Use workqueues to:

- Offload non-urgent processing from ISRs
- Defer work from high-priority threads
- Avoid creating many single-purpose threads

### When to Use Workqueues vs Threads

| Scenario | Use |
| :--- | :--- |
| Deferred ISR processing | Workqueue |
| Multiple independent short tasks | Workqueue |
| Long-running continuous processing | Dedicated thread |
| Task needs specific priority | Dedicated thread or custom workqueue |
| Many similar background tasks | Workqueue |

## System Workqueue

Zephyr provides a built-in workqueue for general use. Prefer this over creating custom workqueues.

### Configuration

```
CONFIG_SYSTEM_WORKQUEUE_STACK_SIZE=1024
CONFIG_SYSTEM_WORKQUEUE_PRIORITY=10
CONFIG_SYSTEM_WORKQUEUE_NO_YIELD=n  # yield between items (default)
```

### Basic Usage

```c
#include <zephyr/kernel.h>

void my_work_handler(struct k_work *work)
{
    /* Deferred processing here */
    printk("Work item executed\n");
}

/* Static work item definition */
K_WORK_DEFINE(my_work, my_work_handler);

/* Submit from ISR or thread */
void some_event(void)
{
    k_work_submit(&my_work);  /* submits to system workqueue */
}
```

### Passing Context to Handler

Use `CONTAINER_OF` to access enclosing structure:

```c
struct my_context {
    struct k_work work;
    int value;
    char data[32];
};

void context_handler(struct k_work *work)
{
    struct my_context *ctx = CONTAINER_OF(work, struct my_context, work);
    /* Access ctx->value, ctx->data */
}

struct my_context ctx;

void init_context(void)
{
    k_work_init(&ctx.work, context_handler);
    ctx.value = 42;
}
```

## Custom Workqueues

Create custom workqueues when:
- System workqueue priority doesn't fit
- Work items might block and stall other system work
- Need isolated processing

```c
#define MY_WQ_STACK_SIZE 1024
#define MY_WQ_PRIORITY 5

K_THREAD_STACK_DEFINE(my_wq_stack, MY_WQ_STACK_SIZE);
struct k_work_q my_work_q;

void init_my_workqueue(void)
{
    k_work_queue_init(&my_work_q);
    k_work_queue_start(&my_work_q, my_wq_stack,
                       K_THREAD_STACK_SIZEOF(my_wq_stack),
                       MY_WQ_PRIORITY, NULL);
}

/* Submit to custom workqueue */
void submit_work(void)
{
    k_work_submit_to_queue(&my_work_q, &my_work);
}
```

### Workqueue Control

```c
/* Drain queue (block until empty) */
k_work_queue_drain(&my_work_q, false);  /* false = allow new submissions after */

/* Drain and plug (block new submissions) */
k_work_queue_drain(&my_work_q, true);

/* Unplug (allow submissions again) */
k_work_queue_unplug(&my_work_q);
```

## Work Items

### Work Item States

| State | Meaning |
| :--- | :--- |
| `K_WORK_QUEUED` | Waiting in queue to be processed |
| `K_WORK_RUNNING` | Currently executing on workqueue thread |
| `K_WORK_CANCELING` | Cancel requested, still running |
| `K_WORK_DELAYED` | Scheduled for future submission (delayable) |

### Checking Work Status

```c
/* Get busy state bitmask */
int busy = k_work_busy_get(&my_work);
if (busy & K_WORK_RUNNING) {
    /* Handler is executing */
}

/* Check if pending (queued, scheduled, or running) */
bool pending = k_work_is_pending(&my_work);
```

### Cancelling Work

```c
/* Non-blocking cancel attempt */
int ret = k_work_cancel(&my_work);
/* Returns: 0=cancelled, -EALREADY=not pending, -EBUSY=running */

/* Blocking cancel (wait until complete) - thread context only */
struct k_work_sync sync;
bool was_pending = k_work_cancel_sync(&my_work, &sync);
/* Returns true if work was pending and is now complete */
```

### Flushing Work

```c
/* Block until specific work item completes */
struct k_work_sync sync;
bool was_pending = k_work_flush(&my_work, &sync);
```

### Resubmitting Work

A work item can be resubmitted from its handler:

```c
void periodic_handler(struct k_work *work)
{
    /* Do processing */

    /* Resubmit for continuous operation */
    k_work_submit(work);  /* Safe: item is no longer queued at this point */
}
```

**Important**: Never modify a pending work item (including reinitialization).

## Delayable Work

Schedule work to execute after a delay.

### Definition and Scheduling

```c
void delayed_handler(struct k_work *work)
{
    /* Get delayable container */
    struct k_work_delayable *dwork = k_work_delayable_from_work(work);

    /* Or if embedded in struct */
    struct my_struct *ctx = CONTAINER_OF(dwork, struct my_struct, dwork);
}

K_WORK_DELAYABLE_DEFINE(my_delayed_work, delayed_handler);

void schedule_delayed(void)
{
    /* Schedule 500ms from now */
    k_work_schedule(&my_delayed_work, K_MSEC(500));
}
```

### Schedule vs Reschedule

| Function | Behavior if Already Scheduled |
| :--- | :--- |
| `k_work_schedule()` | No change (keeps original deadline) |
| `k_work_reschedule()` | Replaces deadline with new one |

```c
/* First unprocessed data → schedule */
k_work_schedule(&dwork, K_MSEC(100));  /* runs in 100ms */

/* More data arrives before deadline */
k_work_schedule(&dwork, K_MSEC(100));  /* still runs at original time */

/* Use reschedule to extend deadline on each new data */
k_work_reschedule(&dwork, K_MSEC(100));  /* resets to 100ms from now */
```

### Immediate Submission

```c
/* Submit immediately (bypass delay) */
k_work_schedule(&dwork, K_NO_WAIT);
k_work_reschedule(&dwork, K_NO_WAIT);
```

### Delayable Work Status

```c
/* Get remaining time until scheduled submission */
k_ticks_t remaining = k_work_delayable_remaining_get(&dwork);

/* Check if pending (delayed, queued, or running) */
bool pending = k_work_delayable_is_pending(&dwork);

/* Cancel delayable work */
k_work_cancel_delayable(&dwork);          /* non-blocking */
k_work_cancel_delayable_sync(&dwork, &sync);  /* blocking */
```

## Triggered Work

Submit work when poll events occur (alternative to dedicated polling thread).

```c
void triggered_handler(struct k_work *work)
{
    struct k_work_poll *pwork = CONTAINER_OF(work, struct k_work_poll, work);
    /* Process triggered event */
}

struct k_work_poll triggered_work;
struct k_poll_event events[1];

void setup_triggered(void)
{
    k_work_poll_init(&triggered_work, triggered_handler);

    /* Watch a semaphore */
    k_poll_event_init(&events[0], K_POLL_TYPE_SEM_AVAILABLE,
                      K_POLL_MODE_NOTIFY_ONLY, &my_sem);

    /* Submit - will execute when semaphore available */
    k_work_poll_submit(&triggered_work, events, 1, K_FOREVER);
}
```

## Best Practices

### Avoid Race Conditions

Work handlers share state with threads/ISRs. Use synchronization:

```c
/* BAD: race condition */
void handler(struct k_work *work)
{
    shared_data++;  /* not atomic! */
}

/* GOOD: use atomics for simple flags */
atomic_t shared_counter = ATOMIC_INIT(0);
void handler(struct k_work *work)
{
    atomic_inc(&shared_counter);
}

/* GOOD: use mutex for complex data (but don't block forever!) */
void handler(struct k_work *work)
{
    if (k_mutex_lock(&data_mutex, K_MSEC(100)) == 0) {
        /* modify shared data */
        k_mutex_unlock(&data_mutex);
    } else {
        /* Could not get lock, reschedule */
        k_work_submit(work);
    }
}
```

### Don't Block Forever

A blocking handler stalls all subsequent work items:

```c
/* BAD: blocks entire workqueue */
void handler(struct k_work *work)
{
    k_sem_take(&some_sem, K_FOREVER);  /* may wait indefinitely */
}

/* GOOD: non-blocking with resubmit */
void handler(struct k_work *work)
{
    if (k_sem_take(&some_sem, K_NO_WAIT) != 0) {
        /* Sem not available, try again later */
        k_work_schedule(k_work_delayable_from_work(work), K_MSEC(10));
        return;
    }
    /* Process with semaphore held */
    k_sem_give(&some_sem);
}
```

### Check Return Values

```c
/* INCOMPLETE: ignoring return value */
k_work_submit(&work);

/* PROPER: check for failure */
int ret = k_work_submit(&work);
if (ret < 0) {
    if (ret == -EBUSY) {
        /* Work is being cancelled */
    } else if (ret == -EINVAL) {
        /* Queue not accepting work (plugged) */
    }
    /* Handle failure appropriately */
}
```

### Handler Self-Protection

Always verify conditions in handler, don't trust submission state:

```c
struct device_ctx {
    struct k_work_delayable retry_work;
    bool shutdown;
};

void retry_handler(struct k_work *work)
{
    struct k_work_delayable *dwork = k_work_delayable_from_work(work);
    struct device_ctx *ctx = CONTAINER_OF(dwork, struct device_ctx, retry_work);

    /* Check if we should actually do anything */
    if (ctx->shutdown) {
        return;  /* Device shutting down, don't retry */
    }

    /* Do actual work */
}

void shutdown_device(struct device_ctx *ctx)
{
    ctx->shutdown = true;
    /* Cancel may fail if handler running, but handler will check flag */
    (void)k_work_cancel_delayable(&ctx->retry_work);
}
```

### System Workqueue Guidelines

| Do | Don't |
| :--- | :--- |
| Keep handlers short | Block indefinitely |
| Use K_NO_WAIT for locks | Call k_sleep() in handler |
| Check return values | Assume submission succeeded |
| Use delayable for retries | Busy-loop in handler |

### When to Create Custom Workqueue

- Work items may block for extended periods
- Need different priority than system workqueue
- Processing must be isolated from other work
- Need to drain/plug for shutdown sequence
