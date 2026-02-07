# Synchronization Primitives Comparison

| Feature | Semaphores | Mutexes | Events | Condition Variables |
| :--- | :--- | :--- | :--- | :--- |
| **Primary Purpose** | Counting resources, signaling | Mutual Exclusion (Locking) | Signaling multiple conditions | Waiting for complex state changes |
| **Ownership** | No (Anyone can Give/Take) | Yes (Only owner can Unlock) | No | No |
| **ISR Safe?** | Yes (Give/Take no-wait) | No | Yes (Post/Set) | No (Wait needs mutex) |
| **Reentrant?** | No | Yes | N/A | N/A |
| **Priority Inheritance**| No | Yes | No | No |
| **Multiple Waiters** | Yes (Highest prio first) | Yes (Highest prio first) | Yes (All released if match) | Yes (Signal one or Broadcast all) |
| **Key API** | `k_sem_give`, `k_sem_take` | `k_mutex_lock`, `k_mutex_unlock` | `k_event_post`, `k_event_wait` | `k_condvar_wait`, `k_condvar_signal` |

## Summary Guidance

-   **Use Mutexes** when you need to protect a shared resource from concurrent access by threads.
-   **Use Semaphores** to signal between ISR/Thread or Thread/Thread, or to limit the number of concurrent accesses (counting).
-   **Use Events** when you have multiple conditions (bits) to wait for, or need to broadcast a simple status to multiple threads.
-   **Use Condition Variables** when threads need to wait for a specific state change in shared data protected by a mutex (e.g., "queue is not empty").
