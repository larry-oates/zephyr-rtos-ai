# Condition Variables

A condition variable is a synchronization primitive that enables threads to wait until a particular condition (state) occurs.

## Table of Contents

1. [Concepts](#concepts)
2. [Implementation](#implementation)
3. [Signal vs Broadcast](#signal-vs-broadcast)
4. [Use Patterns](#use-patterns)
5. [Common Pitfalls](#common-pitfalls)

## Concepts

-   **Condition Predicate:** The actual condition is in your code (e.g., `queue_empty == false`). The condvar is the waiting mechanism.
-   **Paired with Mutex:** Always used with a mutex that protects the shared state.
-   **Atomic Release-and-Wait:** `k_condvar_wait()` atomically releases the mutex and puts the thread to sleep.
-   **Wake-and-Reacquire:** When signaled, the thread reacquires the mutex before returning.
-   **Signal vs Broadcast:**
    -   `k_condvar_signal()`: Wake ONE waiting thread.
    -   `k_condvar_broadcast()`: Wake ALL waiting threads.
-   **NOT ISR Safe:** Condition variables require mutex operations; cannot be used from ISRs.

## Implementation

### Defining (Runtime)

```c
struct k_condvar my_condvar;

void init_function(void)
{
    k_condvar_init(&my_condvar);
}
```

### Defining (Compile-time)

```c
K_CONDVAR_DEFINE(my_condvar);
K_MUTEX_DEFINE(my_mutex);
```

### Waiting

**IMPORTANT:** Always use a `while` loop to re-check the condition after waking.

```c
k_mutex_lock(&mutex, K_FOREVER);

/* Wait for condition using WHILE loop (not if!) */
while (!condition_is_true()) {
    /* Atomically: release mutex, sleep, then reacquire mutex when woken */
    k_condvar_wait(&condvar, &mutex, K_FOREVER);
}

/* Condition is now true, mutex is held */
do_work();

k_mutex_unlock(&mutex);
```

### Waiting with Timeout

```c
k_mutex_lock(&mutex, K_FOREVER);

while (!condition_is_true()) {
    int ret = k_condvar_wait(&condvar, &mutex, K_MSEC(100));
    if (ret == -EAGAIN) {
        /* Timeout expired, condition still not true */
        k_mutex_unlock(&mutex);
        return -ETIMEDOUT;
    }
}

/* Condition is true */
k_mutex_unlock(&mutex);
```

### Signaling (Wake One)

```c
k_mutex_lock(&mutex, K_FOREVER);

/* Modify the shared state */
make_condition_true();

/* Wake one waiting thread */
k_condvar_signal(&condvar);

k_mutex_unlock(&mutex);
```

### Broadcasting (Wake All)

```c
k_mutex_lock(&mutex, K_FOREVER);

/* Modify the shared state */
change_shared_state();

/* Wake all waiting threads */
k_condvar_broadcast(&condvar);

k_mutex_unlock(&mutex);
```

## Signal vs Broadcast

| Scenario | Use |
| :--- | :--- |
| One waiter should handle the condition | `k_condvar_signal()` |
| Multiple waiters, but only one can proceed | `k_condvar_signal()` |
| Multiple waiters should all wake and re-evaluate | `k_condvar_broadcast()` |
| State change affects all waiters | `k_condvar_broadcast()` |
| Shutdown/termination notification | `k_condvar_broadcast()` |

**Rule of thumb:** When in doubt, use `broadcast`. It's safer but may wake threads unnecessarily.

## Use Patterns

### Pattern 1: Producer-Consumer Queue

Classic bounded buffer with wait-for-not-empty and wait-for-not-full.

```c
#define QUEUE_SIZE 10

K_MUTEX_DEFINE(queue_mutex);
K_CONDVAR_DEFINE(queue_not_empty);
K_CONDVAR_DEFINE(queue_not_full);

static int queue[QUEUE_SIZE];
static int head, tail, count;

void producer(int item)
{
    k_mutex_lock(&queue_mutex, K_FOREVER);

    /* Wait while queue is full */
    while (count == QUEUE_SIZE) {
        k_condvar_wait(&queue_not_full, &queue_mutex, K_FOREVER);
    }

    /* Add item to queue */
    queue[tail] = item;
    tail = (tail + 1) % QUEUE_SIZE;
    count++;

    /* Signal that queue is no longer empty */
    k_condvar_signal(&queue_not_empty);

    k_mutex_unlock(&queue_mutex);
}

int consumer(void)
{
    k_mutex_lock(&queue_mutex, K_FOREVER);

    /* Wait while queue is empty */
    while (count == 0) {
        k_condvar_wait(&queue_not_empty, &queue_mutex, K_FOREVER);
    }

    /* Remove item from queue */
    int item = queue[head];
    head = (head + 1) % QUEUE_SIZE;
    count--;

    /* Signal that queue is no longer full */
    k_condvar_signal(&queue_not_full);

    k_mutex_unlock(&queue_mutex);

    return item;
}
```

### Pattern 2: Thread Join / Completion Tracking

Wait for worker threads to complete.

```c
#define NUM_WORKERS 5

K_MUTEX_DEFINE(completion_mutex);
K_CONDVAR_DEFINE(completion_cv);

static int completed_count;

void worker_thread(void *id)
{
    /* Do work */
    do_work((long)id);

    k_mutex_lock(&completion_mutex, K_FOREVER);
    completed_count++;
    k_condvar_signal(&completion_cv);  /* or broadcast if multiple waiters */
    k_mutex_unlock(&completion_mutex);
}

void wait_for_all_workers(void)
{
    k_mutex_lock(&completion_mutex, K_FOREVER);

    while (completed_count < NUM_WORKERS) {
        k_condvar_wait(&completion_cv, &completion_mutex, K_FOREVER);
    }

    k_mutex_unlock(&completion_mutex);
    printk("All workers completed\n");
}
```

### Pattern 3: Threshold Notification

Wait until a counter reaches a specific value.

```c
K_MUTEX_DEFINE(count_mutex);
K_CONDVAR_DEFINE(count_threshold_cv);

static int count;
#define COUNT_LIMIT 10

void incrementer(void)
{
    k_mutex_lock(&count_mutex, K_FOREVER);
    count++;

    if (count >= COUNT_LIMIT) {
        k_condvar_signal(&count_threshold_cv);
    }

    k_mutex_unlock(&count_mutex);
}

void wait_for_threshold(void)
{
    k_mutex_lock(&count_mutex, K_FOREVER);

    while (count < COUNT_LIMIT) {
        k_condvar_wait(&count_threshold_cv, &count_mutex, K_FOREVER);
    }

    printk("Threshold reached: count = %d\n", count);
    k_mutex_unlock(&count_mutex);
}
```

### Pattern 4: Barrier (All Threads Synchronize)

Wait until all threads reach a synchronization point.

```c
#define NUM_THREADS 4

K_MUTEX_DEFINE(barrier_mutex);
K_CONDVAR_DEFINE(barrier_cv);

static int arrived_count;
static int barrier_generation;

void barrier_wait(void)
{
    k_mutex_lock(&barrier_mutex, K_FOREVER);

    int my_generation = barrier_generation;
    arrived_count++;

    if (arrived_count == NUM_THREADS) {
        /* Last thread to arrive */
        arrived_count = 0;
        barrier_generation++;
        k_condvar_broadcast(&barrier_cv);  /* Wake all waiting threads */
    } else {
        /* Wait for others */
        while (my_generation == barrier_generation) {
            k_condvar_wait(&barrier_cv, &barrier_mutex, K_FOREVER);
        }
    }

    k_mutex_unlock(&barrier_mutex);
}
```

## Common Pitfalls

### 1. Using `if` Instead of `while`

**Problem:** Spurious wakeups or multiple threads competing after broadcast.

```c
/* WRONG: Using if */
if (!condition_is_true()) {
    k_condvar_wait(&cv, &mutex, K_FOREVER);
}
/* Condition may still be false after wakeup! */
```

**Solution:** Always use `while`.

```c
/* CORRECT: Using while */
while (!condition_is_true()) {
    k_condvar_wait(&cv, &mutex, K_FOREVER);
}
/* Condition is guaranteed true here */
```

### 2. Signaling Without Holding the Mutex

**Problem:** Race condition between state change and signal.

```c
/* WRONG: Not holding mutex while signaling */
change_condition();
k_condvar_signal(&cv);  /* Waiter might miss the signal */
```

**Solution:** Always signal while holding the mutex.

```c
/* CORRECT */
k_mutex_lock(&mutex, K_FOREVER);
change_condition();
k_condvar_signal(&cv);
k_mutex_unlock(&mutex);
```

### 3. Using Condition Variable from ISR

**Problem:** Condition variables require mutex operations; ISRs cannot block.

```c
void isr_handler(void *arg)
{
    /* FORBIDDEN: Cannot use condvar from ISR */
    k_condvar_signal(&cv);
}
```

**Solution:** Use semaphores or events for ISR-to-thread signaling. Have ISR signal a semaphore, then thread signals condvar if needed.

### 4. Forgetting to Unlock Mutex

**Problem:** Mutex remains locked, other threads deadlock.

```c
void wait_for_condition(void)
{
    k_mutex_lock(&mutex, K_FOREVER);

    while (!condition) {
        k_condvar_wait(&cv, &mutex, K_FOREVER);
    }

    if (error) {
        return;  /* BUG: mutex never unlocked! */
    }

    k_mutex_unlock(&mutex);
}
```

**Solution:** Ensure all code paths unlock the mutex.

### 5. Using Signal When Broadcast Is Needed

**Problem:** Only one thread wakes when multiple should evaluate the condition.

```c
/* Multiple consumer threads waiting for data */
while (queue_empty()) {
    k_condvar_wait(&cv, &mutex, K_FOREVER);
}

/* Producer adds multiple items */
add_items_to_queue(10);
k_condvar_signal(&cv);  /* Only wakes ONE consumer! */
```

**Solution:** Use `broadcast` when condition change affects multiple waiters.

### 6. Condition Variable Is NOT the Condition

**Problem:** Confusing the condvar with the actual condition.

```c
/* WRONG mental model */
/* "Wait for condvar" does not mean "wait for condition" */
```

**Correct understanding:**
-   The **condition** is your boolean expression (e.g., `count >= 10`).
-   The **condvar** is the mechanism to efficiently wait and be woken.
-   Always check the actual condition in a loop.
