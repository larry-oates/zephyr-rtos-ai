# GPIO Devicetree Reference

Complete reference for GPIO devicetree bindings and properties.

## GPIO Controller Binding

Base binding: `dts/bindings/gpio/gpio-controller.yaml`

### Required Properties

| Property | Type | Description |
|----------|------|-------------|
| `gpio-controller` | boolean | Marks node as GPIO controller |
| `#gpio-cells` | int | Number of cells in GPIO specifier (usually 2) |

### Optional Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `ngpios` | int | 32 | Number of in-use GPIO slots. Set when only first N GPIOs (0...N-1) are available. |
| `gpio-reserved-ranges` | array | - | Unusable GPIO offsets as tuples (start, size). Example: `<3 2>, <10 1>` marks offsets 3, 4, 10 unavailable. |
| `gpio-line-names` | string-array | - | Names for GPIO lines (documentation/debugging). |

### Controller Example

```dts
gpio0: gpio@50000000 {
    compatible = "nordic,nrf-gpio";
    reg = <0x50000000 0x200>;
    gpio-controller;
    #gpio-cells = <2>;
    ngpios = <16>;
    gpio-line-names = "LED1", "LED2", "BUTTON1", "", "", "", "", "",
                      "", "", "", "", "", "", "", "";
    status = "okay";
};

gpio1: gpio@50000300 {
    compatible = "nordic,nrf-gpio";
    reg = <0x50000300 0x200>;
    gpio-controller;
    #gpio-cells = <2>;
    ngpios = <16>;
    gpio-reserved-ranges = <12 4>;  /* Pins 12-15 not usable */
};
```

## GPIO Specifier Format

Standard 2-cell format: `<&controller pin flags>`

```dts
gpios = <&gpio0 13 GPIO_ACTIVE_LOW>;
/*       ^      ^  ^
         |      |  flags (from dt-bindings/gpio/gpio.h)
         |      pin number
         phandle to controller
*/
```

## gpio-leds Binding

Path: `dts/bindings/led/gpio-leds.yaml`

### Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `compatible` | string | yes | Must be "gpio-leds" |
| `gpios` | phandle-array | yes | GPIO specifier |
| `label` | string | no | Human-readable name |

### Example

```dts
/ {
    aliases {
        led0 = &green_led;
        led1 = &red_led;
    };

    leds {
        compatible = "gpio-leds";

        green_led: led_0 {
            gpios = <&gpio0 13 GPIO_ACTIVE_LOW>;
            label = "Green LED";
        };

        red_led: led_1 {
            gpios = <&gpio0 14 GPIO_ACTIVE_LOW>;
            label = "Red LED";
        };
    };
};
```

### Usage in Code

```c
#define LED0_NODE DT_ALIAS(led0)
static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(LED0_NODE, gpios);
```

## gpio-keys Binding

Path: `dts/bindings/input/gpio-keys.yaml`

### Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `compatible` | string | yes | Must be "gpio-keys" |
| `debounce-interval-ms` | int | no | Debounce interval (default: 30) |
| `polling-mode` | boolean | no | Poll instead of using interrupts |
| `gpios` | phandle-array | yes | GPIO specifier |
| `label` | string | no | Human-readable name |
| `zephyr,code` | int | no | Input event code |

### Example

```dts
/ {
    aliases {
        sw0 = &button0;
    };

    buttons {
        compatible = "gpio-keys";
        debounce-interval-ms = <50>;

        button0: button_0 {
            gpios = <&gpio0 11 (GPIO_PULL_UP | GPIO_ACTIVE_LOW)>;
            label = "User Button";
            zephyr,code = <INPUT_KEY_0>;
        };
    };
};
```

### Usage in Code

```c
#define SW0_NODE DT_ALIAS(sw0)
static const struct gpio_dt_spec button = GPIO_DT_SPEC_GET(SW0_NODE, gpios);
```

## GPIO Hogs

Requires: `CONFIG_GPIO_HOGS=y`

Auto-configure GPIOs at boot without application code.

### Hog Properties

| Property | Type | Description |
|----------|------|-------------|
| `gpio-hog` | boolean | Marks node as GPIO hog |
| `gpios` | array | GPIO specifiers to hog |
| `input` | boolean | Configure as input |
| `output-low` | boolean | Configure as output LOW |
| `output-high` | boolean | Configure as output HIGH |
| `line-name` | string | Optional descriptive name |

### Example

```dts
&gpio0 {
    mux-hog {
        gpio-hog;
        gpios = <10 GPIO_ACTIVE_HIGH>, <11 GPIO_ACTIVE_HIGH>;
        output-high;
        line-name = "MUX_SEL0", "MUX_SEL1";
    };

    power-enable {
        gpio-hog;
        gpios = <5 GPIO_ACTIVE_HIGH>;
        output-low;
        line-name = "POWER_EN";
    };
};
```

## GPIO Flags (dt-bindings)

Include: `<zephyr/dt-bindings/gpio/gpio.h>`

### Active Level

| Flag | Value | Description |
|------|-------|-------------|
| `GPIO_ACTIVE_LOW` | 1 | Logical active = physical low |
| `GPIO_ACTIVE_HIGH` | 0 | Logical active = physical high |

### Pull Configuration

| Flag | Value | Description |
|------|-------|-------------|
| `GPIO_PULL_UP` | 16 | Enable internal pull-up |
| `GPIO_PULL_DOWN` | 32 | Enable internal pull-down |

### Drive Mode

| Flag | Value | Description |
|------|-------|-------------|
| `GPIO_OPEN_DRAIN` | 64 | Open-drain output |
| `GPIO_OPEN_SOURCE` | 128 | Open-source output |

### Combining Flags

```dts
/* Button with pull-up, active-low */
gpios = <&gpio0 11 (GPIO_PULL_UP | GPIO_ACTIVE_LOW)>;

/* Open-drain output */
gpios = <&gpio0 5 (GPIO_OPEN_DRAIN | GPIO_ACTIVE_LOW)>;
```

## Generic GPIO Node Pattern

For arbitrary GPIO usage (not LED/button specific):

```dts
/ {
    /* Can reuse gpio-leds compatible for any GPIO output */
    custom_gpios {
        compatible = "gpio-leds";

        my_output: output_pin {
            gpios = <&gpio0 5 GPIO_ACTIVE_HIGH>;
            label = "Data Output";
        };
    };
};
```

## Accessing GPIO in Code

### By Alias

```c
#define LED_NODE DT_ALIAS(led0)
static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(LED_NODE, gpios);
```

### By Node Label

```c
static const struct gpio_dt_spec pin =
    GPIO_DT_SPEC_GET(DT_NODELABEL(my_output), gpios);
```

### By Path

```c
static const struct gpio_dt_spec pin =
    GPIO_DT_SPEC_GET(DT_PATH(leds, led_0), gpios);
```

### Checking Node Existence

```c
#if DT_NODE_EXISTS(DT_ALIAS(led0))
static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(DT_ALIAS(led0), gpios);
#endif
```

## Board Overlay Examples

### Adding LED to Custom Board

```dts
/* boards/my_board.overlay */
/ {
    aliases {
        led0 = &status_led;
    };

    leds {
        compatible = "gpio-leds";
        status_led: led_status {
            gpios = <&gpio0 17 GPIO_ACTIVE_HIGH>;
            label = "Status LED";
        };
    };
};
```

### Overriding Existing Pin

```dts
&green_led {
    gpios = <&gpio1 5 GPIO_ACTIVE_LOW>;
};
```

### Disabling a Node

```dts
&unused_led {
    status = "disabled";
};
```

## Multiple GPIOs in One Property

```dts
my_device {
    control-gpios = <&gpio0 5 GPIO_ACTIVE_HIGH>,
                    <&gpio0 6 GPIO_ACTIVE_HIGH>,
                    <&gpio1 2 GPIO_ACTIVE_LOW>;
};
```

```c
/* Access by index */
static const struct gpio_dt_spec ctrl[] = {
    GPIO_DT_SPEC_GET_BY_IDX(DT_NODELABEL(my_device), control_gpios, 0),
    GPIO_DT_SPEC_GET_BY_IDX(DT_NODELABEL(my_device), control_gpios, 1),
    GPIO_DT_SPEC_GET_BY_IDX(DT_NODELABEL(my_device), control_gpios, 2),
};
```

## Optional GPIO

```c
static const struct gpio_dt_spec optional_pin =
    GPIO_DT_SPEC_GET_OR(DT_NODELABEL(my_node), optional_gpios, {0});

if (optional_pin.port != NULL) {
    /* GPIO is defined */
}
```

## GPIO Nexus Binding

Path: `dts/bindings/gpio/gpio-nexus.yaml`

For GPIO mapping/redirection between controllers.

| Property | Type | Description |
|----------|------|-------------|
| `gpio-map` | compound | GPIO mapping entries |
| `gpio-map-mask` | array | Mask for matching specifiers |
| `gpio-map-pass-thru` | array | Flags to pass through |
| `#gpio-cells` | int | Cells in GPIO specifiers |

### Example

```dts
gpio_mux: gpio-mux {
    compatible = "gpio-nexus";
    #gpio-cells = <2>;

    gpio-map =
        <0 0 &gpio0 1 0>,
        <1 0 &gpio0 2 0>,
        <2 0 &gpio1 5 0>;

    gpio-map-mask = <0xF 0x0>;
    gpio-map-pass-thru = <0x0 0x7>;
};

/* Usage: reference the mux instead of individual GPIO controllers */
led {
    gpios = <&gpio_mux 0 GPIO_ACTIVE_HIGH>;  /* Maps to &gpio0 1 */
};
```
