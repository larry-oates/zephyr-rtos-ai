# Devicetree Syntax and Structure

Devicetree is a hierarchical data structure used to describe hardware. In Zephyr, it's defined in Devicetree Source (DTS) files.

## Basic Structure

```devicetree
/dts-v1/;

/ {
    soc {
        serial0: uart@40002000 {
            compatible = "nordic,nrf-uarte";
            reg = <0x40002000 0x1000>;
            status = "okay";
        };
    };

    aliases {
        my-uart = &serial0;
    };

    chosen {
        zephyr,console = &serial0;
    };
};
```

- `/dts-v1/;`: Required version header.
- `/`: The root node.
- `nodes`: Defined as `name@unit-address { ... };`.
- `node labels`: Shorthands like `serial0:` used to refer to nodes elsewhere (e.g., `&serial0`).
- `properties`: Name/value pairs like `compatible = "vendor,device";`.

## Nodes

Nodes represent hardware components.
- **Path**: `/soc/uart@40002000` identifies the node's location.
- **Unit Address**: The part after `@` (e.g., `40002000`). It represents the node's address in its parent's address space (MMIO address, I2C address, SPI chip select, etc.).

## Important Properties

- **compatible**: A list of strings identifying the hardware. Used to match the node with a driver and binding. Format: `"vendor,model"`.
- **reg**: Address and length of the device's registers. Format: `<addr len>`.
- **status**: Use `"okay"` to enable a node or `"disabled"` to disable it.
- **interrupts**: Interrupt specifiers for the device.

## Property Value Types

| Type | Syntax | Example |
| :--- | :--- | :--- |
| `string` | Double quotes | `label = "my-device";` |
| `int` | Angle brackets | `foo = <1>;` |
| `boolean` | No value (present = true) | `hw-flow-control;` |
| `array` | Angle brackets, space-separated | `foo = <1 2 3>;` |
| `uint8-array` | Square brackets, hex | `mac = [01 02 03];` |
| `string-array` | Comma-separated strings | `names = "a", "b";` |
| `phandle` | Angle brackets with `&` | `irq-parent = <&intc>;` |
| `phandle-array`| List of phandles + cells | `pwms = <&pwm0 1 1000>;` |

## Special Nodes

- **aliases**: User-defined shorthands for nodes (e.g., `led0 = &led_red_node;`).
- **chosen**: System-wide configuration (e.g., `zephyr,console = &uart0;`).
