# Condition Variables

A condition variable is a synchronization primitive that enables threads to wait until a particular condition occurs.

## Concepts

-   **Queue of Threads:** Basically a queue that threads can put themselves on when some state is not as desired.
-   **Atomic Operations:** `k_condvar_wait` atomically releases the mutex and puts the thread to sleep.
-   **Signaling:** `k_condvar_signal` wakes one thread, `k_condvar_broadcast` wakes all waiting threads.
-   **Mutex Association:** Must be used with a mutex to protect the shared state/condition.

## Implementation

### Defining

```c
struct k_condvar my_condvar;
k_condvar_init(&my_condvar);
// OR
K_CONDVAR_DEFINE(my_condvar);
```

### Waiting

```c
k_mutex_lock(&mutex, K_FOREVER);
// Blocks, releases mutex, waits for signal, re-acquires mutex
k_condvar_wait(&condvar, &mutex, K_FOREVER);
// Access shared resource
k_mutex_unlock(&mutex);
```

### Signaling

```c
k_mutex_lock(&mutex, K_FOREVER);
// Change state...
k_condvar_signal(&condvar); // Or k_condvar_broadcast(&condvar);
k_mutex_unlock(&mutex);
```

## Suggested Uses

-   Signal changing states (conditions) from one thread to another.
-   **Note:** Condition variables are *not* the condition itself. The condition is in the surrounding logic.
