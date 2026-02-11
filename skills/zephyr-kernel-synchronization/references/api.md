# API Reference

Complete API signatures and configuration options for Zephyr synchronization primitives.

## Table of Contents

1. [Semaphore API](#semaphore-api)
2. [Mutex API](#mutex-api)
3. [Events API](#events-api)
4. [Condition Variable API](#condition-variable-api)
5. [Kconfig Options](#kconfig-options)
6. [Header Files](#header-files)

## Semaphore API

### Types

```c
struct k_sem;  /* Semaphore object */
```

### Macros

```c
/* Compile-time definition and initialization */
K_SEM_DEFINE(name, initial_count, count_limit)
```

### Functions

```c
/* Initialize a semaphore */
int k_sem_init(struct k_sem *sem, unsigned int initial_count, unsigned int limit);

/* Give (increment) a semaphore */
void k_sem_give(struct k_sem *sem);

/* Take (decrement) a semaphore with timeout */
int k_sem_take(struct k_sem *sem, k_timeout_t timeout);
/* Returns: 0 on success, -EBUSY if K_NO_WAIT and unavailable, -EAGAIN on timeout */

/* Reset semaphore count to zero */
void k_sem_reset(struct k_sem *sem);

/* Get current semaphore count */
unsigned int k_sem_count_get(struct k_sem *sem);
```

### Timeout Values

```c
K_NO_WAIT    /* Return immediately if semaphore unavailable */
K_FOREVER    /* Wait indefinitely */
K_MSEC(ms)   /* Wait for specified milliseconds */
K_USEC(us)   /* Wait for specified microseconds */
K_SECONDS(s) /* Wait for specified seconds */
```

## Mutex API

### Types

```c
struct k_mutex;  /* Mutex object */
```

### Macros

```c
/* Compile-time definition and initialization */
K_MUTEX_DEFINE(name)
```

### Functions

```c
/* Initialize a mutex */
int k_mutex_init(struct k_mutex *mutex);

/* Lock a mutex with timeout */
int k_mutex_lock(struct k_mutex *mutex, k_timeout_t timeout);
/* Returns: 0 on success, -EBUSY if K_NO_WAIT and locked, -EAGAIN on timeout */

/* Unlock a mutex (must be called by owner) */
int k_mutex_unlock(struct k_mutex *mutex);
/* Returns: 0 on success, -EPERM if not owner, -EINVAL if not locked */
```

## Events API

### Types

```c
struct k_event;  /* Event object */
```

### Macros

```c
/* Compile-time definition and initialization */
K_EVENT_DEFINE(name)
```

### Functions

```c
/* Initialize an event object */
void k_event_init(struct k_event *event);

/* Set events (overwrite) */
void k_event_set(struct k_event *event, uint32_t events);

/* Post events (bitwise OR) */
void k_event_post(struct k_event *event, uint32_t events);

/* Clear specific events */
void k_event_clear(struct k_event *event, uint32_t events);

/* Test (query) current events without waiting */
uint32_t k_event_test(struct k_event *event, uint32_t events_mask);

/* Wait for ANY of the specified events */
uint32_t k_event_wait(struct k_event *event, uint32_t events,
                      bool reset, k_timeout_t timeout);
/* Returns: Matching events, or 0 on timeout */

/* Wait for ALL of the specified events */
uint32_t k_event_wait_all(struct k_event *event, uint32_t events,
                          bool reset, k_timeout_t timeout);
/* Returns: Matching events (all requested), or 0 on timeout */
```

### Safe Variants (Atomic Clear on Receipt)

```c
/* Wait for ANY, atomically clear matched events */
uint32_t k_event_wait_safe(struct k_event *event, uint32_t events,
                           bool reset, k_timeout_t timeout);

/* Wait for ALL, atomically clear matched events */
uint32_t k_event_wait_all_safe(struct k_event *event, uint32_t events,
                               bool reset, k_timeout_t timeout);
```

### Parameters

-   `events`: Bitmask of events to wait for (up to 32 bits).
-   `reset`: If `true`, reset ALL events to 0 before waiting (use with caution in multi-waiter scenarios).
-   `timeout`: How long to wait.

## Condition Variable API

### Types

```c
struct k_condvar;  /* Condition variable object */
```

### Macros

```c
/* Compile-time definition and initialization */
K_CONDVAR_DEFINE(name)
```

### Functions

```c
/* Initialize a condition variable */
int k_condvar_init(struct k_condvar *condvar);

/* Wait on a condition variable (must hold mutex) */
int k_condvar_wait(struct k_condvar *condvar, struct k_mutex *mutex,
                   k_timeout_t timeout);
/*
 * Atomically releases mutex and blocks thread.
 * When signaled, reacquires mutex before returning.
 * Returns: 0 on success, -EAGAIN on timeout
 */

/* Signal one waiting thread */
int k_condvar_signal(struct k_condvar *condvar);
/* Returns: 0 on success */

/* Broadcast to all waiting threads */
int k_condvar_broadcast(struct k_condvar *condvar);
/* Returns: 0 on success */
```

## Kconfig Options

### Events

```
# Enable event objects (required for k_event_* APIs)
CONFIG_EVENTS=y
```

### Mutex Priority Inheritance

```
# Limit priority elevation (0 = unlimited, default)
# Higher values allow higher priority elevation
CONFIG_PRIORITY_CEILING=0
```

### General Kernel Options

```
# Enable preemptive scheduling (affects priority inheritance)
CONFIG_PREEMPT_ENABLED=y

# Enable cooperative scheduling
CONFIG_COOP_ENABLED=y
```

## Header Files

All synchronization primitives are declared in the main kernel header:

```c
#include <zephyr/kernel.h>
```

This single include provides access to:
-   `struct k_sem` and semaphore functions
-   `struct k_mutex` and mutex functions
-   `struct k_event` and event functions
-   `struct k_condvar` and condition variable functions
-   Timeout macros (`K_FOREVER`, `K_NO_WAIT`, `K_MSEC`, etc.)

## Return Value Conventions

| Return Value | Meaning |
| :--- | :--- |
| `0` | Success |
| `-EBUSY` | Resource busy (with `K_NO_WAIT`) |
| `-EAGAIN` | Timeout expired |
| `-EPERM` | Permission denied (e.g., unlock by non-owner) |
| `-EINVAL` | Invalid argument or state |

## ISR Safety Summary

| Function | ISR Safe? |
| :--- | :--- |
| `k_sem_give` | Yes |
| `k_sem_take` (K_NO_WAIT) | Yes |
| `k_sem_take` (with timeout) | No |
| `k_mutex_*` | No |
| `k_event_post` | Yes |
| `k_event_set` | Yes |
| `k_event_test` | Yes |
| `k_event_wait*` | No |
| `k_condvar_*` | No |
