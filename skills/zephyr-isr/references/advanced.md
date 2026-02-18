# Advanced ISR Features

## Table of Contents

1. [Zero-Latency Interrupts](#zero-latency-interrupts)
2. [Shared Interrupts](#shared-interrupts)
3. [Multi-Level Interrupts](#multi-level-interrupts)
4. [IRQ Locking Patterns](#irq-locking-patterns)
5. [RAM-Based Execution](#ram-based-execution)

## Zero-Latency Interrupts

Interrupts that bypass `irq_lock()` for guaranteed low latency.

### When to Use

- Hard real-time requirements (motor control, safety systems)
- Cannot tolerate latency from kernel critical sections
- Hardware timing constraints

### Architecture Support

Currently **ARM Cortex-M only**.

### Requirements

- `CONFIG_ZERO_LATENCY_IRQS=y`
- Must use `IRQ_DIRECT_CONNECT` with `IRQ_ZERO_LATENCY` flag
- ISR declared with `ISR_DIRECT_DECLARE`

### Implementation

```c
#include <zephyr/irq.h>

#define ZLI_IRQ       24
#define ZLI_PRIO      0   /* Typically highest priority */

/* Zero-latency ISR */
ISR_DIRECT_DECLARE(motor_control_isr)
{
    /* CRITICAL: No kernel API calls allowed! */

    /* Direct hardware manipulation only */
    volatile uint32_t *pwm_reg = (uint32_t *)0x40001000;
    volatile uint32_t *enc_reg = (uint32_t *)0x40002000;

    uint32_t encoder = *enc_reg;
    *pwm_reg = compute_pwm(encoder);

    /* Must return 0 - no reschedule check */
    return 0;
}

void setup(void)
{
    IRQ_DIRECT_CONNECT(ZLI_IRQ, ZLI_PRIO, motor_control_isr, IRQ_ZERO_LATENCY);
    irq_enable(ZLI_IRQ);
}
```

### Constraints (Critical!)

| Allowed | Forbidden |
|---------|-----------|
| Direct register access | Any kernel API |
| Pure computation | `k_sem_give()` |
| Inline assembly | `k_work_submit()` |
| Static variables | `printk()` |
| | Memory allocation |
| | `ISR_DIRECT_PM()` |

**Why:** ZLI runs at priority above kernel, so kernel data structures may be in inconsistent state.

### Communication with Threads

Use shared memory with atomic operations:

```c
#include <zephyr/sys/atomic.h>

static atomic_t zli_event_flag = ATOMIC_INIT(0);
static volatile uint32_t zli_data;

ISR_DIRECT_DECLARE(zli_isr)
{
    zli_data = read_hw();
    atomic_set(&zli_event_flag, 1);
    return 0;
}

void thread_check(void)
{
    if (atomic_cas(&zli_event_flag, 1, 0)) {
        /* Event occurred, process zli_data */
        uint32_t data = zli_data;
        process(data);
    }
}
```

## Shared Interrupts

Multiple ISRs on the same interrupt line.

### When to Use

- Hardware routes multiple devices to one IRQ
- DMA completion + peripheral event on same line
- Legacy hardware with limited IRQ lines

### Configuration

```conf
CONFIG_SHARED_INTERRUPTS=y
CONFIG_SHARED_IRQ_MAX_NUM_CLIENTS=4  # Max ISRs per line
```

### Static Sharing (Build-time)

```c
#define SHARED_IRQ    24
#define SHARED_PRIO   2

void dma_isr(const void *arg)
{
    if (dma_pending()) {
        handle_dma();
    }
}

void uart_isr(const void *arg)
{
    if (uart_pending()) {
        handle_uart();
    }
}

void setup(void)
{
    /* Both handlers registered to same IRQ */
    IRQ_CONNECT(SHARED_IRQ, SHARED_PRIO, dma_isr, NULL, 0);
    IRQ_CONNECT(SHARED_IRQ, SHARED_PRIO, uart_isr, NULL, 0);
    irq_enable(SHARED_IRQ);
}
```

### Dynamic Sharing (Runtime)

```c
void add_handler(unsigned int irq)
{
    irq_connect_dynamic(irq, 2, my_isr, my_arg, 0);
    /* Automatically becomes shared if ISR already exists */
}

void remove_handler(unsigned int irq)
{
    /* Requires CONFIG_DYNAMIC_INTERRUPTS + CONFIG_SHARED_INTERRUPTS */
    irq_disconnect_dynamic(irq, 2, my_isr, my_arg, 0);
}
```

### ISR Design for Shared Interrupts

Each ISR **must** check if its device caused the interrupt:

```c
void device_a_isr(const void *arg)
{
    struct device_a *dev = (struct device_a *)arg;

    /* Check interrupt source */
    if (!(dev->regs->status & IRQ_PENDING_FLAG)) {
        return;  /* Not our interrupt */
    }

    /* Handle our interrupt */
    dev->regs->status = IRQ_PENDING_FLAG;  /* Clear */
    handle_device_a_event(dev);
}
```

## Multi-Level Interrupts

Nested interrupt controllers (cascaded interrupts).

### When to Use

- SoC has more interrupt sources than CPU supports natively
- External interrupt controller chips
- Complex SoC designs

### Configuration

```conf
CONFIG_MULTI_LEVEL_INTERRUPTS=y
CONFIG_2ND_LEVEL_INTERRUPTS=y   # Enable second level
CONFIG_3RD_LEVEL_INTERRUPTS=y   # Enable third level (if needed)

# Bit allocation (must sum to <= 32)
CONFIG_1ST_LEVEL_INTERRUPT_BITS=8
CONFIG_2ND_LEVEL_INTERRUPT_BITS=8
CONFIG_3RD_LEVEL_INTERRUPT_BITS=8
```

### IRQ Number Encoding

```
                 Level 3    Level 2    Level 1
                 ┌──────┐   ┌──────┐   ┌──────┐
IRQ number:      │ 8 bits│   │ 8 bits│   │ 8 bits│
                 └──────┘   └──────┘   └──────┘
```

Example from Zephyr docs:
```
Device A on Level 1, line 4:     0x00000004
Device B on Level 2, line 2, parent Level 1 line 9:  0x00000302
Device D on Level 3, line 2, parent L2 line 5, parent L1 line 9:  0x00030609
```

### Usage

Multi-level IRQ numbers work transparently with standard APIs:

```c
/* IRQ number includes level encoding */
#define NESTED_DEVICE_IRQ  0x00000302  /* From devicetree */

void setup(void)
{
    IRQ_CONNECT(NESTED_DEVICE_IRQ, 2, my_isr, NULL, 0);
    irq_enable(NESTED_DEVICE_IRQ);
}
```

## IRQ Locking Patterns

### Basic Critical Section

```c
void safe_operation(void)
{
    unsigned int key = irq_lock();
    /* Critical section - no interrupts */
    shared_data++;
    irq_unlock(key);
}
```

### Nested Locking

```c
void outer_function(void)
{
    unsigned int key1 = irq_lock();
    /* Interrupts disabled */

    inner_function();  /* May also lock */

    irq_unlock(key1);
}

void inner_function(void)
{
    unsigned int key2 = irq_lock();  /* Nesting OK */
    /* Still disabled */
    irq_unlock(key2);  /* Restores to key1 state (still disabled) */
}
```

### IRQ Lock vs Disabling Specific IRQ

```c
/* Lock ALL interrupts (thread-specific) */
unsigned int key = irq_lock();
/* ... */
irq_unlock(key);

/* Disable ONE specific IRQ (system-wide) */
irq_disable(DEVICE_IRQ);
/* ... */
irq_enable(DEVICE_IRQ);
```

**Key difference:**
- `irq_lock()` is thread-specific; released on context switch
- `irq_disable()` is system-wide; persists across threads

### Thread Context Awareness

```c
void my_function(void)
{
    if (k_is_in_isr()) {
        /* ISR context - cannot hold lock across return */
        /* Use K_NO_WAIT for any blocking operations */
    } else {
        /* Thread context - can use irq_lock() */
        unsigned int key = irq_lock();
        critical_operation();
        irq_unlock(key);
    }
}
```

### Preventing Preemption

IRQ lock inhibits preemption while held:

```c
void atomic_sequence(void)
{
    unsigned int key = irq_lock();

    /* Thread A holds lock here */
    /* If higher-priority thread B becomes ready,
     * it won't run until after irq_unlock() */

    do_step_1();
    do_step_2();
    do_step_3();

    irq_unlock(key);
    /* Thread B may now preempt if ready */
}
```

## RAM-Based Execution

Relocate ISRs to RAM to avoid flash access latency.

### Configuration

```conf
CONFIG_SRAM_VECTOR_TABLE=y    # Vector table in RAM
CONFIG_SRAM_SW_ISR_TABLE=y    # SW ISR table in RAM
```

### Code Relocation

Use Zephyr's code relocation feature to place ISR code in RAM:

```c
/* In CMakeLists.txt or using attributes */
__ramfunc void fast_isr(const void *arg)
{
    /* This function runs from RAM */
}
```

Or via linker script / CMake configuration:

```cmake
# Relocate entire file to RAM
zephyr_code_relocate(FILES src/fast_handlers.c LOCATION SRAM)
```

### Trade-offs

| Benefit | Cost |
|---------|------|
| Faster ISR execution | More RAM usage |
| Consistent latency | Less flash for code |
| No flash wait states | Startup copy time |
