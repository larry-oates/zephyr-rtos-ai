# ISR API Reference

## Table of Contents

1. [Registration Macros](#registration-macros)
2. [Direct ISR Macros](#direct-isr-macros)
3. [IRQ Control Functions](#irq-control-functions)
4. [Interrupt Locking](#interrupt-locking)
5. [Context Detection](#context-detection)
6. [Kconfig Options](#kconfig-options)
7. [Header Files](#header-files)

## Registration Macros

### IRQ_CONNECT

Register an ISR at build time.

```c
IRQ_CONNECT(irq_p, priority_p, isr_p, isr_param_p, flags_p)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `irq_p` | `unsigned int` | IRQ line number (must be compile-time constant) |
| `priority_p` | `unsigned int` | Interrupt priority (arch-specific) |
| `isr_p` | `void (*)(const void *)` | ISR function pointer |
| `isr_param_p` | `const void *` | Argument passed to ISR |
| `flags_p` | `uint32_t` | Architecture-specific flags |

**Constraints:**
- All arguments **must** be compile-time constants
- Does not enable the interrupt; call `irq_enable()` after

**Example:**
```c
#define MY_IRQ  24
#define MY_PRIO 2

void my_isr(const void *arg) { /* handler */ }

void setup(void)
{
    IRQ_CONNECT(MY_IRQ, MY_PRIO, my_isr, NULL, 0);
    irq_enable(MY_IRQ);
}
```

### irq_connect_dynamic

Register an ISR at runtime.

```c
int irq_connect_dynamic(unsigned int irq,
                        unsigned int priority,
                        void (*routine)(const void *parameter),
                        const void *parameter,
                        uint32_t flags);
```

**Returns:** The interrupt vector assigned, or negative error code.

**Requires:** `CONFIG_DYNAMIC_INTERRUPTS=y`

**Example:**
```c
void my_isr(const void *arg) { /* handler */ }

void setup(unsigned int runtime_irq)
{
    int vec = irq_connect_dynamic(runtime_irq, 2, my_isr, NULL, 0);
    if (vec < 0) {
        /* Error handling */
    }
    irq_enable(runtime_irq);
}
```

### irq_disconnect_dynamic

Disconnect a dynamically registered ISR.

```c
int irq_disconnect_dynamic(unsigned int irq,
                           unsigned int priority,
                           void (*routine)(const void *parameter),
                           const void *parameter,
                           uint32_t flags);
```

**Returns:** 0 on success, negative error code on failure.

**Requires:** `CONFIG_DYNAMIC_INTERRUPTS=y` and `CONFIG_SHARED_INTERRUPTS=y`

## Direct ISR Macros

### IRQ_DIRECT_CONNECT

Register a direct ISR at build time (lowest latency).

```c
IRQ_DIRECT_CONNECT(irq_p, priority_p, isr_p, flags_p)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `irq_p` | `unsigned int` | IRQ line number |
| `priority_p` | `unsigned int` | Interrupt priority |
| `isr_p` | function | Direct ISR (declared with `ISR_DIRECT_DECLARE`) |
| `flags_p` | `uint32_t` | Flags (e.g., `IRQ_ZERO_LATENCY`) |

**Differences from regular ISR:**
- No argument passed to ISR
- No automatic stack switch (unless HW does it)
- No automatic PM idle exit
- Scheduling decision controlled by return value

### ISR_DIRECT_DECLARE

Declare a direct ISR handler.

```c
ISR_DIRECT_DECLARE(name)
{
    /* ISR body */
    ISR_DIRECT_PM();  /* Optional: PM idle exit */
    return 1;         /* 1 = reschedule check, 0 = skip */
}
```

**Return value:**
- `0` - Skip scheduling decision (use for zero-latency)
- `1` - Check if rescheduling is needed

### ISR_DIRECT_HEADER / ISR_DIRECT_FOOTER

Architecture-specific setup/teardown (used internally by `ISR_DIRECT_DECLARE`).

```c
#define ISR_DIRECT_HEADER()            ARCH_ISR_DIRECT_HEADER()
#define ISR_DIRECT_FOOTER(check_resched) ARCH_ISR_DIRECT_FOOTER(check_resched)
```

### ISR_DIRECT_PM

Power management idle exit hook.

```c
ISR_DIRECT_PM()
```

**Warning:** Must NOT be used in zero-latency ISRs.

## IRQ Control Functions

### irq_enable

Enable an IRQ line.

```c
#define irq_enable(irq) arch_irq_enable(irq)
```

### irq_disable

Disable an IRQ line.

```c
#define irq_disable(irq) arch_irq_disable(irq)
```

### irq_is_enabled

Check if an IRQ is enabled.

```c
#define irq_is_enabled(irq) arch_irq_is_enabled(irq)
```

**Returns:** `true` if enabled, `false` otherwise.

## Interrupt Locking

### irq_lock

Lock all interrupts (disable globally).

```c
unsigned int irq_lock(void);
```

**Returns:** Lock-out key (opaque value).

**Notes:**
- Can be called recursively
- Each `irq_lock()` must be matched with `irq_unlock()`
- IRQ lock is thread-specific (released on context switch)
- Holding IRQ lock during context switch is illegal

**Example:**
```c
unsigned int key = irq_lock();
/* Critical section - no interrupts */
irq_unlock(key);
```

### irq_unlock

Unlock interrupts (restore previous state).

```c
void irq_unlock(unsigned int key);
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `key` | `unsigned int` | Lock-out key from `irq_lock()` |

**Example (nested locking):**
```c
unsigned int key1 = irq_lock();
/* ... */
unsigned int key2 = irq_lock();  /* Nested */
/* ... */
irq_unlock(key2);  /* Restore to key1 state */
/* ... */
irq_unlock(key1);  /* Fully unlocked */
```

## Context Detection

### k_is_in_isr

Detect if currently executing in ISR context.

```c
bool k_is_in_isr(void);
```

**Returns:** `true` if in ISR context, `false` if in thread context.

**Example:**
```c
void my_function(void)
{
    if (k_is_in_isr()) {
        /* Non-blocking path */
        k_sem_give(&sem);
    } else {
        /* Can block */
        k_sem_take(&sem, K_FOREVER);
    }
}
```

## Kconfig Options

| Option | Description | Default |
|--------|-------------|---------|
| `CONFIG_ISR_STACK_SIZE` | Interrupt stack size in bytes | Arch-dependent |
| `CONFIG_DYNAMIC_INTERRUPTS` | Enable runtime ISR registration | n |
| `CONFIG_SHARED_INTERRUPTS` | Allow multiple ISRs per IRQ line | n |
| `CONFIG_SHARED_IRQ_MAX_NUM_CLIENTS` | Max ISRs per shared IRQ | 2 |
| `CONFIG_ZERO_LATENCY_IRQS` | Enable zero-latency interrupts | n |
| `CONFIG_GEN_IRQ_VECTOR_TABLE` | Generate interrupt vector table | y |
| `CONFIG_MULTI_LEVEL_INTERRUPTS` | Enable nested interrupt controllers | n |
| `CONFIG_2ND_LEVEL_INTERRUPTS` | Enable 2nd level interrupts | n |
| `CONFIG_3RD_LEVEL_INTERRUPTS` | Enable 3rd level interrupts | n |
| `CONFIG_SRAM_VECTOR_TABLE` | Place vector table in RAM | n |

## Header Files

| Header | Contents |
|--------|----------|
| `<zephyr/irq.h>` | Main IRQ API (`IRQ_CONNECT`, `irq_lock`, etc.) |
| `<zephyr/kernel.h>` | `k_is_in_isr()` |
| `<zephyr/arch/<arch>/irq.h>` | Architecture-specific IRQ definitions |
| `<zephyr/sw_isr_table.h>` | Software ISR table structures |
