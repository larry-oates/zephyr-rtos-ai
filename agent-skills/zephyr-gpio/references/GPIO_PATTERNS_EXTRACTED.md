# Zephyr GPIO Usage Patterns - Extracted from Official Samples

This document contains practical GPIO usage patterns extracted from official Zephyr RTOS samples. These patterns are designed for the `zephyr-gpio` skill's common workflows section.

---

## 1. GPIO SPEC FROM DEVICETREE (Foundation Pattern)

### How GPIO specs are obtained from devicetree

**Pattern Source**: `samples/basic/blinky/src/main.c` (lines 14-21)

```c
/* Get GPIO spec from devicetree using alias */
#define LED0_NODE DT_ALIAS(led0)

/* Create a gpio_dt_spec from devicetree definition */
static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(LED0_NODE, gpios);
```

**Key Concepts**:
- Use `DT_ALIAS()` to reference devicetree aliases (e.g., `led0`, `sw0`)
- `GPIO_DT_SPEC_GET()` automatically extracts GPIO port, pin, and flags from devicetree
- This is preferred over manual port/pin configuration

**With Optional Default Fallback**:

Pattern Source: `samples/basic/button/src/main.c` (lines 24-29, 36-37)

```c
/* Optional GPIO spec with error check and fallback */
#define SW0_NODE DT_ALIAS(sw0)
#if !DT_NODE_HAS_STATUS_OKAY(SW0_NODE)
#error "Unsupported board: sw0 devicetree alias is not defined"
#endif
static const struct gpio_dt_spec button = GPIO_DT_SPEC_GET_OR(SW0_NODE, gpios, {0});

/* Optional LED (with zero-default fallback) */
static struct gpio_dt_spec led = GPIO_DT_SPEC_GET_OR(DT_ALIAS(led0), gpios, {0});
```

**Key Concepts**:
- `GPIO_DT_SPEC_GET_OR()` allows optional GPIO with fallback struct
- Always check `DT_NODE_HAS_STATUS_OKAY()` for required pins
- Optional pins can use zero-default: `{0}` means not configured

---

## 2. OUTPUT PIN CONFIGURATION & TOGGLING

### Basic Output Configuration and Toggle Pattern

**Pattern Source**: `samples/basic/blinky/src/main.c` (lines 28-45)

```c
#include <zephyr/drivers/gpio.h>

int main(void)
{
    int ret;
    bool led_state = true;

    /* Step 1: Check if GPIO device is ready */
    if (!gpio_is_ready_dt(&led)) {
        return 0;  /* Device not available, abort */
    }

    /* Step 2: Configure pin as output (starts in ACTIVE state) */
    ret = gpio_pin_configure_dt(&led, GPIO_OUTPUT_ACTIVE);
    if (ret < 0) {
        return 0;  /* Configuration failed */
    }

    /* Step 3: Toggle in a loop */
    while (1) {
        ret = gpio_pin_toggle_dt(&led);
        if (ret < 0) {
            return 0;  /* Toggle failed */
        }

        led_state = !led_state;
        printf("LED state: %s\n", led_state ? "ON" : "OFF");
        k_msleep(SLEEP_TIME_MS);
    }
    return 0;
}
```

**Key Workflow Steps**:
1. **Readiness Check**: `gpio_is_ready_dt()` - must always check before configuring
2. **Configure Output**: `gpio_pin_configure_dt(&gpio_spec, GPIO_OUTPUT_ACTIVE)`
   - `GPIO_OUTPUT_ACTIVE` = starts HIGH
   - `GPIO_OUTPUT_INACTIVE` = starts LOW
3. **Toggle**: `gpio_pin_toggle_dt(&gpio_spec)` - flips current state
4. **Error Handling**: Always check return codes for all operations

### Setting Pin States Explicitly

**Pattern Source**: `samples/basic/button/src/main.c` (lines 91-100)

```c
/* Read current pin state */
int val = gpio_pin_get_dt(&button);

if (val >= 0) {
    /* Set LED to match button state (0 or 1) */
    gpio_pin_set_dt(&led, val);
}
```

**Key Operations**:
- `gpio_pin_set_dt(&gpio_spec, value)` - set pin to 0 (LOW) or 1 (HIGH)
- `gpio_pin_get_dt(&gpio_spec)` - read current pin state, returns 0/1 or negative error

---

## 3. INPUT PIN CONFIGURATION WITH INTERRUPTS

### Complete Interrupt-Driven Button Pattern

**Pattern Source**: `samples/basic/button/src/main.c` (lines 39-72)

```c
#include <zephyr/drivers/gpio.h>
#include <zephyr/sys/util.h>

/* Callback structure (global) */
static struct gpio_callback button_cb_data;

/* Callback function - called when interrupt fires */
void button_pressed(const struct device *dev,
                   struct gpio_callback *cb,
                   uint32_t pins)
{
    printk("Button pressed at %" PRIu32 "\n", k_cycle_get_32());
}

int main(void)
{
    int ret;

    /* Step 1: Check button device is ready */
    if (!gpio_is_ready_dt(&button)) {
        printk("Error: button device %s is not ready\n",
               button.port->name);
        return 0;
    }

    /* Step 2: Configure pin as INPUT */
    ret = gpio_pin_configure_dt(&button, GPIO_INPUT);
    if (ret != 0) {
        printk("Error %d: failed to configure %s pin %d\n",
               ret, button.port->name, button.pin);
        return 0;
    }

    /* Step 3: Configure interrupt trigger type */
    ret = gpio_pin_interrupt_configure_dt(&button,
                                         GPIO_INT_EDGE_TO_ACTIVE);
    if (ret != 0) {
        printk("Error %d: failed to configure interrupt on %s pin %d\n",
               ret, button.port->name, button.pin);
        return 0;
    }

    /* Step 4: Initialize callback structure */
    gpio_init_callback(&button_cb_data, button_pressed, BIT(button.pin));

    /* Step 5: Register callback with GPIO port */
    gpio_add_callback(button.port, &button_cb_data);

    printk("Set up button at %s pin %d\n", button.port->name, button.pin);

    /* Main application loop */
    while (1) {
        k_msleep(1);
    }
    return 0;
}
```

**Key Workflow Steps**:
1. **Readiness Check**: `gpio_is_ready_dt(&button)`
2. **Configure as Input**: `gpio_pin_configure_dt(&button, GPIO_INPUT)`
3. **Set Interrupt Trigger**: `gpio_pin_interrupt_configure_dt(&button, GPIO_INT_EDGE_TO_ACTIVE)`
   - `GPIO_INT_EDGE_TO_ACTIVE` = trigger on rising edge (0→1)
   - `GPIO_INT_EDGE_TO_INACTIVE` = trigger on falling edge (1→0)
   - `GPIO_INT_LEVEL_ACTIVE` = trigger while HIGH
   - `GPIO_INT_LEVEL_INACTIVE` = trigger while LOW
4. **Initialize Callback**: `gpio_init_callback(&cb_data, handler_func, BIT(pin_number))`
   - Creates the callback structure
   - Associates it with the handler function
   - Specifies which pin(s) trigger it
5. **Register Callback**: `gpio_add_callback(gpio_spec.port, &cb_data)`
   - Attaches callback to the GPIO port

**Callback Function Signature**:
```c
void callback_name(const struct device *dev,
                   struct gpio_callback *cb,
                   uint32_t pins)
{
    /* pins bitmask shows which pins triggered this callback */
    /* dev is the GPIO port device */
    /* cb is the callback structure */
}
```

---

## 4. ADVANCED: OPTIONAL PIN HANDLING

### Safe Handling of Optional GPIO Pins

**Pattern Source**: `samples/basic/button/src/main.c` (lines 74-89)

```c
static struct gpio_dt_spec led = GPIO_DT_SPEC_GET_OR(DT_ALIAS(led0), gpios, {0});

int main(void)
{
    int ret;

    /* ... button setup code ... */

    /* Check if LED exists AND is ready */
    if (led.port && !gpio_is_ready_dt(&led)) {
        printk("Error: LED device %s is not ready; ignoring it\n",
               led.port->name);
        led.port = NULL;  /* Mark as unavailable */
    }

    /* Only configure if LED is available */
    if (led.port) {
        ret = gpio_pin_configure_dt(&led, GPIO_OUTPUT);
        if (ret != 0) {
            printk("Error: failed to configure LED\n");
            led.port = NULL;  /* Mark as unavailable */
        } else {
            printk("Set up LED at %s pin %d\n", led.port->name, led.pin);
        }
    }

    /* Use LED only if available */
    if (led.port) {
        gpio_pin_set_dt(&led, 1);  /* Set if exists */
    }
}
```

**Key Pattern**:
- Check `led.port != NULL` to detect if pin was configured
- Set `led.port = NULL` to disable unused pins
- Allows graceful degradation when optional GPIO is unavailable

---

## 5. DEVICE BINDING WITHOUT DEVICETREE (Advanced)

### Direct Device Reference Pattern

**Pattern Source**: `samples/drivers/misc/timeaware_gpio/src/main.c` (lines 23-38)

```c
#include <zephyr/drivers/misc/timeaware_gpio/timeaware_gpio.h>

#define TGPIO_LABEL DT_NODELABEL(tgpio)  /* Reference by node label */
#define TGPIO_PIN_IN  0
#define TGPIO_PIN_OUT 1

int main(void)
{
    const struct device *tgpio_dev;

    /* Get device handle using node label */
    tgpio_dev = DEVICE_DT_GET(TGPIO_LABEL);

    if (!device_is_ready(tgpio_dev)) {
        printk("[TGPIO] Bind failed\n");
        return -EINVAL;
    }

    printk("[TGPIO] Bind Success\n");

    /* Use device directly for specialized GPIO operations */
    tgpio_port_get_time(tgpio_dev, &tm);
    tgpio_pin_periodic_output(tgpio_dev, TGPIO_PIN_OUT, tm, cycles, true);
}
```

**Key Concepts**:
- `DT_NODELABEL(label)` - Reference devicetree node by label instead of alias
- `DEVICE_DT_GET()` - Get device pointer from devicetree
- `device_is_ready()` - Generic device readiness check
- Useful for specialized GPIO drivers (timeaware GPIO, PWM, etc.)

---

## 6. COMMON GPIO PATTERNS SUMMARY TABLE

| Task | Function | Example |
|------|----------|---------|
| Get GPIO from DT | `GPIO_DT_SPEC_GET()` | `static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(LED0_NODE, gpios);` |
| Get GPIO optional | `GPIO_DT_SPEC_GET_OR()` | `GPIO_DT_SPEC_GET_OR(DT_ALIAS(led0), gpios, {0})` |
| Check ready | `gpio_is_ready_dt()` | `if (!gpio_is_ready_dt(&led)) return;` |
| Configure output | `gpio_pin_configure_dt()` | `gpio_pin_configure_dt(&led, GPIO_OUTPUT_ACTIVE);` |
| Configure input | `gpio_pin_configure_dt()` | `gpio_pin_configure_dt(&button, GPIO_INPUT);` |
| Toggle output | `gpio_pin_toggle_dt()` | `gpio_pin_toggle_dt(&led);` |
| Set output | `gpio_pin_set_dt()` | `gpio_pin_set_dt(&led, 1);` |
| Read input | `gpio_pin_get_dt()` | `int val = gpio_pin_get_dt(&button);` |
| Setup interrupt | `gpio_pin_interrupt_configure_dt()` | `gpio_pin_interrupt_configure_dt(&btn, GPIO_INT_EDGE_TO_ACTIVE);` |
| Init callback | `gpio_init_callback()` | `gpio_init_callback(&cb, handler, BIT(pin));` |
| Register callback | `gpio_add_callback()` | `gpio_add_callback(button.port, &button_cb_data);` |

---

## 7. INCLUDES REQUIRED

```c
/* Standard GPIO operations */
#include <zephyr/drivers/gpio.h>

/* For interrupt-driven patterns */
#include <zephyr/kernel.h>

/* For device binding and utilities */
#include <zephyr/device.h>
#include <zephyr/sys/util.h>
#include <zephyr/sys/printk.h>

/* For specialized GPIO (e.g., timeaware) */
#include <zephyr/drivers/misc/timeaware_gpio/timeaware_gpio.h>

/* For standard utilities like PRIu32 */
#include <inttypes.h>
```

---

## 8. ERROR HANDLING PATTERNS

```c
/* Pattern 1: Check and return on failure */
if (!gpio_is_ready_dt(&led)) {
    return 0;
}

/* Pattern 2: Log and return on failure */
int ret = gpio_pin_configure_dt(&button, GPIO_INPUT);
if (ret != 0) {
    printk("Error %d: failed to configure\n", ret);
    return 0;
}

/* Pattern 3: Check positive value for success */
int val = gpio_pin_get_dt(&button);
if (val >= 0) {
    /* val is the pin state: 0 or 1 */
}

/* Pattern 4: Graceful degradation for optional features */
if (led.port && !gpio_is_ready_dt(&led)) {
    led.port = NULL;  /* Disable if unavailable */
}
if (led.port) {
    gpio_pin_set_dt(&led, 1);  /* Only use if available */
}
```

---

## 9. KEY DEVICETREE CONCEPTS

### Devicetree Aliases
From the samples, common aliases are:
- `led0` - Primary LED output
- `sw0` - Primary switch/button input
- `pwm_led0` - PWM-capable LED

### GPIO Specs in Devicetree
A typical GPIO spec looks like:
```dts
/* In .dts or .overlay file */
/ {
    aliases {
        led0 = &led0_gpio;
        sw0 = &button_gpio;
    };
};

&gpio0 {
    led0_gpio: led0 {
        gpios = <GPIO_PORT GPIO_PIN GPIO_FLAGS>;
    };
    button_gpio: button {
        gpios = <GPIO_PORT GPIO_PIN GPIO_FLAGS>;
    };
};
```

The `GPIO_DT_SPEC_GET()` macro automatically extracts:
- GPIO port device
- Pin number
- GPIO flags (active high/low, pull-up/down, etc.)

---

## 10. WORKFLOW QUICK REFERENCE

### Output Pin (LED) Workflow
```
1. Define: static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(LED0_NODE, gpios);
2. Check:  if (!gpio_is_ready_dt(&led)) return;
3. Config: gpio_pin_configure_dt(&led, GPIO_OUTPUT_ACTIVE);
4. Operate: gpio_pin_toggle_dt(&led); or gpio_pin_set_dt(&led, 1);
```

### Input Pin with Interrupt (Button) Workflow
```
1. Define: static const struct gpio_dt_spec button = GPIO_DT_SPEC_GET(SW0_NODE, gpios);
2. Callback: define void button_pressed(const struct device *dev, ...);
3. Check:  if (!gpio_is_ready_dt(&button)) return;
4. Config: gpio_pin_configure_dt(&button, GPIO_INPUT);
5. Interrupt: gpio_pin_interrupt_configure_dt(&button, GPIO_INT_EDGE_TO_ACTIVE);
6. Init CB: gpio_init_callback(&button_cb_data, button_pressed, BIT(button.pin));
7. Register: gpio_add_callback(button.port, &button_cb_data);
8. Loop: while(1) { k_msleep(...); }
```

---

## Sample Sources
- **blinky**: `samples/basic/blinky/src/main.c` - Basic output toggling
- **button**: `samples/basic/button/src/main.c` - Input with interrupts
- **timeaware_gpio**: `samples/drivers/misc/timeaware_gpio/src/main.c` - Device binding
- **blinky_pwm**: `samples/basic/blinky_pwm/src/main.c` - PWM-based GPIO control
