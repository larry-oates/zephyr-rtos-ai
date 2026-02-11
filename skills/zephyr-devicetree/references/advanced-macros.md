# Advanced Devicetree C Macros

Iteration macros, string helpers, and bus-specific conveniences beyond basic property access.

## Iteration Macros

### DT_FOREACH_STATUS_OKAY

Iterate over all nodes with a given compatible that are enabled:

```c
#define DT_DRV_COMPAT vendor_device

/* Generate code for each instance */
#define CREATE_INSTANCE(inst) \
    static struct my_data data_##inst; \
    static const struct my_config config_##inst = { \
        .reg = DT_INST_REG_ADDR(inst), \
    }; \
    DEVICE_DT_INST_DEFINE(inst, my_init, NULL, \
                          &data_##inst, &config_##inst, \
                          POST_KERNEL, CONFIG_MY_INIT_PRIORITY, \
                          &my_api);

DT_INST_FOREACH_STATUS_OKAY(CREATE_INSTANCE)
```

### DT_FOREACH_CHILD

Iterate over all children of a node:

```c
#define LED_NODE DT_PATH(leds)

#define COUNT_LED(node_id) + 1
#define NUM_LEDS (0 DT_FOREACH_CHILD(LED_NODE, COUNT_LED))

#define LED_GPIO_SPEC(node_id) GPIO_DT_SPEC_GET(node_id, gpios),
static const struct gpio_dt_spec leds[] = {
    DT_FOREACH_CHILD(LED_NODE, LED_GPIO_SPEC)
};
```

### DT_FOREACH_CHILD_STATUS_OKAY

Same as above, but only enabled children:

```c
#define INIT_BUTTON(node_id) init_button(GPIO_DT_SPEC_GET(node_id, gpios));

void init_all_buttons(void) {
    DT_FOREACH_CHILD_STATUS_OKAY(DT_PATH(buttons), INIT_BUTTON)
}
```

### DT_FOREACH_PROP_ELEM

Iterate over array property elements:

```c
#define MY_NODE DT_NODELABEL(my_device)

/* For array property: my-values = <1 2 3 4>; */
#define PRINT_ELEM(node_id, prop, idx) \
    printk("Element %d: %d\n", idx, DT_PROP_BY_IDX(node_id, prop, idx));

void print_values(void) {
    DT_FOREACH_PROP_ELEM(MY_NODE, my_values, PRINT_ELEM)
}

/* Collect into array */
#define GET_ELEM(node_id, prop, idx) DT_PROP_BY_IDX(node_id, prop, idx),
static const int values[] = {
    DT_FOREACH_PROP_ELEM(MY_NODE, my_values, GET_ELEM)
};
```

### DT_FOREACH_PROP_ELEM_SEP

With custom separator:

```c
#define GET_VAL(node_id, prop, idx) DT_PROP_BY_IDX(node_id, prop, idx)

/* Generates: val1 | val2 | val3 */
#define MY_FLAGS DT_FOREACH_PROP_ELEM_SEP(MY_NODE, flags, GET_VAL, (|))
```

## String Macros

### DT_STRING_TOKEN

Convert string property to C token (for enums, switch statements):

```c
/* DTS: operating-mode = "high-performance"; */

#define MODE DT_STRING_TOKEN(MY_NODE, operating_mode)
/* Expands to: high_performance (underscores replace hyphens) */

switch (MODE) {
    case low_power: /* ... */ break;
    case normal: /* ... */ break;
    case high_performance: /* ... */ break;
}
```

### DT_STRING_UPPER_TOKEN

Uppercase version:

```c
#define MODE DT_STRING_UPPER_TOKEN(MY_NODE, operating_mode)
/* Expands to: HIGH_PERFORMANCE */
```

### DT_STRING_UNQUOTED

Get string without quotes (for macro concatenation):

```c
/* DTS: prefix = "my"; */
#define PREFIX DT_STRING_UNQUOTED(MY_NODE, prefix)
/* Can use in: PREFIX##_function() */
```

### DT_PROP_BY_IDX for String Arrays

```c
/* DTS: names = "alice", "bob", "charlie"; */

const char *name0 = DT_PROP_BY_IDX(MY_NODE, names, 0);  /* "alice" */
const char *name1 = DT_PROP_BY_IDX(MY_NODE, names, 1);  /* "bob" */
```

## Bus-Specific Macros

### GPIO

```c
#define MY_NODE DT_NODELABEL(my_device)

/* Get GPIO spec (preferred) */
static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(MY_NODE, gpios);
/* Or with index: */
static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET_BY_IDX(MY_NODE, gpios, 0);

/* Individual components */
DT_GPIO_CTLR(node_id, prop)         /* GPIO controller phandle */
DT_GPIO_PIN(node_id, prop)          /* Pin number */
DT_GPIO_FLAGS(node_id, prop)        /* Flags */

/* Usage */
gpio_pin_configure_dt(&led, GPIO_OUTPUT_ACTIVE);
gpio_pin_set_dt(&led, 1);
```

### I2C

```c
#define SENSOR_NODE DT_NODELABEL(my_sensor)

/* Get I2C device spec */
static const struct i2c_dt_spec sensor = I2C_DT_SPEC_GET(SENSOR_NODE);

/* Components */
DT_REG_ADDR(SENSOR_NODE)  /* I2C address */
DT_BUS(SENSOR_NODE)       /* Parent I2C controller node */

/* Usage */
i2c_write_dt(&sensor, data, sizeof(data));
```

### SPI

```c
#define FLASH_NODE DT_NODELABEL(ext_flash)

/* Get SPI device spec */
static const struct spi_dt_spec flash = SPI_DT_SPEC_GET(FLASH_NODE,
                                                        SPI_WORD_SET(8) | SPI_TRANSFER_MSB,
                                                        0);

/* Components */
DT_REG_ADDR(FLASH_NODE)                /* Chip select index */
DT_PROP(FLASH_NODE, spi_max_frequency) /* Max frequency */

/* Usage */
spi_write_dt(&flash, &tx_bufs);
```

### PWM

```c
#define BUZZER_NODE DT_NODELABEL(buzzer)

/* Get PWM spec */
static const struct pwm_dt_spec buzzer = PWM_DT_SPEC_GET(BUZZER_NODE);

/* Components */
DT_PWMS_CTLR(node_id)     /* PWM controller */
DT_PWMS_CHANNEL(node_id)  /* Channel */
DT_PWMS_PERIOD(node_id)   /* Period in ns */
DT_PWMS_FLAGS(node_id)    /* Flags */

/* Usage */
pwm_set_pulse_dt(&buzzer, period / 2);
```

## Existence and Conditional Macros

### Node Existence

```c
#if DT_NODE_EXISTS(DT_NODELABEL(optional_device))
    /* Code for when node exists */
#endif

#if DT_NODE_HAS_STATUS(DT_NODELABEL(uart0), okay)
    /* Code for when node is enabled */
#endif

#if DT_HAS_COMPAT_STATUS_OKAY(vendor_device)
    /* At least one vendor,device node is enabled */
#endif
```

### Property Existence

```c
#if DT_NODE_HAS_PROP(MY_NODE, optional_prop)
    int val = DT_PROP(MY_NODE, optional_prop);
#else
    int val = DEFAULT_VALUE;
#endif

/* Or use default: */
int val = DT_PROP_OR(MY_NODE, optional_prop, DEFAULT_VALUE);
```

### Compile-Time Conditionals

```c
/* COND versions return 1 or 0 instead of being undefined */
BUILD_ASSERT(DT_NODE_HAS_STATUS(DT_CHOSEN(zephyr_console), okay),
             "Console device must be enabled");

/* Use in ternary */
#define MY_SIZE DT_COND_NODE_HAS_PROP(MY_NODE, size, \
                                       DT_PROP(MY_NODE, size), \
                                       DEFAULT_SIZE)
```

## Instance Macros (For Drivers)

When writing drivers, use instance macros with `DT_DRV_COMPAT`:

```c
#define DT_DRV_COMPAT vendor_my_device

/* Instance versions of all macros */
DT_INST_REG_ADDR(inst)
DT_INST_PROP(inst, property)
DT_INST_IRQN(inst)
DT_INST_GPIO_PIN(inst, gpios)
DT_INST_FOREACH_STATUS_OKAY(fn)

/* Example driver pattern */
#define MY_DEVICE_INIT(inst)                                    \
    static struct my_data my_data_##inst;                       \
    static const struct my_config my_config_##inst = {          \
        .base = DT_INST_REG_ADDR(inst),                         \
        .irq = DT_INST_IRQN(inst),                              \
        .speed = DT_INST_PROP_OR(inst, speed, 100000),          \
    };                                                          \
    DEVICE_DT_INST_DEFINE(inst,                                 \
                          my_init,                              \
                          NULL,                                 \
                          &my_data_##inst,                      \
                          &my_config_##inst,                    \
                          POST_KERNEL,                          \
                          CONFIG_MY_DRIVER_INIT_PRIORITY,       \
                          &my_driver_api);

DT_INST_FOREACH_STATUS_OKAY(MY_DEVICE_INIT)
```

## Phandle Navigation

```c
/* Get node from phandle property */
#define PARENT_CTRL DT_PHANDLE(MY_NODE, parent_controller)

/* Phandle array navigation */
DT_PHANDLE_BY_IDX(node_id, prop, idx)
DT_PHANDLE_BY_NAME(node_id, prop, name)

/* Check if phandle exists */
DT_NODE_HAS_PROP(MY_NODE, optional_phandle)
```

## Tips

1. **Use _dt_spec structs** — `gpio_dt_spec`, `i2c_dt_spec`, etc. are cleaner than raw macros
2. **FOREACH for arrays** — More maintainable than manual indexing
3. **DT_INST_* in drivers** — Enables multi-instance drivers automatically
4. **Check generated header** — See `devicetree_generated.h` for actual macro expansions
5. **Static initialization** — All DT_* macros are compile-time constants
