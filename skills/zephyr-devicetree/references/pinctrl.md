# Pin Control (Pinctrl) in Devicetree

Pin control configures pin multiplexing (which peripheral uses which pin) and electrical properties (pull-up, drive strength, etc.).

## Overview

Zephyr's pinctrl subsystem uses a two-part model:
1. **Pin configuration nodes** — Define specific pin states
2. **Device references** — Devices reference their pin configurations via `pinctrl-N` properties

## Basic Structure

### Pin Configuration (Vendor-Specific)

Pin configurations are defined under a pinctrl node. The exact format varies by vendor.

**Nordic nRF:**
```devicetree
&pinctrl {
    uart0_default: uart0_default {
        group1 {
            psels = <NRF_PSEL(UART_TX, 0, 6)>,
                    <NRF_PSEL(UART_RX, 0, 8)>;
        };
    };
    uart0_sleep: uart0_sleep {
        group1 {
            psels = <NRF_PSEL(UART_TX, 0, 6)>,
                    <NRF_PSEL(UART_RX, 0, 8)>;
            low-power-enable;
        };
    };
};
```

**STM32:**
```devicetree
&pinctrl {
    usart2_tx_pa2: usart2_tx_pa2 {
        pinmux = <STM32_PINMUX('A', 2, AF7)>;
    };
    usart2_rx_pa3: usart2_rx_pa3 {
        pinmux = <STM32_PINMUX('A', 3, AF7)>;
    };
};
```

**NXP:**
```devicetree
&pinctrl {
    pinmux_lpuart1: pinmux_lpuart1 {
        group0 {
            pinmux = <&iomuxc_gpio_ad_24_lpuart1_txd>,
                     <&iomuxc_gpio_ad_25_lpuart1_rxd>;
            drive-strength = "high";
            slew-rate = "fast";
        };
    };
};
```

### Device Referencing Pinctrl

Devices reference pin states using `pinctrl-N` and `pinctrl-names`:

```devicetree
&uart0 {
    status = "okay";
    current-speed = <115200>;
    pinctrl-0 = <&uart0_default>;
    pinctrl-1 = <&uart0_sleep>;
    pinctrl-names = "default", "sleep";
};
```

## Properties

| Property | Type | Description |
|----------|------|-------------|
| `pinctrl-0` | phandle-array | First pin state (typically "default") |
| `pinctrl-1` | phandle-array | Second pin state (typically "sleep") |
| `pinctrl-N` | phandle-array | Nth pin state |
| `pinctrl-names` | string-array | Names for each state: `"default"`, `"sleep"`, etc. |

## Common Pin Properties

Electrical properties vary by vendor but common ones include:

| Property | Description |
|----------|-------------|
| `bias-disable` | No pull-up/pull-down |
| `bias-pull-up` | Enable pull-up resistor |
| `bias-pull-down` | Enable pull-down resistor |
| `drive-push-pull` | Push-pull drive mode |
| `drive-open-drain` | Open-drain drive mode |
| `input-enable` | Enable input buffer |
| `output-enable` | Enable output buffer |
| `low-power-enable` | Low power mode (Nordic) |
| `drive-strength` | Drive strength setting |
| `slew-rate` | Slew rate control |

## Vendor Macros

### Nordic nRF
```c
NRF_PSEL(function, port, pin)
// Example: NRF_PSEL(UART_TX, 0, 6) = UART TX on P0.06
```

### STM32
```c
STM32_PINMUX(port, pin, af)
// Example: STM32_PINMUX('A', 2, AF7) = PA2 with alternate function 7
```

### NXP i.MX RT
Uses phandle references to pre-defined pin nodes in SoC dtsi files.

## Complete Overlay Example

```devicetree
/* app.overlay - Add UART with custom pinctrl */

&pinctrl {
    uart1_default: uart1_default {
        group1 {
            psels = <NRF_PSEL(UART_TX, 1, 1)>,
                    <NRF_PSEL(UART_RX, 1, 2)>;
        };
    };
};

&uart1 {
    status = "okay";
    current-speed = <115200>;
    pinctrl-0 = <&uart1_default>;
    pinctrl-names = "default";
};
```

## C API

```c
#include <zephyr/drivers/pinctrl.h>

/* Pinctrl is typically handled automatically by device drivers */
/* Manual control (rarely needed): */
PINCTRL_DT_DEFINE(DT_NODELABEL(uart0));
const struct pinctrl_dev_config *pcfg = PINCTRL_DT_DEV_CONFIG_GET(DT_NODELABEL(uart0));
pinctrl_apply_state(pcfg, PINCTRL_STATE_DEFAULT);
pinctrl_apply_state(pcfg, PINCTRL_STATE_SLEEP);
```

## Tips

1. **Check SoC dtsi** — Most SoCs pre-define pinctrl nodes; you often just reference them
2. **State names matter** — Use `"default"` and `"sleep"` for automatic power management
3. **Multiple groups** — Use multiple groups within a state for different electrical settings
4. **Binding files** — Vendor-specific properties are documented in `dts/bindings/pinctrl/` bindings
