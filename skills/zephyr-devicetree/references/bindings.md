# Devicetree Bindings

Bindings are YAML files that describe the requirements for devicetree nodes. Zephyr uses them to validate DTS files and generate C macros.

## Binding Structure

```yaml
compatible: "vendor,device"
description: "High-level description of the device"

include: [base.yaml, uart-controller.yaml]

properties:
  reg:
    type: array
    required: true
    description: MMIO register space
  current-speed:
    type: int
    default: 115200
  hw-flow-control:
    type: boolean

# If this node is a bus (e.g., I2C controller)
bus: i2c

# If this node is on a bus (e.g., I2C sensor)
on-bus: i2c

# Naming cells for phandle-arrays (e.g., #gpio-cells)
gpio-cells:
  - pin
  - flags
```

## Property Types in Bindings

- `string`, `int`, `boolean`, `array`, `uint8-array`, `string-array`
- `phandle`, `phandles`, `phandle-array`
- `path`: Path to a node (string or phandle reference)
- `compound`: Complex types (no macros generated)

## Key Concepts

- **required**: If `true`, the build fails if the property is missing in the DTS.
- **default**: Value used if the property is missing in the DTS.
- **enum**: Limits property values to a fixed list.
- **bus / on-bus**: Used for matching bindings based on the hardware hierarchy. A sensor on an I2C bus will match a binding with `on-bus: i2c`.
- **child-binding**: Constrains the children of the node (e.g., for `gpio-leds`).
- **specifier-cells**: (e.g., `gpio-cells`, `pwm-cells`) Names the cells in a `phandle-array` so they can be accessed by name in C.

## Where to find bindings
Bindings are usually located in `dts/bindings/` within the Zephyr tree or a module.
- `base.yaml`: Common properties for all nodes.
- `gpio-controller.yaml`: Common for GPIO controllers.
- `i2c-device.yaml`: Common for I2C slaves.
