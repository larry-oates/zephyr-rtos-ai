# ISR Types

## Table of Contents

1. [Regular ISRs](#regular-isrs)
2. [Direct ISRs](#direct-isrs)
3. [Dynamic ISRs](#dynamic-isrs)
4. [Comparison](#comparison)

## Regular ISRs

Standard interrupt handlers registered at build time. Most common choice.

### When to Use

- Arguments known at compile time
- Don't need ultra-low latency
- Need to pass data to ISR via argument

### Implementation

```c
#include <zephyr/irq.h>

#define DEVICE_IRQ    24
#define DEVICE_PRIO   2

struct device_data {
    volatile uint32_t count;
    struct k_sem ready;
};

static struct device_data my_data;

/* ISR handler - receives argument */
void device_isr(const void *arg)
{
    struct device_data *data = (struct device_data *)arg;
    data->count++;
    k_sem_give(&data->ready);
}

/* Registration and setup */
void device_init(void)
{
    k_sem_init(&my_data.ready, 0, 1);

    /* Register at build time - all args must be constants */
    IRQ_CONNECT(DEVICE_IRQ, DEVICE_PRIO, device_isr, &my_data, 0);

    /* Enable the interrupt */
    irq_enable(DEVICE_IRQ);
}
```

### What Happens Behind the Scenes

1. ISR address placed in vector table (or SW ISR table)
2. When IRQ fires:
   - Kernel saves context
   - Switches to interrupt stack
   - Retrieves ISR and argument from table
   - Calls ISR with argument
   - On return, checks for reschedule
   - Restores context

## Direct ISRs

Minimal-overhead handlers for latency-critical interrupts.

### When to Use

- Latency is critical (e.g., motor control, high-speed sampling)
- Don't need ISR argument
- Can handle stack/context manually
- Zero-latency interrupts (ARM Cortex-M)

### Implementation

```c
#include <zephyr/irq.h>

#define FAST_IRQ      24
#define FAST_PRIO     1

/* Direct ISR - no argument, minimal overhead */
ISR_DIRECT_DECLARE(fast_isr)
{
    /* Minimal work here */
    volatile uint32_t *reg = (uint32_t *)0x40001000;
    *reg = 0x01;  /* Acknowledge HW */

    /* Optional: PM idle exit (NOT for zero-latency) */
    ISR_DIRECT_PM();

    /* Return value:
     * 0 = skip reschedule check (fastest, use for ZLI)
     * 1 = check if reschedule needed
     */
    return 1;
}

void fast_device_init(void)
{
    /* Direct registration - no argument parameter */
    IRQ_DIRECT_CONNECT(FAST_IRQ, FAST_PRIO, fast_isr, 0);
    irq_enable(FAST_IRQ);
}
```

### Direct ISR Limitations

- **No argument passed** - Can't use ISR parameter
- **No automatic stack switch** - Uses interrupted context's stack (unless HW does it)
- **No automatic PM handling** - Must call `ISR_DIRECT_PM()` manually
- **Interrupts may stay locked** - Depends on architecture
- **Return value matters** - Controls scheduling behavior

### Zero-Latency Direct ISR (ARM Cortex-M)

```c
#include <zephyr/irq.h>

#define ZLI_IRQ       24
#define ZLI_PRIO      0  /* Highest priority */

/* Zero-latency ISR - bypasses irq_lock() */
ISR_DIRECT_DECLARE(zero_latency_isr)
{
    /* Runs even when irq_lock() is held!
     * Must NOT use ANY kernel APIs
     * Must NOT call ISR_DIRECT_PM()
     * Must return 0 (no reschedule)
     */
    volatile uint32_t *reg = (uint32_t *)0x40001000;
    *reg = 0x01;

    return 0;  /* MUST be 0 for ZLI */
}

void zli_init(void)
{
    /* IRQ_ZERO_LATENCY flag enables ZLI */
    IRQ_DIRECT_CONNECT(ZLI_IRQ, ZLI_PRIO, zero_latency_isr, IRQ_ZERO_LATENCY);
    irq_enable(ZLI_IRQ);
}
```

**Zero-Latency Constraints:**
- ARM Cortex-M only
- Requires `CONFIG_ZERO_LATENCY_IRQS=y`
- No kernel API calls allowed
- No `ISR_DIRECT_PM()` allowed
- Must return 0
- Cannot modify kernel-inspected data

## Dynamic ISRs

ISRs registered at runtime when IRQ number or arguments aren't known at build time.

### When to Use

- IRQ number determined at runtime (e.g., from devicetree)
- Multiple device instances sharing ISR code
- Plug-and-play devices
- Need to disconnect/reconnect ISRs

### Implementation

```c
#include <zephyr/irq.h>

struct dyn_device {
    unsigned int irq;
    void *hw_base;
    volatile uint32_t event_count;
};

/* Shared ISR for multiple instances */
void dyn_device_isr(const void *arg)
{
    struct dyn_device *dev = (struct dyn_device *)arg;
    dev->event_count++;
    /* Clear interrupt at dev->hw_base */
}

int dyn_device_init(struct dyn_device *dev, unsigned int irq, void *base)
{
    dev->irq = irq;
    dev->hw_base = base;
    dev->event_count = 0;

    /* Runtime registration */
    int vec = irq_connect_dynamic(irq, 2, dyn_device_isr, dev, 0);
    if (vec < 0) {
        return vec;  /* Error */
    }

    irq_enable(irq);
    return 0;
}

void dyn_device_shutdown(struct dyn_device *dev)
{
    irq_disable(dev->irq);

    /* Disconnect (requires CONFIG_SHARED_INTERRUPTS) */
    irq_disconnect_dynamic(dev->irq, 2, dyn_device_isr, dev, 0);
}
```

### Dynamic ISR Requirements

- `CONFIG_DYNAMIC_INTERRUPTS=y`
- For disconnect: `CONFIG_SHARED_INTERRUPTS=y`
- Slight runtime overhead vs static registration

## Comparison

| Feature | Regular | Direct | Dynamic |
|---------|---------|--------|---------|
| Registration | Build-time | Build-time | Runtime |
| ISR Argument | Yes | No | Yes |
| Stack Switch | Automatic | Manual/HW | Automatic |
| PM Handling | Automatic | Manual | Automatic |
| Latency | Normal | Lowest | Normal |
| Zero-Latency Support | No | Yes | No |
| Disconnect Support | No | No | Yes* |
| Use Case | General | Time-critical | Flexible |

*Requires `CONFIG_SHARED_INTERRUPTS`

### Decision Flowchart

```
┌─────────────────────────────────────────┐
│ Need to handle hardware interrupt?       │
└─────────────────────┬───────────────────┘
                      │
        ┌─────────────▼─────────────┐
        │ IRQ known at compile time? │
        └─────────────┬─────────────┘
                      │
          ┌───────────┴───────────┐
          │                       │
         Yes                      No
          │                       │
          ▼                       ▼
┌─────────────────────┐   ┌─────────────────────┐
│ Need ultra-low      │   │ Use Dynamic ISR     │
│ latency?            │   │ irq_connect_dynamic │
└─────────┬───────────┘   └─────────────────────┘
          │
    ┌─────┴─────┐
    │           │
   Yes          No
    │           │
    ▼           ▼
┌─────────┐  ┌─────────────────────┐
│ Direct  │  │ Use Regular ISR     │
│ ISR     │  │ IRQ_CONNECT         │
└─────────┘  └─────────────────────┘
```
