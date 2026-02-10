# Creating Custom Drivers

## Table of Contents

1. [Overview](#overview)
2. [Step 1: Devicetree Binding](#step-1-devicetree-binding)
3. [Step 2: Kconfig](#step-2-kconfig)
4. [Step 3: Driver Implementation](#step-3-driver-implementation)
5. [Step 4: CMake Integration](#step-4-cmake-integration)
6. [Step 5: Devicetree Node](#step-5-devicetree-node)
7. [Step 6: Application Configuration](#step-6-application-configuration)
8. [Complete Example](#complete-example)

---

## Overview

Creating a Zephyr driver involves these files:

```
my_project/
├── drivers/
│   └── mydriver/
│       ├── CMakeLists.txt
│       ├── Kconfig
│       └── mydriver.c
├── dts/bindings/
│   └── vendor,mydriver.yaml
├── boards/
│   └── myboard.overlay     # Or app overlay
├── prj.conf
└── CMakeLists.txt          # Top-level
```

---

## Step 1: Devicetree Binding

Create `dts/bindings/vendor,mydriver.yaml`:

```yaml
description: Vendor MyDriver device

compatible: "vendor,mydriver"

include: base.yaml

properties:
  reg:
    required: true
    description: I2C address or register base

  int-gpios:
    type: phandle-array
    description: Interrupt GPIO

  sample-rate:
    type: int
    default: 100
    description: Sample rate in Hz

  mode:
    type: string
    enum:
      - "low-power"
      - "normal"
      - "high-performance"
    default: "normal"
    description: Operating mode
```

### Common Binding Includes

| Include | For | Provides |
|---------|-----|----------|
| `base.yaml` | All devices | `status`, `compatible`, `label` |
| `i2c-device.yaml` | I2C devices | `reg` (I2C address) |
| `spi-device.yaml` | SPI devices | `reg`, `spi-max-frequency` |
| `gpio-controller.yaml` | GPIO controllers | `gpio-cells`, `#gpio-cells` |

### For I2C Device

```yaml
description: I2C sensor

compatible: "vendor,i2c-sensor"

include: [i2c-device.yaml]

properties:
  int-gpios:
    type: phandle-array
```

### For SPI Device

```yaml
description: SPI device

compatible: "vendor,spi-device"

include: [spi-device.yaml]

properties:
  reset-gpios:
    type: phandle-array
```

---

## Step 2: Kconfig

Create `drivers/mydriver/Kconfig`:

```kconfig
# Mydriver configuration

menuconfig MYDRIVER
    bool "My custom driver"
    default y
    depends on I2C
    help
      Enable support for the vendor mydriver device.

if MYDRIVER

config MYDRIVER_INIT_PRIORITY
    int "Init priority"
    default 90
    help
      Device driver initialization priority.

config MYDRIVER_TRIGGER
    bool "Enable trigger support"
    help
      Enable interrupt-based trigger support.

config MYDRIVER_LOG_LEVEL
    int "Log level"
    default 3
    range 0 4
    help
      Log level for mydriver (0=OFF, 4=DEBUG).

endif # MYDRIVER
```

### Kconfig Best Practices

1. Use `menuconfig` for main driver option
2. Add `depends on` for required subsystems
3. Nest options under `if MYDRIVER` block
4. Provide sensible defaults
5. Add `help` text for all options

---

## Step 3: Driver Implementation

Create `drivers/mydriver/mydriver.c`:

```c
#define DT_DRV_COMPAT vendor_mydriver

#include <zephyr/device.h>
#include <zephyr/drivers/i2c.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(mydriver, CONFIG_MYDRIVER_LOG_LEVEL);

/* Configuration structure - stored in flash */
struct mydriver_config {
    struct i2c_dt_spec i2c;
    struct gpio_dt_spec int_gpio;
    uint32_t sample_rate;
};

/* Runtime data - stored in RAM */
struct mydriver_data {
    struct k_sem lock;
    uint8_t last_reading;
    bool initialized;
};

/* Driver API functions */
static int mydriver_read(const struct device *dev, uint8_t *value)
{
    const struct mydriver_config *cfg = dev->config;
    struct mydriver_data *data = dev->data;
    int ret;

    k_sem_take(&data->lock, K_FOREVER);

    ret = i2c_read_dt(&cfg->i2c, value, 1);
    if (ret == 0) {
        data->last_reading = *value;
    }

    k_sem_give(&data->lock);
    return ret;
}

static int mydriver_write(const struct device *dev, uint8_t value)
{
    const struct mydriver_config *cfg = dev->config;
    struct mydriver_data *data = dev->data;
    int ret;

    k_sem_take(&data->lock, K_FOREVER);
    ret = i2c_write_dt(&cfg->i2c, &value, 1);
    k_sem_give(&data->lock);

    return ret;
}

/* Define API structure (optional, for subsystem integration) */
struct mydriver_api {
    int (*read)(const struct device *dev, uint8_t *value);
    int (*write)(const struct device *dev, uint8_t value);
};

static const struct mydriver_api mydriver_api_funcs = {
    .read = mydriver_read,
    .write = mydriver_write,
};

/* Initialization function */
static int mydriver_init(const struct device *dev)
{
    const struct mydriver_config *cfg = dev->config;
    struct mydriver_data *data = dev->data;
    int ret;

    LOG_DBG("Initializing %s", dev->name);

    /* Check I2C bus is ready */
    if (!i2c_is_ready_dt(&cfg->i2c)) {
        LOG_ERR("I2C bus not ready");
        return -ENODEV;
    }

    /* Configure interrupt GPIO if present */
    if (cfg->int_gpio.port != NULL) {
        if (!gpio_is_ready_dt(&cfg->int_gpio)) {
            LOG_ERR("Interrupt GPIO not ready");
            return -ENODEV;
        }

        ret = gpio_pin_configure_dt(&cfg->int_gpio, GPIO_INPUT);
        if (ret < 0) {
            LOG_ERR("Failed to configure interrupt GPIO");
            return ret;
        }
    }

    /* Initialize synchronization */
    k_sem_init(&data->lock, 1, 1);

    /* Verify device communication (e.g., read chip ID) */
    uint8_t chip_id;
    ret = i2c_read_dt(&cfg->i2c, &chip_id, 1);
    if (ret < 0) {
        LOG_ERR("Failed to read chip ID");
        return ret;
    }

    LOG_INF("Device %s initialized, chip ID: 0x%02x", dev->name, chip_id);
    data->initialized = true;

    return 0;
}

/* Device instantiation macro */
#define MYDRIVER_DEFINE(inst)                                              \
    static struct mydriver_data mydriver_data_##inst;                      \
                                                                           \
    static const struct mydriver_config mydriver_config_##inst = {         \
        .i2c = I2C_DT_SPEC_INST_GET(inst),                                 \
        .int_gpio = GPIO_DT_SPEC_INST_GET_OR(inst, int_gpios, {0}),        \
        .sample_rate = DT_INST_PROP(inst, sample_rate),                    \
    };                                                                     \
                                                                           \
    DEVICE_DT_INST_DEFINE(inst,                                            \
                          mydriver_init,                                   \
                          NULL,                                            \
                          &mydriver_data_##inst,                           \
                          &mydriver_config_##inst,                         \
                          POST_KERNEL,                                     \
                          CONFIG_MYDRIVER_INIT_PRIORITY,                   \
                          &mydriver_api_funcs);

/* Instantiate for all enabled nodes */
DT_INST_FOREACH_STATUS_OKAY(MYDRIVER_DEFINE)
```

### Key Patterns

1. **`DT_DRV_COMPAT`**: Must match `compatible` with underscores
2. **Config initialization**: Use `DT_INST_*` macros in config struct
3. **Check dependencies**: Verify bus/GPIO ready before use
4. **Logging**: Use `LOG_MODULE_REGISTER` with Kconfig level
5. **Thread safety**: Use k_sem/k_mutex for shared state

---

## Step 4: CMake Integration

### Driver CMakeLists.txt

Create `drivers/mydriver/CMakeLists.txt`:

```cmake
# Only build if Kconfig is enabled
zephyr_library_sources_ifdef(CONFIG_MYDRIVER mydriver.c)
```

### Top-Level CMakeLists.txt

In your application's `CMakeLists.txt`:

```cmake
cmake_minimum_required(VERSION 3.20.0)

# Add custom drivers BEFORE find_package
list(APPEND ZEPHYR_EXTRA_MODULES ${CMAKE_CURRENT_SOURCE_DIR}/drivers/mydriver)

# Add custom bindings
list(APPEND DTS_ROOT ${CMAKE_CURRENT_SOURCE_DIR})

find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(my_app)

target_sources(app PRIVATE src/main.c)
```

### Alternative: Kconfig include

Add to application's `Kconfig`:

```kconfig
menu "Custom Drivers"

rsource "drivers/mydriver/Kconfig"

endmenu
```

---

## Step 5: Devicetree Node

Add to board overlay or `boards/myboard.overlay`:

```dts
&i2c0 {
    status = "okay";

    mydevice: mydriver@48 {
        compatible = "vendor,mydriver";
        reg = <0x48>;
        int-gpios = <&gpio0 15 GPIO_ACTIVE_LOW>;
        sample-rate = <200>;
    };
};
```

---

## Step 6: Application Configuration

### prj.conf

```ini
CONFIG_I2C=y
CONFIG_GPIO=y
CONFIG_MYDRIVER=y
CONFIG_MYDRIVER_INIT_PRIORITY=90
CONFIG_LOG=y
CONFIG_MYDRIVER_LOG_LEVEL=4
```

### Using the Driver in Application

```c
#include <zephyr/device.h>

/* Get device handle */
const struct device *mydev = DEVICE_DT_GET(DT_NODELABEL(mydevice));

int main(void)
{
    if (!device_is_ready(mydev)) {
        printk("Device not ready\n");
        return -1;
    }

    /* Access driver API */
    const struct mydriver_api *api = mydev->api;
    uint8_t value;
    api->read(mydev, &value);

    return 0;
}
```

---

## Complete Example

### Directory Structure

```
my_app/
├── CMakeLists.txt
├── prj.conf
├── src/
│   └── main.c
├── boards/
│   └── nrf52dk_nrf52832.overlay
├── drivers/
│   └── temp_sensor/
│       ├── CMakeLists.txt
│       ├── Kconfig
│       └── temp_sensor.c
└── dts/bindings/
    └── acme,temp-sensor.yaml
```

### Binding: `dts/bindings/acme,temp-sensor.yaml`

```yaml
description: ACME temperature sensor

compatible: "acme,temp-sensor"

include: [i2c-device.yaml]

properties:
  resolution:
    type: int
    default: 12
    enum: [9, 10, 11, 12]
    description: ADC resolution in bits
```

### Kconfig: `drivers/temp_sensor/Kconfig`

```kconfig
config ACME_TEMP_SENSOR
    bool "ACME temperature sensor driver"
    default y
    depends on I2C
    select SENSOR

config ACME_TEMP_SENSOR_INIT_PRIORITY
    int "Init priority"
    default 90
    depends on ACME_TEMP_SENSOR
```

### Driver: `drivers/temp_sensor/temp_sensor.c`

```c
#define DT_DRV_COMPAT acme_temp_sensor

#include <zephyr/device.h>
#include <zephyr/drivers/i2c.h>
#include <zephyr/drivers/sensor.h>

struct temp_sensor_config {
    struct i2c_dt_spec i2c;
    uint8_t resolution;
};

struct temp_sensor_data {
    int32_t temp_raw;
};

static int temp_sensor_sample_fetch(const struct device *dev,
                                    enum sensor_channel chan)
{
    const struct temp_sensor_config *cfg = dev->config;
    struct temp_sensor_data *data = dev->data;
    uint8_t buf[2];
    int ret;

    ret = i2c_read_dt(&cfg->i2c, buf, sizeof(buf));
    if (ret < 0) {
        return ret;
    }

    data->temp_raw = (buf[0] << 8) | buf[1];
    return 0;
}

static int temp_sensor_channel_get(const struct device *dev,
                                   enum sensor_channel chan,
                                   struct sensor_value *val)
{
    struct temp_sensor_data *data = dev->data;

    if (chan != SENSOR_CHAN_AMBIENT_TEMP) {
        return -ENOTSUP;
    }

    /* Convert raw to celsius (example: 0.0625 per LSB for 12-bit) */
    int32_t temp_mc = (data->temp_raw * 625) / 10;  /* millicelsius */
    val->val1 = temp_mc / 1000;
    val->val2 = (temp_mc % 1000) * 1000;

    return 0;
}

static const struct sensor_driver_api temp_sensor_api = {
    .sample_fetch = temp_sensor_sample_fetch,
    .channel_get = temp_sensor_channel_get,
};

static int temp_sensor_init(const struct device *dev)
{
    const struct temp_sensor_config *cfg = dev->config;

    if (!i2c_is_ready_dt(&cfg->i2c)) {
        return -ENODEV;
    }

    /* Configure resolution register */
    uint8_t config = cfg->resolution << 5;
    return i2c_write_dt(&cfg->i2c, &config, 1);
}

#define TEMP_SENSOR_DEFINE(inst)                                    \
    static struct temp_sensor_data temp_sensor_data_##inst;         \
    static const struct temp_sensor_config temp_sensor_cfg_##inst = { \
        .i2c = I2C_DT_SPEC_INST_GET(inst),                          \
        .resolution = DT_INST_PROP(inst, resolution),               \
    };                                                              \
    DEVICE_DT_INST_DEFINE(inst,                                     \
                          temp_sensor_init,                         \
                          NULL,                                     \
                          &temp_sensor_data_##inst,                 \
                          &temp_sensor_cfg_##inst,                  \
                          POST_KERNEL,                              \
                          CONFIG_ACME_TEMP_SENSOR_INIT_PRIORITY,    \
                          &temp_sensor_api);

DT_INST_FOREACH_STATUS_OKAY(TEMP_SENSOR_DEFINE)
```

### CMakeLists.txt (driver)

```cmake
zephyr_library_sources_ifdef(CONFIG_ACME_TEMP_SENSOR temp_sensor.c)
```

### Overlay

```dts
&i2c0 {
    temp_sensor: temp-sensor@48 {
        compatible = "acme,temp-sensor";
        reg = <0x48>;
        resolution = <12>;
    };
};
```

### prj.conf

```ini
CONFIG_I2C=y
CONFIG_SENSOR=y
CONFIG_ACME_TEMP_SENSOR=y
```

### Application

```c
#include <zephyr/device.h>
#include <zephyr/drivers/sensor.h>

const struct device *temp = DEVICE_DT_GET(DT_NODELABEL(temp_sensor));

int main(void)
{
    struct sensor_value val;

    if (!device_is_ready(temp)) {
        return -1;
    }

    while (1) {
        sensor_sample_fetch(temp);
        sensor_channel_get(temp, SENSOR_CHAN_AMBIENT_TEMP, &val);
        printk("Temp: %d.%06d C\n", val.val1, val.val2);
        k_sleep(K_SECONDS(1));
    }
}
```
