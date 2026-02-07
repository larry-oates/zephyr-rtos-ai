# Events

An event object is a kernel object that implements traditional events.

## Concepts

-   **Bitmask:** A 32-bit value tracks which events have been delivered.
-   **Many-to-Many:** Multiple threads can wait for multiple events.
-   **Posting/Setting:**
    -   *Set*: Overwrite existing events.
    -   *Post*: Bitwise OR with existing events.
-   **Wait Options:** Wait for ALL requested bits or ANY requested bit.
-   **Reset:** Option to clear events after waiting.
-   **ISR Safe:** ISRs can post/set events, but cannot wait.

## Implementation

### Defining

```c
struct k_event my_event;
k_event_init(&my_event);
// OR
K_EVENT_DEFINE(my_event);
```

### Setting/Posting

```c
k_event_set(&my_event, 0x001); // Overwrite
k_event_post(&my_event, 0x120); // Bitwise OR
```

### Waiting

```c
uint32_t events;
// Wait for ANY of the bits (0xFFF). Don't reset.
events = k_event_wait(&my_event, 0xFFF, false, K_MSEC(50));

// Wait for ALL bits (0x121). Don't reset.
events = k_event_wait_all(&my_event, 0x121, false, K_MSEC(50));
```

### Waiting with Removal (Reset)

```c
// Wait and clear the events if received
events = k_event_wait_safe(&my_event, 0xFFF, false, K_MSEC(50));
```

## Suggested Uses

-   Indicate a set of conditions have occurred.
-   Pass small amounts of data (status flags) to multiple threads.
