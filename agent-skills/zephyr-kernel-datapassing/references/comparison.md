# Data Passing Object Comparison

## Quick Reference Table

| Object | Bidirectional? | Data structure | Data item size | Data Alignment | ISRs can receive? | ISRs can send? | Overrun handling |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **FIFO** | No | Queue | Arbitrary | 4 B | Yes (No Wait) | Yes | N/A |
| **LIFO** | No | Queue | Arbitrary | 4 B | Yes (No Wait) | Yes | N/A |
| **Stack** | No | Array | Word | Word | Yes (No Wait) | Yes | Undefined behavior |
| **Message queue** | No | Ring buffer | Arbitrary | Power of two | Yes (No Wait) | Yes | Pend thread or return -errno |
| **Mailbox** | Yes | Queue | Arbitrary | Arbitrary | No | No | N/A |
| **Pipe** | No | Ring buffer (Optional) | Arbitrary | Arbitrary | Yes (No Wait) | Yes (No Wait) | Pend thread or return -errno |
| **ZBus** | No (Pub/Sub) | Channel | Arbitrary | Arbitrary | Yes (Publish) | Yes | Overwrites previous value |
| **Ring Buffer** | No | Circular array | Byte stream | None | Yes | Yes | Partial write / drop |

## Selection Guide

### FIFO (First-In, First-Out)
*   **Use when**: You need to transfer data items of arbitrary size asynchronously in a FIFO manner.
*   **Pros**: Simple, efficient for processing data in order of arrival.
*   **Cons**: Requires callers to allocate space for queue overhead in data elements (unless using `k_fifo_alloc_put`).
*   **Avoid when**: You need fixed-size messages with built-in buffering (use Message Queue).

### LIFO (Last-In, First-Out)
*   **Use when**: You need to transfer data items of arbitrary size asynchronously in a LIFO manner.
*   **Pros**: Good for "undo" operations or processing most recent data first.
*   **Cons**: Same allocation constraints as FIFO.
*   **Avoid when**: Order of arrival matters (use FIFO).

### Stack
*   **Use when**: You need to transfer integer-sized data items in a LIFO manner.
*   **Pros**: Very low overhead, simple array-based implementation.
*   **Cons**: Fixed data size (machine word), potential for undefined behavior on overrun.
*   **Avoid when**: You need arbitrary-sized data (use LIFO) or FIFO ordering.

### Message Queue
*   **Use when**: You need to transfer small, fixed-size data items asynchronously.
*   **Pros**: Ring buffer implementation avoids dynamic allocation per item. Can peek at data.
*   **Cons**: Data is copied (memcpy), so large items increase latency.
*   **Avoid when**: Data items are large (use FIFO with pointers or Mailbox).

### Mailbox
*   **Use when**: You need enhanced capabilities beyond a message queue, such as:
    *   Synchronous transfer (block until received).
    *   Variable-sized messages.
    *   Bidirectional exchange (sender gets info back).
    *   Flow control.
*   **Pros**: Very flexible, supports "empty" signals and huge data transfers (by reference).
*   **Cons**: Heavier weight, ISRs cannot participate.
*   **Avoid when**: ISRs are involved or you need simple async transfer.

### Pipe
*   **Use when**: You need to send a byte stream (chunks of data) between threads.
*   **Pros**: Handles partial reads/writes, ideal for stream processing (e.g., UART data).
*   **Cons**: More complex than simple queues.
*   **Avoid when**: You need discrete messages (use Message Queue).

### ZBus (Zephyr Bus)
*   **Use when**:
    *   Decoupled, event-driven architecture.
    *   One-to-many or many-to-many communication.
    *   Broadcasting state changes to multiple subscribers.
*   **Pros**: Loose coupling, flexible observer patterns, supports listeners and message subscribers.
*   **Cons**: Higher overhead, subscribers may miss intermediate values (only latest retained).
*   **Avoid when**: You need guaranteed delivery of every message (use Message Queue).
*   **Details**: [references/zbus.md](zbus.md)

### Ring Buffer
*   **Use when**:
    *   Low-level byte stream buffering (drivers, protocol parsing).
    *   Performance-critical paths needing zero-copy access.
    *   ISR-to-thread data passing with manual synchronization.
*   **Pros**: Minimal overhead, zero-copy claim/finish API, SPSC lock-free.
*   **Cons**: No built-in blocking (must pair with semaphore/event), not thread-safe for MPMC.
*   **Avoid when**: You need kernel-managed blocking (use Pipe).
*   **Details**: [references/ring_buffer.md](ring_buffer.md)

## Decision Flowchart

```
Need to pass data between threads/ISRs?
│
├─ Is it a byte stream (not discrete messages)?
│  ├─ Yes, need kernel blocking → Pipe
│  └─ Yes, need minimal overhead → Ring Buffer + Semaphore
│
├─ Is it pub/sub (1:N, N:1, event-driven)?
│  └─ Yes → ZBus
│
├─ Fixed-size messages?
│  ├─ Yes, small items → Message Queue
│  └─ Yes, but large or need zero-copy → FIFO with pointers
│
├─ Variable-size messages?
│  ├─ Need bidirectional / sync → Mailbox
│  └─ Async, arbitrary order → FIFO or LIFO
│
├─ Integer values only (machine word)?
│  └─ Yes, LIFO order → Stack
│
└─ Processing order?
   ├─ First-in, first-out → FIFO
   └─ Last-in, first-out → LIFO
```
