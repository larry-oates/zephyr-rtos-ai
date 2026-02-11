# GPIO API Reference

Complete reference for Zephyr GPIO driver API functions.

## Core Structures

### gpio_dt_spec

Container for GPIO pin information from devicetree.

```c
struct gpio_dt_spec {
    const struct device *port;  /* GPIO controller device pointer */
    gpio_pin_t pin;             /* Pin number (0-31 typical) */
    gpio_dt_flags_t dt_flags;   /* Flags from devicetree */
};
```

### gpio_callback

Callback structure for interrupt handling.

```c
struct gpio_callback {
    sys_snode_t node;                                           /* Linked list node */
    gpio_callback_handler_t handler;                            /* Callback function */
    gpio_port_pins_t pin_mask;                                  /* Pins triggering callback */
};

/* Callback handler signature */
typedef void (*gpio_callback_handler_t)(const struct device *port,
                                        struct gpio_callback *cb,
                                        gpio_port_pins_t pins);
```

## Devicetree Macros

### GPIO_DT_SPEC_GET

Get gpio_dt_spec from devicetree node property.

```c
GPIO_DT_SPEC_GET(node_id, prop)
GPIO_DT_SPEC_GET_BY_IDX(node_id, prop, idx)  /* For phandle arrays */
GPIO_DT_SPEC_GET_OR(node_id, prop, default_value)
```

**Example:**
```c
#define LED_NODE DT_ALIAS(led0)
static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(LED_NODE, gpios);
```

### GPIO_DT_SPEC_INST_GET

Get gpio_dt_spec using instance number (for drivers).

```c
GPIO_DT_SPEC_INST_GET(inst, prop)
GPIO_DT_SPEC_INST_GET_BY_IDX(inst, prop, idx)
```

## Pin Configuration

### gpio_pin_configure_dt

Configure pin using devicetree spec.

```c
int gpio_pin_configure_dt(const struct gpio_dt_spec *spec, gpio_flags_t extra_flags);
```

**Parameters:**
- `spec`: GPIO specification from devicetree
- `extra_flags`: Additional flags to OR with dt_flags

**Returns:** 0 on success, negative errno on failure

**Example:**
```c
gpio_pin_configure_dt(&led, GPIO_OUTPUT_ACTIVE);
gpio_pin_configure_dt(&button, GPIO_INPUT);
```

### gpio_pin_configure

Configure pin using raw device/pin.

```c
int gpio_pin_configure(const struct device *port, gpio_pin_t pin, gpio_flags_t flags);
```

## Pin Read/Write

### gpio_pin_get_dt / gpio_pin_get

Read logical pin value (respects ACTIVE_LOW).

```c
int gpio_pin_get_dt(const struct gpio_dt_spec *spec);
int gpio_pin_get(const struct device *port, gpio_pin_t pin);
```

**Returns:**
- 0: Inactive (low for ACTIVE_HIGH, high for ACTIVE_LOW)
- 1: Active
- Negative: Error

### gpio_pin_get_raw

Read physical pin value (ignores ACTIVE_LOW).

```c
int gpio_pin_get_raw(const struct device *port, gpio_pin_t pin);
```

**Returns:** 0 or 1 for physical level, negative on error

### gpio_pin_set_dt / gpio_pin_set

Set logical pin value (respects ACTIVE_LOW).

```c
int gpio_pin_set_dt(const struct gpio_dt_spec *spec, int value);
int gpio_pin_set(const struct device *port, gpio_pin_t pin, int value);
```

**Parameters:**
- `value`: 0 for inactive, non-zero for active

### gpio_pin_set_raw

Set physical pin value (ignores ACTIVE_LOW).

```c
int gpio_pin_set_raw(const struct device *port, gpio_pin_t pin, int value);
```

### gpio_pin_toggle_dt / gpio_pin_toggle

Toggle pin output.

```c
int gpio_pin_toggle_dt(const struct gpio_dt_spec *spec);
int gpio_pin_toggle(const struct device *port, gpio_pin_t pin);
```

## Port Operations

For multi-pin operations on same port.

### gpio_port_get_raw

Read all pins on port.

```c
int gpio_port_get_raw(const struct device *port, gpio_port_value_t *value);
```

### gpio_port_set_masked_raw

Set multiple pins with mask.

```c
int gpio_port_set_masked_raw(const struct device *port,
                             gpio_port_pins_t mask,
                             gpio_port_value_t value);
```

### gpio_port_set_bits_raw / gpio_port_clear_bits_raw

Set or clear specific bits.

```c
int gpio_port_set_bits_raw(const struct device *port, gpio_port_pins_t pins);
int gpio_port_clear_bits_raw(const struct device *port, gpio_port_pins_t pins);
```

### gpio_port_toggle_bits

Toggle multiple pins.

```c
int gpio_port_toggle_bits(const struct device *port, gpio_port_pins_t pins);
```

## Interrupt Configuration

### gpio_pin_interrupt_configure_dt

Configure interrupt using devicetree spec.

```c
int gpio_pin_interrupt_configure_dt(const struct gpio_dt_spec *spec, gpio_flags_t flags);
```

**Common flag combinations:**
- `GPIO_INT_EDGE_TO_ACTIVE`: Interrupt on transition to active state
- `GPIO_INT_EDGE_TO_INACTIVE`: Interrupt on transition to inactive state
- `GPIO_INT_EDGE_BOTH`: Interrupt on any transition
- `GPIO_INT_LEVEL_ACTIVE`: Level-triggered when active
- `GPIO_INT_DISABLE`: Disable interrupt

### gpio_pin_interrupt_configure

Configure interrupt using raw device/pin.

```c
int gpio_pin_interrupt_configure(const struct device *port,
                                 gpio_pin_t pin,
                                 gpio_flags_t flags);
```

## Callback Management

### gpio_init_callback

Initialize callback structure.

```c
void gpio_init_callback(struct gpio_callback *callback,
                        gpio_callback_handler_t handler,
                        gpio_port_pins_t pin_mask);
```

**Parameters:**
- `callback`: Callback struct to initialize
- `handler`: Function to call on interrupt
- `pin_mask`: Bitmask of pins (use `BIT(pin)`)

**Example:**
```c
static struct gpio_callback button_cb;
gpio_init_callback(&button_cb, button_handler, BIT(button.pin));
```

### gpio_add_callback

Register callback with GPIO port.

```c
int gpio_add_callback(const struct device *port, struct gpio_callback *callback);
```

### gpio_remove_callback

Unregister callback.

```c
int gpio_remove_callback(const struct device *port, struct gpio_callback *callback);
```

## Device Readiness

### gpio_is_ready_dt

Check if GPIO device is ready.

```c
bool gpio_is_ready_dt(const struct gpio_dt_spec *spec);
```

**Example:**
```c
if (!gpio_is_ready_dt(&led)) {
    return -ENODEV;
}
```

## Configuration Flags

### Direction Flags

| Flag | Value | Description |
|------|-------|-------------|
| `GPIO_INPUT` | (1 << 0) | Configure as input |
| `GPIO_OUTPUT` | (1 << 1) | Configure as output |
| `GPIO_OUTPUT_INACTIVE` | GPIO_OUTPUT | Output, initial inactive |
| `GPIO_OUTPUT_ACTIVE` | GPIO_OUTPUT \| GPIO_OUTPUT_INIT_HIGH | Output, initial active |
| `GPIO_OUTPUT_LOW` | GPIO_OUTPUT \| GPIO_OUTPUT_INIT_LOW | Output, initial low |
| `GPIO_OUTPUT_HIGH` | GPIO_OUTPUT \| GPIO_OUTPUT_INIT_HIGH | Output, initial high |

### Active Level Flags

| Flag | Value | Description |
|------|-------|-------------|
| `GPIO_ACTIVE_LOW` | (1 << 4) | Active = physical low |
| `GPIO_ACTIVE_HIGH` | 0 | Active = physical high (default) |

### Pull Resistor Flags

| Flag | Value | Description |
|------|-------|-------------|
| `GPIO_PULL_UP` | (1 << 8) | Enable pull-up |
| `GPIO_PULL_DOWN` | (1 << 9) | Enable pull-down |

### Drive Mode Flags

| Flag | Description |
|------|-------------|
| `GPIO_OPEN_DRAIN` | Open-drain output |
| `GPIO_OPEN_SOURCE` | Open-source output |

### Interrupt Trigger Flags

| Flag | Description |
|------|-------------|
| `GPIO_INT_DISABLE` | Disable interrupt |
| `GPIO_INT_EDGE_RISING` | Rising edge trigger |
| `GPIO_INT_EDGE_FALLING` | Falling edge trigger |
| `GPIO_INT_EDGE_BOTH` | Both edges trigger |
| `GPIO_INT_LEVEL_LOW` | Low level trigger |
| `GPIO_INT_LEVEL_HIGH` | High level trigger |
| `GPIO_INT_EDGE_TO_ACTIVE` | Edge to active (respects ACTIVE_LOW) |
| `GPIO_INT_EDGE_TO_INACTIVE` | Edge to inactive |
| `GPIO_INT_LEVEL_ACTIVE` | Level active |
| `GPIO_INT_LEVEL_INACTIVE` | Level inactive |

## Error Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| -ENODEV | Device not found or not ready |
| -ENOTSUP | Operation not supported |
| -EINVAL | Invalid argument (pin number, flags) |
| -EIO | I/O error |
| -EBUSY | Resource busy |
