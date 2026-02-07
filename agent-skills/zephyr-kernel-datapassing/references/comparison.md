# Data Passing Object Comparison

| Object | Bidirectional? | Data structure | Data item size | Data Alignment | ISRs can receive? | ISRs can send? | Overrun handling |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **FIFO** | No | Queue | Arbitrary | 4 B | Yes (No Wait) | Yes | N/A |
| **LIFO** | No | Queue | Arbitrary | 4 B | Yes (No Wait) | Yes | N/A |
| **Stack** | No | Array | Word | Word | Yes (No Wait) | Yes | Undefined behavior |
| **Message queue** | No | Ring buffer | Arbitrary | Power of two | Yes (No Wait) | Yes | Pend thread or return -errno |
| **Mailbox** | Yes | Queue | Arbitrary | Arbitrary | No | No | N/A |
| **Pipe** | No | Ring buffer (Optional) | Arbitrary | Arbitrary | Yes (No Wait) | Yes (No Wait) | Pend thread or return -errno |

## Selection Guide

### FIFO (First-In, First-Out)
*   **Use when**: You need to transfer data items of arbitrary size asynchronously in a FIFO manner.
*   **Pros**: Simple, efficient for processing data in order of arrival.
*   **Cons**: Requires callers to allocate space for queue overhead in data elements (unless using `k_fifo_alloc_put`).

### LIFO (Last-In, First-Out)
*   **Use when**: You need to transfer data items of arbitrary size asynchronously in a LIFO manner.
*   **Pros**: Good for "undo" operations or processing most recent data first.
*   **Cons**: Same allocation constraints as FIFO.

### Stack
*   **Use when**: You need to transfer integer-sized data items in a LIFO manner.
*   **Pros**: Very low overhead, simple array-based implementation.
*   **Cons**: Fixed data size (machine word), potential for undefined behavior on overrun.

### Message Queue
*   **Use when**: You need to transfer small, fixed-size data items asynchronously.
*   **Pros**: Ring buffer implementation avoids dynamic allocation per item. Can peek at data.
*   **Cons**: Data is copied (memcpy), so large items increase latency.

### Mailbox
*   **Use when**: You need enhanced capabilities beyond a message queue, such as:
    *   Synchronous transfer (block until received).
    *   Variable-sized messages.
    *   Bidirectional exchange (sender gets info back).
    *   Flow control.
*   **Pros**: Very flexible, supports "empty" signals and huge data transfers (by reference).
*   **Cons**: Heavier weight, ISRs cannot participate.

### Pipe
*   **Use when**: You need to send a byte stream (chunks of data) between threads.
*   **Pros**: Handles partial reads/writes, ideal for stream processing (e.g., UART data).
*   **Cons**: More complex than simple queues.
