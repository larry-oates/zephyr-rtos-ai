# Interrupts in Devicetree

Interrupt configuration describes how devices signal events to the CPU via interrupt controllers.

## Overview

The interrupt model has:
1. **Interrupt controllers** — Handle and route interrupts (NVIC, GIC, etc.)
2. **Interrupt consumers** — Devices that generate interrupts
3. **Interrupt nexus** — Optional routing/mapping layer

## Interrupt Controller

Controllers are marked with `interrupt-controller` and define cell format with `#interrupt-cells`:

```devicetree
nvic: interrupt-controller@e000e100 {
    compatible = "arm,v7m-nvic";
    reg = <0xe000e100 0xc00>;
    interrupt-controller;
    #interrupt-cells = <2>;  /* IRQ number + priority */
};

/* ARM GIC example */
gic: interrupt-controller@8000000 {
    compatible = "arm,gic-v3";
    interrupt-controller;
    #interrupt-cells = <3>;  /* Type + IRQ + flags */
};
```

## Interrupt Consumer

Devices reference interrupts and optionally their parent controller:

```devicetree
&uart0 {
    interrupts = <12 1>;  /* IRQ 12, priority 1 */
    interrupt-parent = <&nvic>;
};

/* Multiple interrupts */
&dma1 {
    interrupts = <11 0>, <12 0>, <13 0>;
    interrupt-names = "chan0", "chan1", "chan2";
};
```

## Properties

### Controller Properties

| Property | Type | Description |
|----------|------|-------------|
| `interrupt-controller` | boolean | Marks node as interrupt controller |
| `#interrupt-cells` | int | Number of cells per interrupt specifier |

### Consumer Properties

| Property | Type | Description |
|----------|------|-------------|
| `interrupts` | array | Interrupt specifier(s) |
| `interrupt-parent` | phandle | Override default interrupt controller |
| `interrupt-names` | string-array | Names for each interrupt |
| `interrupts-extended` | phandle-array | Mix different controllers |

## Cell Formats

### ARM Cortex-M (NVIC) - 2 cells
```
<irq_number priority>
```
- `irq_number`: Interrupt vector number
- `priority`: Interrupt priority (0 = highest)

### ARM GIC - 3 cells
```
<type irq_number flags>
```
- `type`: 0 = SPI (shared), 1 = PPI (private)
- `irq_number`: Interrupt ID
- `flags`: Trigger type (edge/level, polarity)

### RISC-V PLIC - 2 cells
```
<irq_number priority>
```

## Default Interrupt Parent

Set a default controller for all children:

```devicetree
soc {
    interrupt-parent = <&nvic>;

    uart0: uart@40000000 {
        /* Uses &nvic automatically */
        interrupts = <12 1>;
    };
};
```

## Multiple Interrupt Controllers

Use `interrupts-extended` to reference different controllers:

```devicetree
my_device {
    interrupts-extended = <&nvic 5 1>,
                          <&gpio0 3 (GPIO_INT_EDGE | GPIO_INT_ACTIVE_LOW)>;
    interrupt-names = "tx", "gpio-alert";
};
```

## Interrupt Nexus (Mapping)

For complex routing, use `interrupt-map`:

```devicetree
pcie: pcie@1000 {
    interrupt-map-mask = <0x1800 0 0 7>;
    interrupt-map = <0x0000 0 0 1 &gic 0 14 4>,
                    <0x0000 0 0 2 &gic 0 15 4>,
                    <0x0800 0 0 1 &gic 0 16 4>,
                    <0x0800 0 0 2 &gic 0 17 4>;
    #interrupt-cells = <1>;
};
```

## GPIO Interrupts

GPIO controllers often act as interrupt controllers:

```devicetree
gpio0: gpio@50000000 {
    compatible = "nordic,nrf-gpio";
    gpio-controller;
    #gpio-cells = <2>;
    interrupt-controller;
    #interrupt-cells = <2>;
};

button0 {
    gpios = <&gpio0 11 GPIO_ACTIVE_LOW>;
    /* GPIO interrupt via gpio-controller's interrupt-controller capability */
};
```

## Complete Example

```devicetree
/* Configure UART with interrupt */
&uart0 {
    status = "okay";
    current-speed = <115200>;
    interrupts = <2 1>;  /* IRQ 2, priority 1 */
    interrupt-names = "uart0";
};

/* External interrupt on GPIO */
/ {
    buttons {
        compatible = "gpio-keys";
        button0: button_0 {
            gpios = <&gpio0 11 (GPIO_PULL_UP | GPIO_ACTIVE_LOW)>;
            zephyr,code = <INPUT_KEY_0>;
        };
    };
};
```

## C API

```c
#include <zephyr/devicetree.h>

#define MY_NODE DT_NODELABEL(uart0)

/* Get interrupt number */
#define MY_IRQ DT_IRQN(MY_NODE)

/* Get interrupt priority */
#define MY_IRQ_PRIO DT_IRQ(MY_NODE, priority)

/* For multiple interrupts */
DT_IRQ_BY_IDX(node_id, idx, cell)     /* Nth interrupt's cell */
DT_IRQ_BY_NAME(node_id, name, cell)   /* Named interrupt's cell */
DT_NUM_IRQS(node_id)                  /* Count of interrupts */

/* In driver initialization */
IRQ_CONNECT(DT_IRQN(MY_NODE),
            DT_IRQ(MY_NODE, priority),
            my_isr,
            NULL,
            0);
irq_enable(DT_IRQN(MY_NODE));

/* Or using instance macros in drivers */
#define DT_DRV_COMPAT vendor_device
IRQ_CONNECT(DT_INST_IRQN(0),
            DT_INST_IRQ(0, priority),
            my_isr,
            DEVICE_DT_INST_GET(0),
            0);
```

## Tips

1. **Check SoC header** — IRQ numbers are often defined in SoC-specific headers
2. **Priority values** — Lower number = higher priority on most ARMs
3. **interrupt-parent inheritance** — Children inherit parent's interrupt-parent
4. **Shared interrupts** — Use `interrupt-names` to distinguish in code
5. **GPIO interrupts** — Typically configured via GPIO API, not raw IRQ
