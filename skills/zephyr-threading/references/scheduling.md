# Scheduling

## Table of Contents
- [Scheduling Algorithm](#scheduling-algorithm)
- [Priority Classes](#priority-classes)
- [Cooperative Behavior](#cooperative-behavior)
- [Preemptive Behavior](#preemptive-behavior)
- [Time Slicing](#time-slicing)
- [Scheduler Locking](#scheduler-locking)
- [Thread Sleeping](#thread-sleeping)
- [CPU Idling](#cpu-idling)

## Scheduling Algorithm

The kernel's scheduler selects the **highest priority ready thread** to run.

Key rules:
1. Lower numeric priority value = higher priority (priority -2 beats priority 5)
2. Among equal-priority threads, longest-waiting thread runs first
3. ISRs always preempt threads (unless interrupts are masked)
4. Cooperative threads run until they voluntarily yield
5. Preemptive threads can be preempted by higher/equal priority threads

### Reschedule Points

Scheduler evaluates which thread should run at:
- Thread transitions from running to suspended/waiting (e.g., `k_sem_take`, `k_sleep`)
- Thread transitions to ready (e.g., `k_sem_give`, `k_thread_start`)
- Return from ISR to thread context
- Thread calls `k_yield()`
- Time slice expires (if enabled)

## Priority Classes

### Priority Value Ranges

| Class | Priority Range | Preemptible By Scheduler |
| :--- | :--- | :--- |
| Meta-IRQ | -CONFIG_NUM_METAIRQ_PRIORITIES to -CONFIG_NUM_COOP_PRIORITIES-1 | Can preempt other threads |
| Cooperative | -CONFIG_NUM_COOP_PRIORITIES to -1 | No (must yield) |
| Preemptive | 0 to CONFIG_NUM_PREEMPT_PRIORITIES-1 | Yes |

Default configs: `CONFIG_NUM_COOP_PRIORITIES=16`, `CONFIG_NUM_PREEMPT_PRIORITIES=15`

### Priority Macros

```c
/* Cooperative priority: x=0 is highest, x=CONFIG_NUM_COOP_PRIORITIES-1 is lowest */
#define MY_COOP_PRIO K_PRIO_COOP(0)   /* highest cooperative */

/* Preemptive priority: x=0 is highest, x=CONFIG_NUM_PREEMPT_PRIORITIES-1 is lowest */
#define MY_PREEMPT_PRIO K_PRIO_PREEMPT(5)  /* mid-range preemptive */

/* Special values */
K_HIGHEST_THREAD_PRIO    /* most negative, highest priority possible */
K_LOWEST_THREAD_PRIO     /* CONFIG_NUM_PREEMPT_PRIORITIES, used by idle */
K_IDLE_PRIO              /* idle thread priority (lowest) */
```

### Choosing Priority Class

| Use Case | Recommended Class |
| :--- | :--- |
| Device drivers | Cooperative |
| Performance-critical code | Cooperative |
| Short atomic operations | Cooperative |
| General application threads | Preemptive |
| Time-sensitive processing | Higher preemptive |
| Background tasks | Lower preemptive |
| Interrupt bottom-half | Meta-IRQ (if needed) |

### Changing Priority at Runtime

```c
k_tid_t tid = k_current_get();

/* Set new priority */
k_thread_priority_set(tid, new_priority);

/* Get current priority */
int prio = k_thread_priority_get(tid);
```

Priority changes take effect immediately. A preemptive thread can become cooperative (and vice versa) by changing its priority.

## Cooperative Behavior

Cooperative threads (negative priority) have exclusive CPU use until they:
- Call `k_yield()`
- Call blocking API (`k_sleep`, `k_sem_take`, etc.)
- Return from entry function
- Are aborted

### Yielding

```c
void cooperative_thread(void *p1, void *p2, void *p3)
{
    while (1) {
        /* Do work */

        /* Option 1: Yield to equal/higher priority threads */
        k_yield();

        /* Option 2: Sleep (allows ALL threads to run) */
        k_msleep(10);
    }
}
```

**`k_yield()` vs `k_sleep()`**:
- `k_yield()`: Places thread at back of its priority queue, reschedules. If no equal/higher priority ready threads exist, calling thread continues immediately.
- `k_sleep()`: Makes thread unready for specified time. All threads (including lower priority) can run.

### Mutual Exclusion via Cooperation

Cooperative threads can implement critical sections without locks:

```c
void coop_thread(void *p1, void *p2, void *p3)
{
    /* No other thread can interrupt this section */
    access_shared_resource();
    modify_data();
    /* Still safe, we're cooperative */

    k_yield();  /* Now others can run */
}
```

**Warning**: Only works if ALL threads accessing the resource are cooperative and don't block during access.

## Preemptive Behavior

Preemptive threads (non-negative priority) can be preempted when:
- A higher-priority thread becomes ready
- An equal-priority thread becomes ready (with time slicing)
- An ISR returns and a higher/equal priority thread is ready

### Preemption Example

```
Time  Thread A (prio 5)    Thread B (prio 3)    Event
───────────────────────────────────────────────────────────
0     Running              Blocked              A is running
1     Running              Blocked              A still running
2     ─preempted─          Ready→Running        B unblocked (higher prio)
3     Ready                Running              B runs
4     Ready                Running              B runs
5     Ready→Running        Blocked              B blocks, A resumes
```

## Time Slicing

When enabled, the scheduler gives equal-priority preemptive threads fair CPU time by preempting them after a time slice.

### Configuration

```
# Enable time slicing
CONFIG_TIMESLICING=y

# Time slice duration (default: 0 = no time slicing)
CONFIG_TIMESLICE_SIZE=10  # milliseconds

# Only apply time slicing at or below this priority (0=all preemptive)
CONFIG_TIMESLICE_PRIORITY=0
```

### Per-Thread Time Slice

```c
/* Set custom time slice for a specific thread */
k_thread_time_slice_set(&my_thread,
                        K_MSEC(20),      /* slice duration */
                        slice_expired,    /* callback (or NULL) */
                        NULL);            /* callback arg */

void slice_expired(struct k_thread *thread, void *data)
{
    /* Called when thread's time slice expires */
}
```

### Time Slice Behavior

1. At end of time slice, scheduler implicitly calls `k_yield()` for the thread
2. If no equal-priority ready threads exist, thread continues
3. Cooperative threads and threads above `CONFIG_TIMESLICE_PRIORITY` are exempt

**Note**: Time slicing does NOT guarantee equal CPU time—it only ensures no thread runs longer than one slice without yielding.

## Scheduler Locking

A preemptive thread can temporarily become unpreemptible:

```c
void critical_operation(void)
{
    /* Lock scheduler - thread becomes effectively cooperative */
    k_sched_lock();

    /* Critical section - cannot be preempted */
    modify_shared_state();

    /* Unlock scheduler - preemption restored */
    k_sched_unlock();
}
```

**Behavior**:
- While locked, thread cannot be preempted by scheduler
- Thread can still block (on semaphore, sleep, etc.)—scheduler switches then
- When thread becomes ready again, lock state is preserved
- ISRs still interrupt (scheduler lock != interrupt lock)

**Use case**: More efficient than changing priority for short critical sections.

## Thread Sleeping

### Sleep APIs

```c
/* Sleep for specified timeout */
int32_t remaining = k_sleep(K_SECONDS(1));
int32_t remaining = k_sleep(K_MSEC(500));
int32_t remaining = k_sleep(K_FOREVER);  /* sleep until woken */

/* Convenience wrappers */
int32_t remaining = k_msleep(500);   /* milliseconds */
int32_t remaining = k_usleep(1000);  /* microseconds */
```

**Return value**: Time remaining if woken early by `k_wakeup()`, or 0 if full duration elapsed.

### Wake a Sleeping Thread

```c
k_tid_t tid = /* sleeping thread */;
k_wakeup(tid);  /* no effect if thread not sleeping */
```

### Busy Waiting

For very short delays where context switch overhead exceeds delay:

```c
/* Busy wait (does NOT yield CPU) */
k_busy_wait(100);  /* microseconds */
```

**Use sparingly**: Wastes CPU cycles, starves other threads.

## CPU Idling

Normally handled by the idle thread. Direct use rarely needed.

```c
/* Simple idle (returns on any interrupt) */
k_cpu_idle();

/* Atomic idle (for race-free event waiting) */
unsigned int key = irq_lock();
if (event_not_ready) {
    k_cpu_atomic_idle(key);  /* atomically unlocks and idles */
} else {
    irq_unlock(key);
}
```

**Warning**: Avoid unless implementing custom power management. Idle thread handles this.

## Earliest Deadline First Scheduling

Optional feature for advanced scheduling:

```
CONFIG_SCHED_DEADLINE=y
```

```c
/* Set thread deadline (absolute time) */
k_thread_deadline_set(tid, deadline_cycle);
```

When enabled, among threads with equal static priority, the one with the earlier deadline runs first.

## SMP Considerations

With symmetric multiprocessing (`CONFIG_SMP=y`):

### CPU Affinity

```c
/* Pin thread to specific CPU */
k_thread_cpu_pin(tid, cpu_id);

/* Set CPU mask (which CPUs thread can run on) */
k_thread_cpu_mask_clear(tid);
k_thread_cpu_mask_enable(tid, 0);  /* enable CPU 0 */
k_thread_cpu_mask_enable(tid, 1);  /* enable CPU 1 */
```

### SMP Scheduling

- Each CPU runs independent scheduler
- Threads can migrate between CPUs unless pinned
- Global ready queue vs per-CPU queue depends on config

## Scheduler Implementation Options

Choose ready queue implementation based on workload:

| Option | Best For | Trade-off |
| :--- | :--- | :--- |
| `CONFIG_SCHED_SIMPLE` | < 3 runnable threads | Smallest code, O(n) insert |
| `CONFIG_SCHED_MULTIQ` | General use | Array of lists, O(1), more RAM |
| `CONFIG_SCHED_SCALABLE` | > 20 runnable threads | Red-black tree, O(log n), +2KB code |

Similarly for wait queues:
- `CONFIG_WAITQ_SIMPLE`: Doubly-linked list (few waiters)
- `CONFIG_WAITQ_SCALABLE`: Balanced tree (many waiters)
