# Semaphores

A semaphore is a kernel object that implements a traditional counting semaphore.

## Table of Contents

1. [Concepts](#concepts)
2. [Implementation](#implementation)
3. [Use Patterns](#use-patterns)
4. [ISR Usage](#isr-usage)
5. [Common Pitfalls](#common-pitfalls)

## Concepts

-   **Count & Limit:** Has a current count (number of times it can be taken) and a maximum limit.
-   **Give/Take:** `k_sem_give()` increments count (up to limit). `k_sem_take()` decrements count (blocks if 0).
-   **No Ownership:** Any thread or ISR can give. Any thread can take. No tracking of who "owns" the semaphore.
-   **ISR Safe:** ISRs can give. ISRs can take only with `K_NO_WAIT`.
-   **Wait Queue:** Multiple threads can wait on a semaphore. When given, the highest priority thread that waited longest is woken.

## Implementation

### Defining (Runtime)

```c
struct k_sem my_sem;

void init_function(void)
{
    /* Initialize with initial_count=0, limit=1 (Binary Semaphore) */
    k_sem_init(&my_sem, 0, 1);
}
```

### Defining (Compile-time)

```c
/* Binary semaphore: initial=0, limit=1 */
K_SEM_DEFINE(my_sem, 0, 1);

/* Counting semaphore: initial=5 available, limit=5 max */
K_SEM_DEFINE(resource_sem, 5, 5);
```

### Giving (Signaling)

```c
/* Increment count (up to limit). Never blocks. */
k_sem_give(&my_sem);
```

### Taking (Waiting)

```c
/* Wait forever */
k_sem_take(&my_sem, K_FOREVER);

/* Wait with timeout */
if (k_sem_take(&my_sem, K_MSEC(50)) == 0) {
    /* Acquired successfully */
} else {
    /* Timeout expired, semaphore not acquired */
}

/* Non-blocking (for ISRs or polling) */
if (k_sem_take(&my_sem, K_NO_WAIT) == 0) {
    /* Acquired */
}
```

### Resetting

```c
/* Reset count to 0, wake no waiting threads */
k_sem_reset(&my_sem);
```

### Querying Count

```c
unsigned int count = k_sem_count_get(&my_sem);
```

## Use Patterns

### Pattern 1: Binary Semaphore for Signaling (ISR-to-Thread)

Use when an ISR needs to signal a thread that work is ready.

```c
K_SEM_DEFINE(data_ready_sem, 0, 1);

void isr_handler(void *arg)
{
    /* Data arrived, signal the processing thread */
    k_sem_give(&data_ready_sem);
}

void processing_thread(void)
{
    while (1) {
        /* Block until ISR signals data is ready */
        k_sem_take(&data_ready_sem, K_FOREVER);
        /* Process the data */
        process_incoming_data();
    }
}
```

### Pattern 2: Counting Semaphore for Resource Pool

Use to limit concurrent access to a pool of resources.

```c
#define NUM_BUFFERS 3
K_SEM_DEFINE(buffer_sem, NUM_BUFFERS, NUM_BUFFERS);

void *acquire_buffer(void)
{
    /* Wait for a buffer to become available */
    k_sem_take(&buffer_sem, K_FOREVER);
    return allocate_from_pool();
}

void release_buffer(void *buf)
{
    return_to_pool(buf);
    k_sem_give(&buffer_sem);
}
```

### Pattern 3: Thread Ping-Pong Synchronization

Use two semaphores to alternate execution between threads.

```c
K_SEM_DEFINE(sem_a, 1, 1);  /* Thread A starts first */
K_SEM_DEFINE(sem_b, 0, 1);

void thread_a(void)
{
    while (1) {
        k_sem_take(&sem_a, K_FOREVER);
        /* Do work */
        k_sem_give(&sem_b);  /* Hand off to thread B */
    }
}

void thread_b(void)
{
    while (1) {
        k_sem_take(&sem_b, K_FOREVER);
        /* Do work */
        k_sem_give(&sem_a);  /* Hand off to thread A */
    }
}
```

### Pattern 4: Gate (Barrier)

Block all threads until an initialization completes.

```c
K_SEM_DEFINE(init_gate, 0, 1);

void init_thread(void)
{
    /* Perform initialization */
    do_hardware_init();
    /* Open the gate */
    k_sem_give(&init_gate);
}

void worker_thread(void)
{
    /* Wait for initialization to complete */
    k_sem_take(&init_gate, K_FOREVER);
    /* Give back so other threads can proceed */
    k_sem_give(&init_gate);

    /* Now do work */
    do_work();
}
```

## ISR Usage

-   **Giving from ISR:** Always safe. `k_sem_give()` never blocks.
-   **Taking from ISR:** Only with `K_NO_WAIT`. ISRs must never block.

```c
void my_isr(void *arg)
{
    /* Safe: giving from ISR */
    k_sem_give(&my_sem);

    /* Safe: non-blocking take */
    if (k_sem_take(&another_sem, K_NO_WAIT) == 0) {
        /* Acquired */
    }

    /* FORBIDDEN: blocking take in ISR */
    /* k_sem_take(&my_sem, K_FOREVER);  // NEVER DO THIS */
}
```

## Common Pitfalls

### 1. Using Semaphores for Mutual Exclusion (Instead of Mutex)

**Problem:** Semaphores lack ownership and priority inheritance.

```c
/* BAD: Using semaphore as a lock between threads of different priorities */
K_SEM_DEFINE(lock_sem, 1, 1);

void low_priority_thread(void) {
    k_sem_take(&lock_sem, K_FOREVER);
    /* ... long operation ... */
    k_sem_give(&lock_sem);  /* High priority thread waits without priority inheritance */
}
```

**Solution:** Use `k_mutex` for mutual exclusion between threads.

### 2. Giving Multiple Times Without Taking

**Problem:** Giving beyond the limit has no effect; signals can be "lost."

```c
K_SEM_DEFINE(sem, 0, 1);

/* ISR fires twice before thread runs */
k_sem_give(&sem);  /* count = 1 */
k_sem_give(&sem);  /* count still 1 (limit reached) - second signal lost! */

/* Thread only sees one signal */
k_sem_take(&sem, K_FOREVER);  /* count = 0 */
```

**Solution:** Use counting semaphore with higher limit, or use events/message queues.

### 3. Blocking in ISR

**Problem:** Calling `k_sem_take()` with timeout in ISR causes system crash.

```c
void isr_handler(void *arg)
{
    /* CRASH: Never block in ISR */
    k_sem_take(&sem, K_MSEC(100));
}
```

**Solution:** Always use `K_NO_WAIT` in ISRs and handle the failure case.

### 4. Forgetting to Initialize

**Problem:** Using `struct k_sem` without initialization causes undefined behavior.

```c
struct k_sem my_sem;
/* WRONG: Using without init */
k_sem_take(&my_sem, K_FOREVER);  /* Undefined behavior */
```

**Solution:** Always call `k_sem_init()` or use `K_SEM_DEFINE()`.
