---
name: zephyr-kernel-synchronization
description: Expert guidance on Zephyr kernel synchronization primitives (Semaphores, Mutexes, Events, Condition Variables). Use when the user asks about locking, signaling, thread safety, synchronization, or choosing the right primitive in Zephyr.
---

# Zephyr Kernel Synchronization

## Overview

This skill provides expert knowledge on the four main synchronization primitives in the Zephyr kernel: Semaphores, Mutexes, Events, and Condition Variables.

## Choosing the Right Primitive

If you are unsure which primitive to use, or need to compare their features (ISR safety, ownership, priority inheritance), refer to the comparison guide:

-   **Comparison Guide:** [references/comparison.md](references/comparison.md)

## Detailed References

For specific implementation details, API usage, and concepts for each primitive:

-   **Semaphores:** [references/semaphores.md](references/semaphores.md) (Counting, signaling, basic locking)
-   **Mutexes:** [references/mutexes.md](references/mutexes.md) (Mutual exclusion, priority inheritance, ownership)
-   **Events:** [references/events.md](references/events.md) (Many-to-many signaling, bitmasks)
-   **Condition Variables:** [references/condvar.md](references/condvar.md) (Waiting for complex state changes)

## Resource Locations

For locations of relevant documentation, header files, and samples within the Zephyr workspace:

-   **Locations:** [references/locations.md](references/locations.md)
