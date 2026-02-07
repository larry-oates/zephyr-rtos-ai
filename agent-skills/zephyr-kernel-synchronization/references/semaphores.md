# Semaphores

A semaphore is a kernel object that implements a traditional counting semaphore.

## Concepts

-   **Count & Limit:** Has a current count and a maximum limit.
-   **Give/Take:** 'Give' increments count. 'Take' decrements count (blocks if 0).
-   **No Ownership:** Any thread (or ISR) can give. Any thread can take.
-   **ISR Safe:** ISRs can give. ISRs can take (if no wait).

## Implementation

### Defining

```c
struct k_sem my_sem;
// Init with initial_count=0, limit=1 (Binary Semaphore)
k_sem_init(&my_sem, 0, 1);
// OR
K_SEM_DEFINE(my_sem, 0, 1);
```

### Giving

```c
k_sem_give(&my_sem);
```

### Taking

```c
if (k_sem_take(&my_sem, K_MSEC(50)) == 0) {
    // Acquired
}
```

## Suggested Uses

-   **Control Access:** Limit number of threads accessing a resource (Counting Semaphore).
-   **Signaling:** Synchronize processing between Producer/Consumer (Binary Semaphore).
-   **Gate:** Count 0 blocks all, until given.
