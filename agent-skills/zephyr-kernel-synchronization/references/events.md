# Events

An event object is a kernel object that implements traditional events using a 32-bit bitmask for many-to-many signaling.

## Table of Contents

1. [Concepts](#concepts)
2. [Implementation](#implementation)
3. [Wait Variants](#wait-variants)
4. [Use Patterns](#use-patterns)
5. [ISR Usage](#isr-usage)
6. [Common Pitfalls](#common-pitfalls)

## Concepts

-   **Bitmask:** A 32-bit value tracks which events have occurred.
-   **Many-to-Many:** Multiple threads/ISRs can post events, multiple threads can wait.
-   **Post vs Set:**
    -   `k_event_post()`: Bitwise OR with existing events (adds to current state).
    -   `k_event_set()`: Overwrites existing events (replaces current state).
-   **Wait Options:**
    -   Wait for ANY of the requested bits (`k_event_wait`).
    -   Wait for ALL of the requested bits (`k_event_wait_all`).
-   **Safe Variants:** Atomically clear events upon receipt (`k_event_wait_safe`, `k_event_wait_all_safe`).
-   **ISR Safe:** ISRs can post/set events but cannot wait.

## Implementation

### Defining (Runtime)

```c
struct k_event my_event;

void init_function(void)
{
    k_event_init(&my_event);
}
```

### Defining (Compile-time)

```c
K_EVENT_DEFINE(my_event);
```

### Setting (Overwrite)

```c
/* Replace all event bits with 0x001 */
k_event_set(&my_event, 0x001);
```

### Posting (OR)

```c
/* Add bit 0x020 to existing events */
k_event_post(&my_event, 0x020);

/* Example: post from ISR */
void uart_isr(void *arg)
{
    k_event_post(&my_event, EVENT_UART_RX);
}
```

### Clearing

```c
/* Clear specific bits */
k_event_set(&my_event, k_event_test(&my_event) & ~BITS_TO_CLEAR);

/* Clear all events */
k_event_set(&my_event, 0);
```

## Wait Variants

### Wait for ANY (without removal)

Returns when ANY of the specified bits are set. Does not clear the events.

```c
uint32_t events;

/* Wait for any of bits 0-11 */
events = k_event_wait(&my_event, 0xFFF, false, K_MSEC(50));
if (events == 0) {
    /* Timeout - no events received */
} else {
    /* events contains the matched bits */
    if (events & 0x001) { /* Handle event 0 */ }
    if (events & 0x002) { /* Handle event 1 */ }
}
```

### Wait for ALL (without removal)

Returns only when ALL specified bits are set.

```c
uint32_t events;

/* Wait for bits 0, 5, and 8 (0x121) to ALL be set */
events = k_event_wait_all(&my_event, 0x121, false, K_MSEC(50));
if (events == 0) {
    /* Timeout - not all events received */
} else {
    /* All requested events are set */
}
```

### Wait for ANY (with atomic removal)

Clears the matched bits atomically upon receipt — prevents race conditions.

```c
uint32_t events;

/* Wait and atomically clear received events */
events = k_event_wait_safe(&my_event, 0xFFF, false, K_MSEC(50));
/* events are now cleared from the event object */
```

### Wait for ALL (with atomic removal)

Clears all specified bits atomically when all are received.

```c
uint32_t events;

events = k_event_wait_all_safe(&my_event, 0x121, false, K_MSEC(50));
/* All bits (0x121) are cleared if they were all set */
```

### Parameters

-   `event`: Pointer to event object.
-   `events`: Bitmask of events to wait for.
-   `reset`: If `true`, reset ALL events to 0 before waiting (use with care in multi-waiter scenarios).
-   `timeout`: `K_FOREVER`, `K_NO_WAIT`, or `K_MSEC(n)`.

## Use Patterns

### Pattern 1: Multiple Interrupt Sources

Signal a thread about multiple hardware events.

```c
#define EVENT_UART_RX  BIT(0)
#define EVENT_UART_TX  BIT(1)
#define EVENT_GPIO     BIT(2)
#define EVENT_TIMER    BIT(3)

K_EVENT_DEFINE(hw_events);

void uart_rx_isr(void *arg) { k_event_post(&hw_events, EVENT_UART_RX); }
void uart_tx_isr(void *arg) { k_event_post(&hw_events, EVENT_UART_TX); }
void gpio_isr(void *arg)    { k_event_post(&hw_events, EVENT_GPIO); }
void timer_isr(void *arg)   { k_event_post(&hw_events, EVENT_TIMER); }

void event_handler_thread(void)
{
    while (1) {
        uint32_t events = k_event_wait_safe(&hw_events, 0xF, false, K_FOREVER);

        if (events & EVENT_UART_RX) { handle_uart_rx(); }
        if (events & EVENT_UART_TX) { handle_uart_tx(); }
        if (events & EVENT_GPIO)    { handle_gpio(); }
        if (events & EVENT_TIMER)   { handle_timer(); }
    }
}
```

### Pattern 2: State Machine with Multiple Conditions

Wait for a specific combination of conditions.

```c
#define STATE_INITIALIZED BIT(0)
#define STATE_CONFIGURED  BIT(1)
#define STATE_CONNECTED   BIT(2)

K_EVENT_DEFINE(system_state);

void initialization_complete(void)
{
    k_event_post(&system_state, STATE_INITIALIZED);
}

void configuration_loaded(void)
{
    k_event_post(&system_state, STATE_CONFIGURED);
}

void network_connected(void)
{
    k_event_post(&system_state, STATE_CONNECTED);
}

void main_application(void)
{
    /* Wait for system to be fully ready (all three conditions) */
    k_event_wait_all(&system_state,
                     STATE_INITIALIZED | STATE_CONFIGURED | STATE_CONNECTED,
                     false, K_FOREVER);

    /* System is ready, start main loop */
    run_application();
}
```

### Pattern 3: Broadcast to Multiple Threads

Multiple threads wait for the same event.

```c
K_EVENT_DEFINE(shutdown_event);
#define SHUTDOWN_REQUESTED BIT(0)

void request_shutdown(void)
{
    k_event_post(&shutdown_event, SHUTDOWN_REQUESTED);
}

void worker_thread_1(void)
{
    while (1) {
        /* Check for shutdown, non-blocking */
        if (k_event_wait(&shutdown_event, SHUTDOWN_REQUESTED, false, K_NO_WAIT)) {
            break;  /* Shutdown requested */
        }
        do_work_1();
    }
    cleanup_1();
}

void worker_thread_2(void)
{
    while (1) {
        if (k_event_wait(&shutdown_event, SHUTDOWN_REQUESTED, false, K_NO_WAIT)) {
            break;
        }
        do_work_2();
    }
    cleanup_2();
}
```

### Pattern 4: Producer-Consumer with Status Flags

```c
#define DATA_AVAILABLE BIT(0)
#define BUFFER_FULL    BIT(1)

K_EVENT_DEFINE(buffer_status);

void producer(void)
{
    while (1) {
        /* Wait for buffer to have space */
        if (k_event_wait(&buffer_status, BUFFER_FULL, false, K_NO_WAIT) == 0) {
            produce_data();
            k_event_post(&buffer_status, DATA_AVAILABLE);
        } else {
            k_sleep(K_MSEC(10));  /* Buffer full, wait */
        }
    }
}

void consumer(void)
{
    while (1) {
        k_event_wait_safe(&buffer_status, DATA_AVAILABLE, false, K_FOREVER);
        consume_data();
        /* Clear BUFFER_FULL if buffer now has space */
        if (buffer_has_space()) {
            uint32_t current = k_event_test(&buffer_status);
            k_event_set(&buffer_status, current & ~BUFFER_FULL);
        }
    }
}
```

## ISR Usage

-   **Posting/Setting from ISR:** Always safe. These operations never block.
-   **Waiting from ISR:** Forbidden. ISRs cannot block.

```c
void my_isr(void *arg)
{
    /* Safe: post from ISR */
    k_event_post(&my_event, EVENT_FLAG);

    /* Safe: set from ISR */
    k_event_set(&my_event, NEW_STATE);

    /* Safe: query events (non-blocking) */
    uint32_t current = k_event_test(&my_event);

    /* FORBIDDEN: waiting in ISR */
    /* k_event_wait(&my_event, 0xFFF, false, K_FOREVER);  // NEVER DO THIS */
}
```

## Common Pitfalls

### 1. Using `reset=true` with Multiple Waiters

**Problem:** One thread resets events, causing other threads to miss them.

```c
/* Thread A */
k_event_wait(&events, MASK_A, true, K_FOREVER);  /* Resets ALL events */

/* Thread B - may miss events that Thread A reset */
k_event_wait(&events, MASK_B, true, K_FOREVER);
```

**Solution:** Use `reset=false` and clear events explicitly with `_safe` variants.

### 2. Race Condition: Check-Then-Act

**Problem:** Events change between query and action.

```c
/* Thread */
uint32_t e = k_event_test(&events);
if (e & MY_EVENT) {
    /* Event might be cleared by another thread here! */
    handle_event();
}
```

**Solution:** Use `k_event_wait_safe()` for atomic check-and-clear.

### 3. Waiting in ISR

**Problem:** ISRs cannot block.

```c
void isr_handler(void *arg)
{
    /* CRASH: Cannot wait in ISR */
    k_event_wait(&events, MASK, false, K_FOREVER);
}
```

**Solution:** Use `k_event_test()` in ISRs for non-blocking queries.

### 4. Event Loss with Post

**Problem:** Posting the same bit multiple times has no cumulative effect.

```c
k_event_post(&events, BIT(0));  /* Bit 0 set */
k_event_post(&events, BIT(0));  /* Still just bit 0 set - second post is "lost" */
/* Consumer only sees one event */
```

**Solution:** For counting events, use semaphores or message queues instead.

### 5. Forgetting to Enable Events

**Problem:** Events require Kconfig to be enabled.

```
# prj.conf
CONFIG_EVENTS=y
```

Without this, event APIs are not available.
