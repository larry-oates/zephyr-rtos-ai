# Zephyr Device Model

## Table of Contents

1. [Device Structure](#device-structure)
2. [Initialization Levels and Priorities](#initialization-levels-and-priorities)
3. [Device Definition Macros](#device-definition-macros)
4. [Power Management](#power-management)
5. [Device Dependencies](#device-dependencies)

---

## Device Structure

### The `struct device`

Every device in Zephyr is represented by a `struct device`:

```c
struct device {
    const char *name;           /* Device name (from DT or static) */
    const void *config;         /* Immutable configuration */
    const void *api;            /* Driver API function pointers */
    void *data;                 /* Mutable runtime data */
    /* Plus internal fields for PM, init state, etc. */
};
```

### Config vs Data

| Aspect | Config Structure | Data Structure |
|--------|------------------|----------------|
| Mutability | `const` - immutable | Mutable at runtime |
| Storage | Flash (ROM) | RAM |
| Contents | HW addresses, pins, IRQs | State, buffers, locks |
| Initialization | Compile-time | Runtime in init function |

### Example Structures

```c
/* Configuration - stored in flash */
struct mydriver_config {
    uint32_t base_addr;              /* Register base address */
    uint32_t irq_num;                /* IRQ number */
    const struct gpio_dt_spec reset; /* GPIO for reset pin */
    uint32_t clock_freq;             /* Clock frequency */
};

/* Runtime data - stored in RAM */
struct mydriver_data {
    struct k_sem lock;               /* Synchronization */
    uint8_t rx_buffer[256];          /* Receive buffer */
    volatile bool transfer_done;     /* Transfer complete flag */
    uint32_t error_count;            /* Error statistics */
};
```

---

## Initialization Levels and Priorities

### Initialization Levels

Devices initialize in a specific order based on levels:

| Level | Value | Description | Use Case |
|-------|-------|-------------|----------|
| `EARLY` | 0 | Before standard initialization | Architecture early init |
| `PRE_KERNEL_1` | 1 | No kernel services available | Interrupt controllers, clocks |
| `PRE_KERNEL_2` | 2 | After PRE_KERNEL_1 | Drivers depending on PRE_KERNEL_1 |
| `POST_KERNEL` | 3 | Kernel services available | Most drivers (recommended default) |
| `APPLICATION` | 4 | After kernel, before main() | Application-specific devices |

### Initialization Priority

Within each level, devices initialize by priority (0-99, lower = earlier):

```c
/* Priority constants in Kconfig */
CONFIG_KERNEL_INIT_PRIORITY_DEFAULT=40
CONFIG_KERNEL_INIT_PRIORITY_DEVICE=50
CONFIG_I2C_INIT_PRIORITY=50
CONFIG_GPIO_INIT_PRIORITY=40
CONFIG_SENSOR_INIT_PRIORITY=90
```

### Choosing Level and Priority

```
Initialization Order:

PRE_KERNEL_1     PRE_KERNEL_2        POST_KERNEL           APPLICATION
    │                 │                   │                     │
    ▼                 ▼                   ▼                     ▼
┌────────┐       ┌────────┐         ┌────────┐             ┌────────┐
│ Clock  │       │  Bus   │         │ Device │             │  App   │
│ GPIO   │──────▶│  I2C   │────────▶│ Sensor │────────────▶│ Custom │
│ IRQ    │       │  SPI   │         │ Display│             │        │
└────────┘       └────────┘         └────────┘             └────────┘
```

**Rules:**
1. Clocks, GPIO controllers, interrupt controllers → `PRE_KERNEL_1`
2. Bus controllers (I2C, SPI, UART) → `PRE_KERNEL_2` or early `POST_KERNEL`
3. Bus devices (sensors, displays) → `POST_KERNEL`
4. Within a level, parent devices need lower priority than children

---

## Device Definition Macros

### DEVICE_DT_DEFINE

For defining a device from a specific devicetree node:

```c
DEVICE_DT_DEFINE(node_id,       /* DT node identifier */
                 init_fn,        /* Initialization function */
                 pm,             /* PM device pointer (or NULL) */
                 data,           /* Pointer to data structure */
                 config,         /* Pointer to config structure */
                 level,          /* Initialization level */
                 prio,           /* Initialization priority */
                 api);           /* Driver API pointer */
```

### DEVICE_DT_INST_DEFINE

For multi-instance drivers using `DT_DRV_COMPAT`:

```c
#define DT_DRV_COMPAT vendor_device

#define MYDRIVER_INIT(inst)                                       \
    static struct mydriver_data data_##inst;                      \
    static const struct mydriver_config config_##inst = {         \
        .base_addr = DT_INST_REG_ADDR(inst),                      \
        .irq_num = DT_INST_IRQN(inst),                            \
    };                                                            \
    DEVICE_DT_INST_DEFINE(inst,                                   \
                          mydriver_init,                          \
                          NULL,                                   \
                          &data_##inst,                           \
                          &config_##inst,                         \
                          POST_KERNEL,                            \
                          CONFIG_MYDRIVER_INIT_PRIORITY,          \
                          &mydriver_api);

DT_INST_FOREACH_STATUS_OKAY(MYDRIVER_INIT)
```

### DEVICE_DEFINE

For non-devicetree devices (rare, avoid if possible):

```c
DEVICE_DEFINE(name,             /* C identifier for device */
              "device_name",    /* Device name string */
              init_fn,
              pm,
              data,
              config,
              level,
              prio,
              api);
```

---

## Power Management

### PM Device Structure

Enable with `CONFIG_PM_DEVICE=y`:

```c
#include <zephyr/pm/device.h>

/* PM action callback */
static int mydriver_pm_action(const struct device *dev,
                              enum pm_device_action action)
{
    switch (action) {
    case PM_DEVICE_ACTION_SUSPEND:
        /* Save state, disable HW */
        return 0;
    case PM_DEVICE_ACTION_RESUME:
        /* Restore state, enable HW */
        return 0;
    default:
        return -ENOTSUP;
    }
}

/* Define PM device */
PM_DEVICE_DT_INST_DEFINE(inst, mydriver_pm_action);

/* Use in DEVICE_DT_INST_DEFINE */
DEVICE_DT_INST_DEFINE(inst,
                      mydriver_init,
                      PM_DEVICE_DT_INST_GET(inst),  /* PM pointer */
                      &data,
                      &config,
                      POST_KERNEL,
                      CONFIG_MYDRIVER_INIT_PRIORITY,
                      &mydriver_api);
```

### PM Device Actions

| Action | Description |
|--------|-------------|
| `PM_DEVICE_ACTION_SUSPEND` | Device going to low power |
| `PM_DEVICE_ACTION_RESUME` | Device returning from low power |
| `PM_DEVICE_ACTION_TURN_OFF` | Device being turned off |
| `PM_DEVICE_ACTION_TURN_ON` | Device being turned on |

### Application PM Control

```c
#include <zephyr/pm/device.h>

/* Suspend a device */
pm_device_action_run(dev, PM_DEVICE_ACTION_SUSPEND);

/* Resume a device */
pm_device_action_run(dev, PM_DEVICE_ACTION_RESUME);

/* Check device state */
enum pm_device_state state;
pm_device_state_get(dev, &state);
```

---

## Device Dependencies

### Implicit Dependencies via Devicetree

Zephyr automatically handles dependencies based on devicetree hierarchy:

```dts
/* Parent bus initializes before child device */
&i2c0 {
    status = "okay";

    sensor@48 {
        compatible = "vendor,sensor";
        reg = <0x48>;
        /* Implicitly depends on i2c0 */
    };
};
```

### Checking Parent Readiness

```c
static int sensor_init(const struct device *dev)
{
    const struct sensor_config *cfg = dev->config;

    /* Check bus is ready before using */
    if (!i2c_is_ready_dt(&cfg->i2c)) {
        return -ENODEV;
    }

    /* Now safe to use I2C */
    return 0;
}
```

### Manual Dependency Handling

For complex dependencies not captured in devicetree:

```c
static int mydriver_init(const struct device *dev)
{
    /* Get dependency device */
    const struct device *clock_dev = DEVICE_DT_GET(DT_NODELABEL(clock0));

    if (!device_is_ready(clock_dev)) {
        /* Dependency not ready - this shouldn't happen if
         * init levels/priorities are correct */
        return -ENODEV;
    }

    /* Use clock device */
    return 0;
}
```

### Debugging Init Order

```c
/* Add to your init function */
static int mydriver_init(const struct device *dev)
{
    printk("[INIT] %s initializing\n", dev->name);
    /* ... */
    printk("[INIT] %s complete: %d\n", dev->name, ret);
    return ret;
}
```

Use `CONFIG_BOOT_BANNER=y` and add printk to see actual init order.
