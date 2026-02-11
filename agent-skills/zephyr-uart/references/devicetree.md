# UART Devicetree Reference

Devicetree configuration for UART peripherals in Zephyr.

## Table of Contents

1. [Base Properties](#base-properties)
2. [Common Patterns](#common-patterns)
3. [Pin Control](#pin-control)
4. [Overlay Examples](#overlay-examples)
5. [Accessing from C](#accessing-from-c)

---

## Base Properties

Properties from `uart-controller.yaml` binding:

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `status` | string | No | "okay" to enable, "disabled" to disable |
| `current-speed` | int | No | Initial baud rate in bps |
| `hw-flow-control` | boolean | No | Enable RTS/CTS hardware flow control |
| `parity` | string | No | "none", "odd", "even", "mark", "space" |
| `stop-bits` | string | No | "0_5", "1", "1_5", "2" |
| `data-bits` | int | No | 5, 6, 7, 8, or 9 |
| `clock-frequency` | int | No | Clock frequency for UART operation |

### Default Values

If not specified:
- `current-speed`: Driver/SoC default (often 115200)
- `parity`: "none"
- `stop-bits`: "1"
- `data-bits`: 8
- `hw-flow-control`: disabled

---

## Common Patterns

### Basic UART Enable

```dts
&uart0 {
    status = "okay";
    current-speed = <115200>;
};
```

### With Hardware Flow Control

```dts
&uart0 {
    status = "okay";
    current-speed = <115200>;
    hw-flow-control;
};
```

### Full Configuration

```dts
&uart0 {
    status = "okay";
    current-speed = <9600>;
    parity = "even";
    stop-bits = "2";
    data-bits = <8>;
};
```

### Disable a UART

```dts
&uart1 {
    status = "disabled";
};
```

---

## Pin Control

Most UARTs require pin control configuration. This is SoC-specific.

### Nordic nRF

```dts
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

&uart0 {
    status = "okay";
    current-speed = <115200>;
    pinctrl-0 = <&uart0_default>;
    pinctrl-1 = <&uart0_sleep>;
    pinctrl-names = "default", "sleep";
};
```

### STM32

```dts
&pinctrl {
    usart2_tx_pa2: usart2_tx_pa2 {
        pinmux = <STM32_PINMUX('A', 2, AF7)>;
    };

    usart2_rx_pa3: usart2_rx_pa3 {
        pinmux = <STM32_PINMUX('A', 3, AF7)>;
    };
};

&usart2 {
    status = "okay";
    current-speed = <115200>;
    pinctrl-0 = <&usart2_tx_pa2 &usart2_rx_pa3>;
    pinctrl-names = "default";
};
```

### ESP32

```dts
&pinctrl {
    uart0_default: uart0_default {
        group1 {
            pinmux = <UART0_TX_GPIO1>;
            output-high;
        };
        group2 {
            pinmux = <UART0_RX_GPIO3>;
            bias-pull-up;
        };
    };
};

&uart0 {
    status = "okay";
    current-speed = <115200>;
    pinctrl-0 = <&uart0_default>;
    pinctrl-names = "default";
};
```

---

## Overlay Examples

### Board Overlay (app/boards/<board>.overlay)

Modify UART for specific application:

```dts
/* Change baud rate for GPS module */
&uart1 {
    status = "okay";
    current-speed = <9600>;
};
```

### Adding a Second UART

```dts
/* Enable UART2 for debug */
&uart2 {
    status = "okay";
    current-speed = <115200>;
    pinctrl-0 = <&uart2_default>;
    pinctrl-names = "default";
};
```

### Console/Shell UART Selection

Use `chosen` node to select console UART:

```dts
/ {
    chosen {
        zephyr,console = &uart0;
        zephyr,shell-uart = &uart0;
    };
};
```

### UART for Custom Device

```dts
/ {
    gps_device: gps {
        compatible = "vendor,gps-module";
        uart = <&uart1>;
    };
};

&uart1 {
    status = "okay";
    current-speed = <9600>;
};
```

---

## Accessing from C

### Get Device from Chosen Node

```c
/* For console/shell UART */
#define UART_NODE DT_CHOSEN(zephyr_shell_uart)
static const struct device *const uart = DEVICE_DT_GET(UART_NODE);
```

### Get Device from Node Label

```c
#define UART_NODE DT_NODELABEL(uart0)
static const struct device *const uart = DEVICE_DT_GET(UART_NODE);
```

### Get Device from Alias

```dts
/ {
    aliases {
        debug-uart = &uart1;
    };
};
```

```c
#define UART_NODE DT_ALIAS(debug_uart)
static const struct device *const uart = DEVICE_DT_GET(UART_NODE);
```

### Check Node Exists

```c
#if DT_NODE_EXISTS(DT_NODELABEL(uart2))
    /* UART2 is defined */
#endif
```

### Get Properties

```c
/* Get configured baud rate from DTS */
#define UART_BAUD DT_PROP(DT_NODELABEL(uart0), current_speed)

/* Check if flow control enabled */
#if DT_PROP(DT_NODELABEL(uart0), hw_flow_control)
    /* HW flow control enabled */
#endif
```

---

## Vendor-Specific Properties

Some SoCs have additional properties. Check vendor bindings:

### Nordic nRF

| Property | Description |
|----------|-------------|
| `rx-pin-pull-up` | Enable internal pull-up on RX |
| `disable-rx` | Disable RX pin (TX only) |

### STM32

| Property | Description |
|----------|-------------|
| `tx-invert` | Invert TX signal |
| `rx-invert` | Invert RX signal |
| `single-wire` | Half-duplex single-wire mode |

### Location of Bindings

- `dts/bindings/serial/uart-controller.yaml` - Base binding
- `dts/bindings/serial/<vendor>*.yaml` - Vendor-specific bindings

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| UART not working | `status` not "okay" | Add `status = "okay";` |
| Wrong baud rate | Not specified in DTS | Add `current-speed = <115200>;` |
| No data | Pins not configured | Add pinctrl configuration |
| Garbled output | Baud mismatch | Verify `current-speed` matches receiver |
| Device not found | Wrong node reference | Check `DT_NODELABEL` vs actual node name |
| Build error "node not found" | UART not enabled in SoC DTS | Check SoC dtsi file |

---

## Common DTS Macros

| Macro | Usage |
|-------|-------|
| `DT_NODELABEL(label)` | Get node by label (e.g., `uart0`) |
| `DT_CHOSEN(prop)` | Get chosen node (e.g., `zephyr_shell_uart`) |
| `DT_ALIAS(alias)` | Get node by alias |
| `DEVICE_DT_GET(node)` | Get device pointer from node |
| `DT_PROP(node, prop)` | Get property value |
| `DT_NODE_EXISTS(node)` | Check if node exists |
| `DT_NODE_HAS_STATUS(node, okay)` | Check if node is enabled |
