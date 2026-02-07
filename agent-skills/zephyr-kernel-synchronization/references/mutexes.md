# Mutexes

A mutex is a kernel object that implements a traditional reentrant mutex.

## Concepts

-   **Mutual Exclusion:** Ensures exclusive access to a shared resource.
-   **Ownership:** Has an owning thread. Only the owner can unlock it.
-   **Reentrant:** The owner can lock it multiple times (must unlock equal times).
-   **Priority Inheritance:** Temporarily elevates owner's priority if a higher-priority thread waits on the mutex.
-   **NOT ISR Safe:** Cannot be used by ISRs.

## Implementation

### Defining

```c
struct k_mutex my_mutex;
k_mutex_init(&my_mutex);
// OR
K_MUTEX_DEFINE(my_mutex);
```

### Locking

```c
k_mutex_lock(&my_mutex, K_FOREVER);
// OR with timeout
if (k_mutex_lock(&my_mutex, K_MSEC(100)) == 0) { ... }
```

### Unlocking

```c
k_mutex_unlock(&my_mutex);
```

## Suggested Uses

-   Provide exclusive access to a resource (e.g., physical device, shared memory buffer).

## Priority Inheritance Details

-   Solves priority inversion.
-   Limited by `CONFIG_PRIORITY_CEILING`.
-   Best practice: Lock only a single mutex at a time if possible to avoid sub-optimal priority restoration orders.
