# Synchronization Primitives Comparison

## Quick Reference Table

| Feature | Semaphores | Mutexes | Events | Condition Variables |
| :--- | :--- | :--- | :--- | :--- |
| **Primary Purpose** | Counting resources, signaling | Mutual Exclusion (Locking) | Signaling multiple conditions (bitmask) | Waiting for complex state changes |
| **Ownership** | No (Anyone can Give/Take) | Yes (Only owner can Unlock) | No | No (but requires mutex) |
| **ISR Safe?** | Yes (Give always, Take w/ K_NO_WAIT) | No | Yes (Post/Set only, no Wait) | No |
| **Reentrant?** | No | Yes (same owner can lock multiple times) | N/A | N/A |
| **Priority Inheritance** | No | Yes | No | No (but mutex used with it has PI) |
| **Multiple Waiters** | Yes (Highest priority, longest wait first) | Yes (Highest priority, longest wait first) | Yes (All matching waiters released) | Yes (Signal one or Broadcast all) |
| **Data Passing** | No | No | Yes (32-bit bitmask) | No |
| **Kconfig Required** | No (always available) | No (always available) | Yes (`CONFIG_EVENTS=y`) | No (always available) |

## Key API Summary

| Primitive | Key Operations |
| :--- | :--- |
| **Semaphore** | `k_sem_init`, `k_sem_give`, `k_sem_take`, `k_sem_reset`, `k_sem_count_get` |
| **Mutex** | `k_mutex_init`, `k_mutex_lock`, `k_mutex_unlock` |
| **Events** | `k_event_init`, `k_event_post`, `k_event_set`, `k_event_wait`, `k_event_wait_all`, `k_event_wait_safe`, `k_event_wait_all_safe` |
| **Condition Variable** | `k_condvar_init`, `k_condvar_wait`, `k_condvar_signal`, `k_condvar_broadcast` |

## Selection Guide

### Use Semaphores When

-   **ISR-to-Thread signaling:** ISR needs to wake a thread (binary semaphore).
-   **Resource counting:** Limit concurrent access to N resources (counting semaphore).
-   **Simple thread synchronization:** One thread signals another.
-   **Gate/barrier:** Block threads until initialization completes.

**Avoid when:** You need mutual exclusion between threads of different priorities (use mutex for priority inheritance).

### Use Mutexes When

-   **Protecting shared data:** Exclusive access to variables, buffers, or data structures.
-   **Protecting hardware:** Only one thread should access a peripheral at a time.
-   **Priority-sensitive locking:** Threads of different priorities share a resource (priority inheritance prevents inversion).
-   **Reentrant locking needed:** Same thread may lock from nested function calls.

**Avoid when:** ISRs are involved (use semaphores) or you just need signaling (use semaphores or events).

### Use Events When

-   **Multiple conditions (bitmask):** Wait for any/all of several independent conditions.
-   **ISR posting multiple flags:** ISRs signal different event types to a single handler thread.
-   **Broadcast to multiple threads:** All threads waiting on a condition should wake.
-   **State machine with flags:** Track system state as a set of bits.

**Avoid when:** You need counting (semaphores), mutual exclusion (mutex), or complex state predicates (condvar).

### Use Condition Variables When

-   **Complex condition predicate:** Condition is more than simple flag (e.g., "queue not empty AND not shutdown").
-   **Producer-consumer patterns:** Wait for "data available" or "space available" states.
-   **Thread completion tracking:** Wait for N threads to reach a certain point.
-   **Barrier synchronization:** All threads must reach a point before any proceed.

**Avoid when:** ISRs are involved (use semaphores/events) or condition is a simple bitmask (use events).

## Decision Flowchart

```
Need thread/ISR synchronization?
│
├─ Is an ISR involved?
│  │
│  ├─ ISR needs to signal a thread?
│  │  └─ Semaphore (binary, k_sem_give from ISR)
│  │
│  ├─ ISR needs to set multiple flags?
│  │  └─ Events (k_event_post from ISR)
│  │
│  └─ ISR needs to receive a signal?
│     └─ Semaphore with K_NO_WAIT (polling)
│
├─ Need mutual exclusion (protect shared resource)?
│  │
│  ├─ Threads have different priorities?
│  │  └─ Mutex (priority inheritance)
│  │
│  └─ Simple exclusive access needed?
│     └─ Mutex
│
├─ Need to wait for condition/state change?
│  │
│  ├─ Condition is a bitmask of independent flags?
│  │  └─ Events
│  │
│  ├─ Condition is complex predicate (e.g., count > N)?
│  │  └─ Condition Variable + Mutex
│  │
│  └─ Just need to wait for a signal (no state)?
│     └─ Semaphore (binary)
│
├─ Need to limit concurrent access to N resources?
│  └─ Semaphore (counting, initial = N)
│
└─ Need thread-to-thread ping-pong synchronization?
   └─ Two Semaphores
```

## Common Mistakes

| Mistake | Problem | Solution |
| :--- | :--- | :--- |
| Semaphore for mutual exclusion | No priority inheritance → priority inversion | Use Mutex |
| Mutex in ISR | ISRs cannot block | Use Semaphore (K_NO_WAIT) |
| `if` instead of `while` with condvar | Spurious wakeups cause bugs | Always use `while` loop |
| Events without `CONFIG_EVENTS=y` | Compilation error | Add to prj.conf |
| Signaling condvar without mutex | Race condition | Always hold mutex when signaling |
| Forgetting to unlock mutex | Deadlock | Ensure all paths unlock |
| Multiple mutexes in different order | Deadlock | Lock in consistent order |

## Performance Considerations

| Primitive | Overhead | Best For |
| :--- | :--- | :--- |
| Semaphore | Lowest | Simple signaling, ISR interaction |
| Mutex | Low | Thread-only mutual exclusion |
| Events | Low-Medium | Multi-flag signaling |
| Condition Variable | Medium | Complex state waiting |

For high-frequency operations in performance-critical code, prefer semaphores. For correctness with priority-sensitive threads, prefer mutexes.
