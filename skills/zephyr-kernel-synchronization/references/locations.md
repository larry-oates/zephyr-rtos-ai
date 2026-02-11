# Resource Locations

Paths to documentation, source code, headers, and samples for Zephyr synchronization primitives.

*Note: `<zephyr-ws>` represents the root of the Zephyr workspace.*

## Documentation

| Resource | Path |
| :--- | :--- |
| **Synchronization Overview** | `<zephyr-ws>/deps/zephyr/doc/kernel/services/synchronization/` |
| **Semaphores Doc** | `<zephyr-ws>/deps/zephyr/doc/kernel/services/synchronization/semaphores.rst` |
| **Mutexes Doc** | `<zephyr-ws>/deps/zephyr/doc/kernel/services/synchronization/mutexes.rst` |
| **Events Doc** | `<zephyr-ws>/deps/zephyr/doc/kernel/services/synchronization/events.rst` |
| **Condition Variables Doc** | `<zephyr-ws>/deps/zephyr/doc/kernel/services/synchronization/condvar.rst` |

## Header Files

| Resource | Path |
| :--- | :--- |
| **Main Kernel Header** | `<zephyr-ws>/deps/zephyr/include/zephyr/kernel.h` |
| **Kernel Includes Dir** | `<zephyr-ws>/deps/zephyr/include/zephyr/kernel/` |

All synchronization primitives (`k_sem`, `k_mutex`, `k_event`, `k_condvar`) are declared in `kernel.h`.

## Kernel Source

| Resource | Path |
| :--- | :--- |
| **Semaphore Implementation** | `<zephyr-ws>/deps/zephyr/kernel/sem.c` |
| **Mutex Implementation** | `<zephyr-ws>/deps/zephyr/kernel/mutex.c` |
| **Events Implementation** | `<zephyr-ws>/deps/zephyr/kernel/events.c` |
| **Condition Variable Impl** | `<zephyr-ws>/deps/zephyr/kernel/condvar.c` |

## Samples

| Sample | Path | Description |
| :--- | :--- | :--- |
| **Synchronization** | `<zephyr-ws>/deps/zephyr/samples/synchronization/` | Basic semaphore ping-pong between threads |
| **Condition Variables** | `<zephyr-ws>/deps/zephyr/samples/kernel/condition_variables/` | Producer-consumer and simple condvar examples |
| **Philosophers** | `<zephyr-ws>/deps/zephyr/samples/philosophers/` | Classic dining philosophers with mutex/semaphore options |

### Sample Details

#### Synchronization Sample

Demonstrates thread synchronization using semaphores:

-   Two threads alternately print messages
-   Uses binary semaphores for handoff
-   Shows both static and dynamic thread creation

```
<zephyr-ws>/deps/zephyr/samples/synchronization/
├── CMakeLists.txt
├── prj.conf
├── sample.yaml
├── README.rst
└── src/
    └── main.c
```

#### Condition Variables Samples

Two examples demonstrating condition variables:

**condvar/** - Threshold notification pattern:
-   Multiple incrementer threads
-   One watcher thread waits for count threshold
-   Demonstrates `k_condvar_signal`

**simple/** - Worker completion tracking:
-   Multiple worker threads signal completion
-   Main thread waits for all workers
-   Demonstrates `k_condvar_wait` in a while loop

```
<zephyr-ws>/deps/zephyr/samples/kernel/condition_variables/
├── condvar/
│   └── src/main.c
└── simple/
    └── src/main.c
```

#### Philosophers Sample

Classic dining philosophers problem:

-   Configurable to use different synchronization primitives
-   Demonstrates deadlock avoidance (Dijkstra's solution)
-   Shows mutex vs semaphore trade-offs

```
<zephyr-ws>/deps/zephyr/samples/philosophers/
├── CMakeLists.txt
├── prj.conf
├── sample.yaml
├── README.rst
└── src/
    ├── main.c
    └── phil_obj_abstract.h  # Fork abstraction for different primitives
```

## Tests

| Resource | Path |
| :--- | :--- |
| **Kernel Tests** | `<zephyr-ws>/deps/zephyr/tests/kernel/` |
| **Semaphore Tests** | `<zephyr-ws>/deps/zephyr/tests/kernel/semaphore/` |
| **Mutex Tests** | `<zephyr-ws>/deps/zephyr/tests/kernel/mutex/` |
| **Events Tests** | `<zephyr-ws>/deps/zephyr/tests/kernel/events/` |
| **Condition Var Tests** | `<zephyr-ws>/deps/zephyr/tests/kernel/condvar/` |
