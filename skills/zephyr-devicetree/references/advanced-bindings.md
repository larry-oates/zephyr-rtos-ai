# Advanced Devicetree Bindings

Advanced binding features for complex hardware descriptions including child bindings, enums, specifier cells, and inheritance.

## Child Bindings

Child bindings constrain the format of child nodes. Used for containers like `gpio-leds`, `pwm-leds`, etc.

### Basic Child Binding

```yaml
# gpio-leds.yaml
compatible: "gpio-leds"
description: Container for GPIO-connected LEDs

child-binding:
  description: An LED connected to a GPIO
  properties:
    gpios:
      type: phandle-array
      required: true
    label:
      type: string
```

**DTS Usage:**
```devicetree
leds {
    compatible = "gpio-leds";
    led0: led_0 {
        gpios = <&gpio0 13 GPIO_ACTIVE_LOW>;
        label = "Green LED";
    };
    led1: led_1 {
        gpios = <&gpio0 14 GPIO_ACTIVE_LOW>;
        label = "Red LED";
    };
};
```

### Nested Child Bindings

For deeper hierarchies (grandchildren):

```yaml
# fixed-partitions.yaml
compatible: "fixed-partitions"

properties:
  "#address-cells":
    const: 1
  "#size-cells":
    const: 1

child-binding:
  description: A flash partition
  properties:
    reg:
      type: array
      required: true
    label:
      type: string
    read-only:
      type: boolean
```

## Enum and Const Properties

### Enum (Restrict to List)

```yaml
properties:
  operating-mode:
    type: string
    enum:
      - "low-power"
      - "normal"
      - "high-performance"
    default: "normal"
    description: Device operating mode

  trigger-type:
    type: int
    enum: [0, 1, 2, 4]
    description: Interrupt trigger type
```

**DTS Usage:**
```devicetree
my_device {
    operating-mode = "high-performance";
    trigger-type = <2>;
};
```

**C Access:**
```c
/* Get enum as index (0, 1, 2...) */
DT_ENUM_IDX(node_id, operating_mode)

/* Get enum as token for switch statements */
DT_STRING_TOKEN(node_id, operating_mode)
```

### Const (Fixed Value)

```yaml
properties:
  "#address-cells":
    type: int
    const: 1
  "#size-cells":
    type: int
    const: 0
  compatible:
    const: "vendor,specific-device"
```

The build fails if DTS doesn't match the const value.

## Specifier Cells

Specifier cells name the elements in phandle-arrays, enabling named access in C.

### GPIO Cells

```yaml
# gpio-controller.yaml
gpio-cells:
  - pin
  - flags
```

**DTS:**
```devicetree
led {
    gpios = <&gpio0 13 GPIO_ACTIVE_LOW>;
    /*       ^phandle ^pin ^flags */
};
```

**C Access:**
```c
DT_GPIO_PIN(node_id, gpios)    /* Returns 13 */
DT_GPIO_FLAGS(node_id, gpios)  /* Returns GPIO_ACTIVE_LOW */
/* Or generically: */
DT_PHA(node_id, gpios, pin)
DT_PHA(node_id, gpios, flags)
```

### PWM Cells

```yaml
# pwm-controller.yaml
pwm-cells:
  - channel
  - period
  - flags
```

**DTS:**
```devicetree
buzzer {
    pwms = <&pwm0 2 1000000 PWM_POLARITY_NORMAL>;
    /*     ^phandle ^ch ^period ^flags */
};
```

**C Access:**
```c
DT_PWMS_CHANNEL(node_id, buzzer)
DT_PWMS_PERIOD(node_id, buzzer)
DT_PWMS_FLAGS(node_id, buzzer)
/* Or: */
DT_PHA(node_id, pwms, channel)
DT_PHA(node_id, pwms, period)
```

### Custom Cells

```yaml
# my-controller.yaml
my-cells:
  - index
  - config
  - mode
```

**DTS:**
```devicetree
consumer {
    my-controller = <&my_ctrl 0 0x1234 2>;
};
```

**C Access:**
```c
DT_PHA(node_id, my_controller, index)   /* 0 */
DT_PHA(node_id, my_controller, config)  /* 0x1234 */
DT_PHA(node_id, my_controller, mode)    /* 2 */
```

## Binding Inheritance (include)

### Basic Include

```yaml
# vendor,uart.yaml
compatible: "vendor,uart"
include: base.yaml

properties:
  current-speed:
    type: int
    default: 115200
```

### Multiple Includes

```yaml
include:
  - base.yaml
  - uart-controller.yaml
  - pinctrl-device.yaml
```

### Include with Overrides

```yaml
include:
  - name: base.yaml
    property-allowlist:
      - reg
      - interrupts
      - status

  - name: uart-controller.yaml
    property-blocklist:
      - deprecated-property
```

### Common Base Bindings

| Binding | Provides |
|---------|----------|
| `base.yaml` | `reg`, `status`, `compatible`, `label` |
| `i2c-device.yaml` | I2C slave properties |
| `spi-device.yaml` | SPI slave properties |
| `gpio-controller.yaml` | GPIO controller properties |
| `interrupt-controller.yaml` | Interrupt controller properties |
| `pinctrl-device.yaml` | Pin control properties |

## Deprecated Properties

```yaml
properties:
  old-property:
    type: int
    deprecated: true
    description: Use 'new-property' instead

  new-property:
    type: int
```

Build warns if deprecated properties are used.

## Property Dependencies

```yaml
properties:
  feature-enabled:
    type: boolean

  feature-config:
    type: int
    description: Only valid if feature-enabled is set
```

Note: Zephyr bindings don't enforce property dependencies at build time, but document them.

## Complete Binding Example

```yaml
# vendor,my-sensor.yaml
description: A custom environmental sensor

compatible: "vendor,my-sensor"

include:
  - base.yaml
  - i2c-device.yaml

properties:
  reg:
    required: true

  sample-rate:
    type: int
    enum: [1, 10, 100, 1000]
    default: 100
    description: Sampling rate in Hz

  temperature-offset:
    type: int
    default: 0
    description: Temperature calibration offset (m°C)

  power-mode:
    type: string
    enum:
      - "ultra-low"
      - "low"
      - "normal"
    default: "normal"

  interrupt-gpios:
    type: phandle-array
    description: Optional data-ready interrupt
```

**Usage:**
```devicetree
&i2c1 {
    my_sensor: sensor@44 {
        compatible = "vendor,my-sensor";
        reg = <0x44>;
        sample-rate = <100>;
        power-mode = "low";
        interrupt-gpios = <&gpio0 5 GPIO_ACTIVE_LOW>;
    };
};
```

## Tips

1. **Start with base.yaml** — Always include it for standard properties
2. **Use enums** — Constrain values to prevent typos
3. **Name your cells** — Makes C code more readable
4. **Document well** — Binding descriptions appear in build errors
5. **Check existing bindings** — Look at `dts/bindings/` for patterns
