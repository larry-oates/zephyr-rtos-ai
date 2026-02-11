# GPIO Devicetree Reference

Complete reference for GPIO devicetree bindings and properties.

## GPIO Controller Binding

Base binding for GPIO controllers: `dts/bindings/gpio/gpio-controller.yaml`

### Required Properties

| Property | Type | Description |
|----------|------|-------------|
| `gpio-controller` | boolean | Marks node as GPIO controller |
| `#gpio-cells` | int | Number of cells in GPIO specifier (usually 2) |

### Common Controller Example

```dts
gpio0: gpio@50000000 {
    compatible = "nordic,nrf-gpio";
    reg = <0x50000000 0x200>;
    gpio-controller;
    #gpio-cells = <2>;
    status = "okay";
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

For LED outputs controlled by GPIO.

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

For button/switch inputs.

### Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `compatible` | string | yes | Must be "gpio-keys" |
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
/* Change LED pin on existing board */
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

## GPIO Controller Selection

### Multiple GPIO Ports

```dts
/* Port 0 */
gpios = <&gpio0 13 GPIO_ACTIVE_LOW>;

/* Port 1 */
gpios = <&gpio1 5 GPIO_ACTIVE_HIGH>;
```

### Getting Port Device in Code

```c
/* From dt_spec (automatic) */
const struct device *port = led.port;

/* Directly */
const struct device *gpio0 = DEVICE_DT_GET(DT_NODELABEL(gpio0));
```

## Common Patterns

### Multiple GPIOs in One Property

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

### Optional GPIO

```c
static const struct gpio_dt_spec optional_pin =
    GPIO_DT_SPEC_GET_OR(DT_NODELABEL(my_node), optional_gpios, {0});

if (optional_pin.port != NULL) {
    /* GPIO is defined */
}
```
