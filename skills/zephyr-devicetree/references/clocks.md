# Clocks in Devicetree

Clock configuration describes clock sources, frequencies, and how peripherals connect to clocks.

## Overview

The clock model has two parts:
1. **Clock providers** — Clock controllers that generate/distribute clocks
2. **Clock consumers** — Devices that use clocks from providers

## Clock Provider

Clock providers use `#clock-cells` to define how many cells identify each clock output.

```devicetree
rcc: rcc@40023800 {
    compatible = "st,stm32-rcc";
    reg = <0x40023800 0x400>;
    #clock-cells = <2>;  /* Two cells: bus-id and clock-id */
};

/* Or simpler single-cell provider */
clock: clock-controller@4000 {
    compatible = "vendor,clock-controller";
    reg = <0x4000 0x100>;
    #clock-cells = <1>;  /* One cell: clock-id */
};
```

## Clock Consumer

Consumers reference clocks using `clocks` and optionally `clock-names`:

```devicetree
&usart1 {
    clocks = <&rcc STM32_CLOCK_BUS_APB2 0x00000010>;
    /* Or with multiple clocks: */
    clocks = <&rcc CLOCK_PCLK>, <&rcc CLOCK_HSE>;
    clock-names = "apb", "hse";
};
```

## Properties

### Provider Properties

| Property | Type | Description |
|----------|------|-------------|
| `#clock-cells` | int | Number of cells to identify a clock output |
| `clock-output-names` | string-array | Optional names for clock outputs |
| `clock-frequency` | int | Fixed clock frequency in Hz |

### Consumer Properties

| Property | Type | Description |
|----------|------|-------------|
| `clocks` | phandle-array | Reference to clock(s) with specifier cells |
| `clock-names` | string-array | Names for each clock reference |
| `clock-frequency` | int | Override/specify frequency |
| `assigned-clocks` | phandle-array | Clocks to configure at boot |
| `assigned-clock-rates` | array | Rates for assigned-clocks |

## Vendor Patterns

### STM32
```devicetree
/* STM32 uses two cells: bus and bit position */
&usart2 {
    clocks = <&rcc STM32_CLOCK_BUS_APB1 0x00020000>;
};
```

### Nordic nRF
```devicetree
/* Nordic peripherals often don't need explicit clock config */
/* But for external oscillators: */
&clock {
    status = "okay";
    hfclk = "external";
};
```

### NXP
```devicetree
&lpuart1 {
    clocks = <&ccm IMX_CCM_LPUART_CLK 0x7C 24>;
};
```

## Common Clock Types

```devicetree
/ {
    clocks {
        /* Fixed clock (e.g., external crystal) */
        xtal: xtal {
            compatible = "fixed-clock";
            #clock-cells = <0>;
            clock-frequency = <32768>;
        };

        /* Fixed-factor divider */
        pll_div2: pll-div2 {
            compatible = "fixed-factor-clock";
            #clock-cells = <0>;
            clocks = <&pll>;
            clock-mult = <1>;
            clock-div = <2>;
        };
    };
};
```

## Complete Example

```devicetree
/* Add external 8MHz crystal and use it for a peripheral */

/ {
    clocks {
        ext_osc: ext-osc {
            compatible = "fixed-clock";
            #clock-cells = <0>;
            clock-frequency = <8000000>;
        };
    };
};

&spi1 {
    status = "okay";
    clocks = <&rcc STM32_CLOCK_BUS_APB2 0x00001000>,
             <&ext_osc>;
    clock-names = "apb", "ext";
};
```

## C API

```c
#include <zephyr/drivers/clock_control.h>

/* Get clock rate from devicetree */
#define MY_NODE DT_NODELABEL(usart1)

/* Check if clocks property exists */
#if DT_NODE_HAS_PROP(MY_NODE, clocks)
    /* Get clock controller device */
    const struct device *clk = DEVICE_DT_GET(DT_CLOCKS_CTLR(MY_NODE));

    /* Get clock rate */
    uint32_t rate;
    clock_control_get_rate(clk,
                           (clock_control_subsys_t)DT_CLOCKS_CELL(MY_NODE, id),
                           &rate);
#endif

/* Macros for clock access */
DT_CLOCKS_CTLR(node_id)              /* Clock controller phandle */
DT_CLOCKS_CTLR_BY_IDX(node_id, idx)  /* Nth clock controller */
DT_CLOCKS_CTLR_BY_NAME(node_id, name) /* Clock by name */
DT_CLOCKS_CELL(node_id, cell)        /* Specific cell value */
DT_CLOCKS_CELL_BY_IDX(node_id, idx, cell)
DT_CLOCKS_CELL_BY_NAME(node_id, name, cell)
```

## Tips

1. **Check SoC dtsi** — Clock trees are pre-defined in SoC files
2. **Use clock-names** — Makes code more readable when multiple clocks exist
3. **Fixed clocks** — Use `fixed-clock` for external oscillators
4. **Build output** — Check `zephyr.dts` to verify clock assignments
