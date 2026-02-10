# Mutexes

A mutex is a kernel object that implements a traditional reentrant mutex with priority inheritance.

## Table of Contents

1. [Concepts](#concepts)
2. [Implementation](#implementation)
3. [Priority Inheritance](#priority-inheritance)
4. [Reentrant Locking](#reentrant-locking)
5. [Use Patterns](#use-patterns)
6. [Common Pitfalls](#common-pitfalls)

## Concepts

-   **Mutual Exclusion:** Ensures only one thread can access a shared resource at a time.
-   **Ownership:** Has an owning thread. Only the owner can unlock the mutex.
-   **Reentrant:** The owner can lock multiple times (must unlock equal times).
-   **Priority Inheritance:** Temporarily elevates owner's priority if higher-priority thread waits.
-   **NOT ISR Safe:** Mutexes cannot be used by ISRs — use semaphores for ISR signaling.
-   **Wait Queue:** Multiple threads can wait. Highest priority thread that waited longest is woken first.

## Implementation

### Defining (Runtime)

```c
struct k_mutex my_mutex;

void init_function(void)
{
    k_mutex_init(&my_mutex);
}
```

### Defining (Compile-time)

```c
K_MUTEX_DEFINE(my_mutex);
```

### Locking

```c
/* Wait forever for the mutex */
k_mutex_lock(&my_mutex, K_FOREVER);

/* Wait with timeout */
if (k_mutex_lock(&my_mutex, K_MSEC(100)) == 0) {
    /* Acquired successfully */
} else {
    /* Timeout expired, mutex not acquired */
}

/* Non-blocking attempt */
if (k_mutex_lock(&my_mutex, K_NO_WAIT) == 0) {
    /* Acquired */
} else {
    /* Mutex already held by another thread */
}
```

### Unlocking

```c
/* Only the owning thread can unlock */
k_mutex_unlock(&my_mutex);
```

## Priority Inheritance

Priority inheritance prevents **priority inversion** — a situation where a high-priority thread waits for a low-priority thread that is preempted by medium-priority threads.

### How It Works

1. Thread L (low priority) locks mutex M.
2. Thread H (high priority) tries to lock M and blocks.
3. Kernel temporarily elevates L's priority to match H's.
4. L runs at high priority until it unlocks M.
5. H acquires M and runs. L's priority is restored.

### Configuration

```
# Limit how high priority can be raised (0 = unlimited)
CONFIG_PRIORITY_CEILING=0
```

### Multiple Mutex Limitation

Priority inheritance works optimally with one mutex. With multiple mutexes:

-   Base priority is saved when first mutex is locked.
-   Priority may be elevated multiple times.
-   When unlocking, priority is restored to saved base (not intermediate levels).

**Best Practice:** Lock only one mutex at a time when threads of different priorities share resources.

```c
/* Sub-optimal: multiple mutex locks */
k_mutex_lock(&mutex_a, K_FOREVER);
k_mutex_lock(&mutex_b, K_FOREVER);  /* Priority may be elevated */
/* ... */
k_mutex_unlock(&mutex_b);
k_mutex_unlock(&mutex_a);  /* Priority restored to base, not intermediate */

/* Better: single mutex or nested resources */
k_mutex_lock(&resource_mutex, K_FOREVER);
/* Access both resources */
k_mutex_unlock(&resource_mutex);
```

## Reentrant Locking

The owning thread can lock a mutex it already holds. Each lock increments an internal count; each unlock decrements it. The mutex is released when count reaches zero.

```c
K_MUTEX_DEFINE(resource_mutex);

void outer_function(void)
{
    k_mutex_lock(&resource_mutex, K_FOREVER);  /* count = 1 */
    inner_function();
    k_mutex_unlock(&resource_mutex);           /* count = 0, released */
}

void inner_function(void)
{
    k_mutex_lock(&resource_mutex, K_FOREVER);  /* count = 2 (same owner, OK) */
    /* Access resource */
    k_mutex_unlock(&resource_mutex);           /* count = 1 */
}
```

## Use Patterns

### Pattern 1: Protecting Shared Data

```c
K_MUTEX_DEFINE(data_mutex);
static int shared_counter;

void increment_counter(void)
{
    k_mutex_lock(&data_mutex, K_FOREVER);
    shared_counter++;
    k_mutex_unlock(&data_mutex);
}

int read_counter(void)
{
    int value;
    k_mutex_lock(&data_mutex, K_FOREVER);
    value = shared_counter;
    k_mutex_unlock(&data_mutex);
    return value;
}
```

### Pattern 2: Protecting Hardware Access

```c
K_MUTEX_DEFINE(display_mutex);

void display_write(const char *text)
{
    k_mutex_lock(&display_mutex, K_FOREVER);
    /* Only one thread can access display hardware */
    hw_display_send(text);
    k_mutex_unlock(&display_mutex);
}
```

### Pattern 3: Dining Philosophers (Deadlock Avoidance)

Dijkstra's solution: Always acquire lower-numbered fork first.

```c
K_MUTEX_DEFINE(fork0);
K_MUTEX_DEFINE(fork1);
/* ... */

void philosopher(int id)
{
    struct k_mutex *first, *second;

    /* Always pick up lower-numbered fork first */
    if (id == NUM_PHILOSOPHERS - 1) {
        first = &fork0;
        second = &forks[id];
    } else {
        first = &forks[id];
        second = &forks[id + 1];
    }

    while (1) {
        k_mutex_lock(first, K_FOREVER);
        k_mutex_lock(second, K_FOREVER);
        /* Eat */
        k_mutex_unlock(second);
        k_mutex_unlock(first);
        /* Think */
    }
}
```

### Pattern 4: Try-Lock Pattern

Non-blocking lock attempt for optional work.

```c
void optional_maintenance(void)
{
    if (k_mutex_lock(&resource_mutex, K_NO_WAIT) == 0) {
        /* Got the lock, do maintenance */
        perform_maintenance();
        k_mutex_unlock(&resource_mutex);
    }
    /* If lock not available, skip maintenance this time */
}
```

## Common Pitfalls

### 1. Using Mutex in ISR

**Problem:** Mutexes require thread context and cannot be used in ISRs.

```c
void isr_handler(void *arg)
{
    /* CRASH: Cannot use mutex in ISR */
    k_mutex_lock(&my_mutex, K_FOREVER);
}
```

**Solution:** Use semaphores to signal from ISR to thread.

### 2. Unlocking from Wrong Thread

**Problem:** Only the owner can unlock a mutex.

```c
void thread_a(void)
{
    k_mutex_lock(&mutex, K_FOREVER);
    /* Start thread B to "help" */
}

void thread_b(void)
{
    /* ERROR: Thread B is not the owner */
    k_mutex_unlock(&mutex);  /* Returns error, mutex stays locked */
}
```

**Solution:** Ensure the same thread that locks also unlocks.

### 3. Deadlock from Inconsistent Lock Order

**Problem:** Two threads lock multiple mutexes in different orders.

```c
/* Thread A */
k_mutex_lock(&mutex1, K_FOREVER);
k_mutex_lock(&mutex2, K_FOREVER);  /* Waits for B */

/* Thread B (simultaneously) */
k_mutex_lock(&mutex2, K_FOREVER);
k_mutex_lock(&mutex1, K_FOREVER);  /* Waits for A */

/* DEADLOCK: Both threads wait forever */
```

**Solution:** Always lock mutexes in the same order across all threads.

### 4. Forgetting to Unlock

**Problem:** Mutex remains locked, blocking other threads forever.

```c
void process_data(void)
{
    k_mutex_lock(&data_mutex, K_FOREVER);

    if (error_condition) {
        return;  /* BUG: mutex never unlocked! */
    }

    /* ... process ... */
    k_mutex_unlock(&data_mutex);
}
```

**Solution:** Ensure all code paths unlock the mutex.

```c
void process_data(void)
{
    k_mutex_lock(&data_mutex, K_FOREVER);

    if (error_condition) {
        k_mutex_unlock(&data_mutex);
        return;
    }

    /* ... process ... */
    k_mutex_unlock(&data_mutex);
}
```

### 5. Using Semaphore Instead of Mutex

**Problem:** Semaphores lack ownership and priority inheritance.

```c
/* BAD: Semaphore as lock */
K_SEM_DEFINE(lock, 1, 1);

void low_priority_thread(void)
{
    k_sem_take(&lock, K_FOREVER);
    /* High priority thread waits without priority boost */
    /* ... long operation ... */
    k_sem_give(&lock);
}
```

**Solution:** Use mutex when protecting shared resources between threads.
