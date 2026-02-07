---
name: zephyr-kernel-datapassing
description: Enhances the knowledge of an AI agent with all kernel objects that are used to pass data between threads and ISRs in Zephyr OS. Use this skill when you need to implement, explain, or debug data passing mechanisms (FIFO, LIFO, Stack, Message Queue, Mailbox, Pipe).
---

# Zephyr Kernel Data Passing

## Overview

This skill provides expert knowledge on Zephyr kernel objects used for data passing. It helps in selecting the right object for the task and provides implementation details.

## Workflow

### 1. Selection Strategy
To choose the correct kernel object, first determine the requirements:
*   **Participants**: Thread-to-Thread? ISR-to-Thread?
*   **Data Size**: Fixed small structure? Arbitrary size? Byte stream?
*   **Behavior**: FIFO? LIFO? Synchronous? Asynchronous?

**Step 1:** Read [references/comparison.md](references/comparison.md) to see the features, pros, and cons of each object type.

### 2. Implementation
Once the object is selected, use the implementation guide to write the code.

**Step 2:** Read [references/data_passing.md](references/data_passing.md) for:
*   API usage (Definition, Put, Get).
*   Code snippets.
*   Key concepts (Alignment, Allocation).

### 3. API & Further Reading
For specific header details or deep-dives into the source.

**Step 3:** Read [references/api.md](references/api.md) for header file locations.

## Source Locations

The following locations in the Zephyr codebase contain the source of truth for these objects.

| Description | Path |
| :--- | :--- |
| **Documentation** | `<zephyr-ws-dir>/zephyr/doc/kernel/services/data_passing` |
| **Comparison** | `<zephyr-ws-dir>/zephyr/doc/kernel/services/index.rst` |
| **Headers** | `<zephyr-ws-dir>//zephyr/include/zephyr/kernel.h` |
| **MsgQ Sample** | `<zephyr-ws-dir>/zephyr/samples/kernel/msg_queue` |
| **Philosophers Sample** | `<zephyr-ws-dir>/zephyr/samples/philosophers` |
