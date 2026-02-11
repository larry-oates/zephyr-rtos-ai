# Zephyr GPIO Quick Cheat Sheet

**Use this for quick lookup in skill implementations.**

## Minimal Output Example (Copy-Paste Ready)

```c
#include <zephyr/drivers/gpio.h>
#include <zephyr/kernel.h>

#define LED_NODE DT_ALIAS(led0)
static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(LED_NODE, gpios);

int main(void)
{
    if (!gpio_is_ready_dt(&led)) return -1;
    if (gpio_pin_configure_dt(&led, GPIO_OUTPUT_ACTIVE) < 0) return -1;

    while (1) {
        gpio_pin_toggle_dt(&led);
        k_msleep(1000);
    }
    return 0;
}
```

## Minimal Input + Interrupt Example

```c
#include <zephyr/drivers/gpio.h>
#include <zephyr/kernel.h>

#define BTN_NODE DT_ALIAS(sw0)
static const struct gpio_dt_spec button = GPIO_DT_SPEC_GET(BTN_NODE, gpios);
static struct gpio_callback btn_cb;

void button_handler(const struct device *dev, struct gpio_callback *cb, uint32_t pins)
{
    printk("Button pressed\n");
}

int main(void)
{
    if (!gpio_is_ready_dt(&button)) return -1;
    if (gpio_pin_configure_dt(&button, GPIO_INPUT) < 0) return -1;
    if (gpio_pin_interrupt_configure_dt(&button, GPIO_INT_EDGE_TO_ACTIVE) < 0) return -1;

    gpio_init_callback(&btn_cb, button_handler, BIT(button.pin));
    gpio_add_callback(button.port, &btn_cb);

    while (1) k_msleep(100);
    return 0;
}
```

## Function Quick Lookup

| Need | Use | Notes |
|------|-----|-------|
| Get GPIO from DT | `GPIO_DT_SPEC_GET(NODE, gpios)` | For required pins |
| Get GPIO (optional) | `GPIO_DT_SPEC_GET_OR(NODE, gpios, {0})` | Allows missing pins |
| Check device ready | `gpio_is_ready_dt(&spec)` | Always check first |
| Configure output | `gpio_pin_configure_dt(&spec, GPIO_OUTPUT_ACTIVE)` | `_ACTIVE` or `_INACTIVE` start state |
| Configure input | `gpio_pin_configure_dt(&spec, GPIO_INPUT)` | For buttons/sensors |
| Toggle output | `gpio_pin_toggle_dt(&spec)` | Flip current state |
| Set output | `gpio_pin_set_dt(&spec, 0 or 1)` | 0=LOW, 1=HIGH |
| Read input | `gpio_pin_get_dt(&spec)` | Returns 0, 1, or negative error |
| Setup interrupt | `gpio_pin_interrupt_configure_dt(&spec, TYPE)` | See interrupt types below |
| Init callback | `gpio_init_callback(&cb, handler, BIT(pin))` | Must do before add_callback |
| Register callback | `gpio_add_callback(spec.port, &cb)` | Attaches to port |

## Interrupt Types

```c
GPIO_INT_EDGE_TO_ACTIVE      // Rising edge (0→1)
GPIO_INT_EDGE_TO_INACTIVE    // Falling edge (1→0)
GPIO_INT_LEVEL_ACTIVE        // While HIGH
GPIO_INT_LEVEL_INACTIVE      // While LOW
GPIO_INT_EDGE                // Both edges (some platforms)
```

## Error Checking Patterns

```c
// Pattern: Check boolean result
if (!gpio_is_ready_dt(&led)) {
    return -ENODEV;
}

// Pattern: Check return code
int ret = gpio_pin_configure_dt(&led, GPIO_OUTPUT_ACTIVE);
if (ret < 0) {
    printk("Config failed: %d\n", ret);
    return ret;
}

// Pattern: Check positive value from get
int state = gpio_pin_get_dt(&button);
if (state >= 0) {
    // state is 0 or 1
}

// Pattern: Optional with graceful fallback
if (led.port && !gpio_is_ready_dt(&led)) {
    led.port = NULL;  // Disable this pin
}
if (led.port) {
    gpio_pin_set_dt(&led, 1);  // Use only if available
}
```

## Devicetree Aliases

Common aliases to use with `DT_ALIAS()`:
- `led0` - Primary LED
- `sw0` - Primary button/switch
- `pwm_led0` - PWM-capable LED
- `led1`, `sw1`, etc. - Secondary devices

These must be defined in your board's `.dts` or `.overlay` file.

## Callback Signature

```c
void my_callback(const struct device *dev,
                 struct gpio_callback *cb,
                 uint32_t pins)
{
    // dev: GPIO port device
    // cb: The callback structure (contains private data)
    // pins: Bitmask of which pins triggered (use to handle multiple pins)

    if (pins & BIT(my_pin_number)) {
        // Pin number my_pin_number triggered
    }
}
```

## Includes

```c
#include <zephyr/drivers/gpio.h>      // Main GPIO API
#include <zephyr/kernel.h>            // k_msleep, k_sleep, etc.
#include <zephyr/device.h>            // device_is_ready(), etc.
#include <zephyr/sys/util.h>          // BIT() macro
#include <zephyr/sys/printk.h>        // printk()
```

## Common Mistakes to Avoid

❌ **Don't**: Call configure/set before checking `gpio_is_ready_dt()`
✓ **Do**: Always check readiness first

❌ **Don't**: Forget to register callback with `gpio_add_callback()`
✓ **Do**: Call `gpio_init_callback()` THEN `gpio_add_callback()`

❌ **Don't**: Use `gpio_pin_interrupt_configure_dt()` without input config
✓ **Do**: Configure as INPUT first, then setup interrupt

❌ **Don't**: Check `return < 0` for `gpio_pin_get_dt()` (it returns 0/1 for success)
✓ **Do**: Check `return >= 0` for `gpio_pin_get_dt()`

❌ **Don't**: Assume optional pins exist
✓ **Do**: Check `gpio_spec.port != NULL` before using optional pins

❌ **Don't**: Ignore return codes
✓ **Do**: Check all return values and log errors

## Workflow Sequences

### Turn On LED, Wait, Turn Off
```c
gpio_pin_set_dt(&led, 1);      // ON
k_msleep(1000);                // Wait 1 sec
gpio_pin_set_dt(&led, 0);      // OFF
```

### Blink N Times
```c
for (int i = 0; i < 10; i++) {
    gpio_pin_toggle_dt(&led);
    k_msleep(250);
}
```

### Wait for Button Press (Polling - NOT recommended)
```c
while (gpio_pin_get_dt(&button) == 0) {
    k_msleep(10);  // Poll every 10ms
}
printk("Button pressed\n");
```

### Wait for Button Press (Interrupts - RECOMMENDED)
```c
// Setup in main (see above)
// Then just sleep - handler will be called
while (1) {
    k_msleep(100);
}
```

### Mirror Button State to LED
```c
int state = gpio_pin_get_dt(&button);
if (state >= 0) {
    gpio_pin_set_dt(&led, state);  // Same as button
}
```

## Key Files to Reference

- `zephyr/samples/basic/blinky/src/main.c` - Basic output
- `zephyr/samples/basic/button/src/main.c` - Input + interrupts
- `zephyr/samples/basic/blinky_pwm/src/main.c` - PWM-based GPIO
- `zephyr/include/zephyr/drivers/gpio.h` - Complete API definitions
