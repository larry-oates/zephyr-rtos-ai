# Thread Lifecycle

## Table of Contents
- [Thread Properties](#thread-properties)
- [Thread Creation](#thread-creation)
- [Thread States](#thread-states)
- [Thread Control](#thread-control)
- [Thread Stack Management](#thread-stack-management)
- [System Threads](#system-threads)

## Thread Properties

Every Zephyr thread has:

| Property | Description |
| :--- | :--- |
| **Stack area** | Memory region for thread's stack (must use special macros) |
| **Thread control block** | `struct k_thread` instance for kernel bookkeeping |
| **Entry point function** | Function invoked on start, receives up to 3 arguments |
| **Scheduling priority** | Integer determining CPU time allocation |
| **Thread options** | Flags for special kernel treatment (see below) |
| **Start delay** | How long kernel waits before starting thread |
| **Execution mode** | Supervisor (default) or user mode |

### Thread Options

| Option | Effect |
| :--- | :--- |
| `K_ESSENTIAL` | Thread termination/abort triggers fatal system error |
| `K_FP_REGS` | Kernel saves/restores floating point registers on context switch |
| `K_SSE_REGS` | (x86) Kernel saves/restores SSE registers |
| `K_USER` | Thread runs in user mode with reduced privileges (requires `CONFIG_USERSPACE`) |
| `K_INHERIT_PERMS` | Thread inherits parent's kernel object permissions |

Combine options with bitwise OR: `K_ESSENTIAL | K_FP_REGS`

## Thread Creation

### Static Definition (Compile-time)

Use `K_THREAD_DEFINE` for threads known at compile time. Stack and control block are auto-defined.

```c
#define STACK_SIZE 1024
#define PRIORITY 5

void my_entry_point(void *p1, void *p2, void *p3) {
    ARG_UNUSED(p1);
    ARG_UNUSED(p2);
    ARG_UNUSED(p3);

    while (1) {
        /* thread processing */
        k_msleep(100);
    }
}

/* Thread starts immediately (delay=0) */
K_THREAD_DEFINE(my_thread_id, STACK_SIZE,
                my_entry_point, NULL, NULL, NULL,
                PRIORITY, 0, 0);

/* Thread with delayed start (500ms) */
K_THREAD_DEFINE(delayed_thread, STACK_SIZE,
                my_entry_point, NULL, NULL, NULL,
                PRIORITY, K_ESSENTIAL, 500);
```

**Note**: The delay parameter in `K_THREAD_DEFINE` is in milliseconds (integer), not `k_timeout_t`.

### Dynamic Creation (Runtime)

Use `k_thread_create` when thread parameters are determined at runtime.

```c
K_THREAD_STACK_DEFINE(my_stack_area, 1024);
struct k_thread my_thread_data;

void start_my_thread(void)
{
    k_tid_t tid = k_thread_create(
        &my_thread_data,              /* thread control block */
        my_stack_area,                /* stack area */
        K_THREAD_STACK_SIZEOF(my_stack_area),  /* stack size */
        my_entry_point,               /* entry function */
        NULL, NULL, NULL,             /* p1, p2, p3 arguments */
        5,                            /* priority */
        0,                            /* options */
        K_NO_WAIT                     /* start immediately */
    );

    k_thread_name_set(tid, "my_thread");  /* optional: set name for debugging */
}
```

### Delayed Start

```c
/* Create but don't start */
k_tid_t tid = k_thread_create(&data, stack, size, entry,
                              NULL, NULL, NULL,
                              PRIORITY, 0, K_FOREVER);

/* Later, start the thread */
k_thread_start(tid);

/* Or create with specific delay */
k_tid_t tid = k_thread_create(&data, stack, size, entry,
                              NULL, NULL, NULL,
                              PRIORITY, 0, K_MSEC(500));
```

### Dynamic Stack Allocation

```c
void *stack = k_thread_stack_alloc(CONFIG_DYNAMIC_THREAD_STACK_SIZE);
if (stack == NULL) {
    /* allocation failed */
    return;
}

k_tid_t tid = k_thread_create(&thread_data, stack,
                              CONFIG_DYNAMIC_THREAD_STACK_SIZE,
                              entry, NULL, NULL, NULL,
                              PRIORITY, 0, K_NO_WAIT);

/* When thread completes, free the stack */
k_thread_join(tid, K_FOREVER);
k_thread_stack_free(stack);
```

## Thread States

A thread is either **ready** (eligible for execution) or **unready** (cannot execute).

### Factors Making Thread Unready

| Factor | Description |
| :--- | :--- |
| Not started | Thread created with delay or `K_FOREVER` |
| Waiting on kernel object | e.g., `k_sem_take()`, `k_mutex_lock()` with blocking |
| Waiting for timeout | e.g., `k_sleep()`, `k_msleep()` |
| Suspended | `k_thread_suspend()` called |
| Terminated/Aborted | Thread returned from entry or was aborted |

### State Transitions

```
                 ┌──────────────┐
                 │   Created    │
                 │  (unready)   │
                 └──────┬───────┘
                        │ k_thread_start() or delay expires
                        ▼
┌───────────┐    ┌──────────────┐
│ Suspended │◄───│    Ready     │
│ (unready) │    │              │
└─────┬─────┘    └──────┬───────┘
      │                 │ selected by scheduler
      │ k_thread_resume │
      └────────────────►▼
                 ┌──────────────┐
                 │   Running    │
                 │              │
                 └──────┬───────┘
                        │ blocks, sleeps, or yields
                        ▼
                 ┌──────────────┐
                 │   Waiting    │
                 │  (unready)   │
                 └──────┬───────┘
                        │ wait satisfied
                        ▼
                 [back to Ready]
```

## Thread Control

### Suspend and Resume

```c
k_tid_t tid = /* ... */;

/* Suspend thread (can suspend itself or others) */
k_thread_suspend(tid);

/* Resume suspended thread */
k_thread_resume(tid);

/* Suspending already-suspended thread has no additional effect */
```

### Sleep and Wake

```c
/* Current thread sleeps for specified time */
k_sleep(K_SECONDS(1));      /* timeout type */
k_msleep(1000);             /* milliseconds (convenience) */
k_usleep(1000000);          /* microseconds */

/* Wake another thread early */
k_wakeup(tid);              /* no effect if thread not sleeping */
```

### Yield

```c
/* Voluntarily give up CPU to equal/higher priority ready threads */
k_yield();
```

### Termination

A thread **terminates** by returning from its entry function:

```c
void my_entry_point(void *p1, void *p2, void *p3)
{
    /* Release any held resources before returning! */
    k_mutex_unlock(&my_mutex);
    k_free(my_buffer);

    /* Thread terminates */
    return;
}
```

**Critical**: Kernel does NOT auto-release resources (mutexes, allocated memory). Clean up before return.

### Abort

A thread **aborts** when:
- It triggers a fatal error (null pointer, etc.)
- Another thread calls `k_thread_abort(tid)`

```c
/* Abort another thread (prefer graceful termination when possible) */
k_thread_abort(tid);

/* Abort self */
k_thread_abort(k_current_get());
```

### Join (Wait for Completion)

```c
/* Block until thread terminates or aborts (or timeout) */
int ret = k_thread_join(tid, K_FOREVER);

/* With timeout */
ret = k_thread_join(tid, K_MSEC(5000));
if (ret == -EAGAIN) {
    /* timeout expired, thread still running */
}
```

**Note**: After `k_thread_join` returns successfully, the thread struct memory can be reused.

## Thread Stack Management

### Stack Macros

| Macro | Use Case |
| :--- | :--- |
| `K_THREAD_STACK_DEFINE(name, size)` | Threads that may run in user mode |
| `K_KERNEL_STACK_DEFINE(name, size)` | Kernel-only threads (smaller footprint) |
| `K_THREAD_STACK_SIZEOF(stack)` | Get actual usable size for thread creation |
| `K_KERNEL_STACK_SIZEOF(stack)` | Get actual usable size for kernel stack |
| `K_THREAD_STACK_ARRAY_DEFINE(name, n, size)` | Array of n stacks |

### Stack Size Considerations

- Include space for: local variables, function call frames, ISR preemption
- Use `CONFIG_THREAD_ANALYZER` to measure actual usage
- Start larger, then tune down based on measurements

```c
/* Check stack usage at runtime */
#include <zephyr/debug/thread_analyzer.h>

thread_analyzer_print();  /* prints all thread stack usage */
```

### Guard Against Overflow

Enable stack overflow detection in Kconfig:
```
CONFIG_THREAD_STACK_INFO=y
CONFIG_THREAD_ANALYZER=y
```

## System Threads

Zephyr automatically creates these threads:

### Main Thread

- Performs kernel initialization
- Calls application's `main()` function
- Default priority: highest preemptive (0) or lowest cooperative (-1) if no preemptive
- Marked essential during init and `main()` execution
- Can terminate normally after `main()` returns

```c
int main(void)
{
    /* Initialization */

    while (1) {
        /* Main thread can be used for application processing */
        k_msleep(1000);
    }

    /* Or return to terminate main thread (other threads continue) */
    return 0;
}
```

### Idle Thread

- Runs when no other threads are ready
- Activates power management or executes "do nothing" loop
- Lowest priority in system
- Never terminates (essential thread)

### System Workqueue Thread

- Created when system workqueue is used
- Processes work items submitted via `k_work_submit()`
- Priority configured via `CONFIG_SYSTEM_WORKQUEUE_PRIORITY`

## Thread Custom Data

Each thread has a 32-bit custom data field (requires `CONFIG_THREAD_CUSTOM_DATA=y`):

```c
/* Set custom data */
k_thread_custom_data_set((void *)my_context);

/* Get custom data */
struct my_context *ctx = k_thread_custom_data_get();
```

**Use case**: Store per-thread context when callback functions don't pass user data.

## User Mode Constraints

When `CONFIG_USERSPACE` is enabled and creating threads from user mode:

- Parent must have permissions on child thread and stack objects
- Child and stack must be uninitialized
- `K_USER` option is required
- `K_ESSENTIAL` option is forbidden
- Child priority must be equal or lower than parent
