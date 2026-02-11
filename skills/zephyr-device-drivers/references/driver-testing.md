# Testing Device Drivers

## Table of Contents

1. [Testing Overview](#testing-overview)
2. [Ztest for Drivers](#ztest-for-drivers)
3. [Emulators](#emulators)
4. [Fake Devices](#fake-devices)
5. [Test Fixtures](#test-fixtures)
6. [Running Tests](#running-tests)

---

## Testing Overview

### Testing Approaches

| Approach | Use Case | Platform |
|----------|----------|----------|
| Unit tests with emulators | Comprehensive driver testing | native_sim |
| Integration tests | Test with real hardware | Target board |
| Fake/stub devices | Test application code | Any |
| Twister | Automated test execution | CI/CD |

### Project Structure for Tests

```
my_driver/
├── CMakeLists.txt
├── Kconfig
├── my_driver.c
└── tests/
    ├── CMakeLists.txt
    ├── prj.conf
    ├── testcase.yaml
    ├── boards/
    │   └── native_sim.overlay
    └── src/
        └── main.c
```

---

## Ztest for Drivers

### Basic Driver Test

```c
#include <zephyr/ztest.h>
#include <zephyr/device.h>
#include <zephyr/drivers/gpio.h>

static const struct device *gpio_dev = DEVICE_DT_GET(DT_NODELABEL(gpio0));

ZTEST(driver_tests, test_device_ready)
{
    zassert_true(device_is_ready(gpio_dev), "GPIO device not ready");
}

ZTEST(driver_tests, test_gpio_output)
{
    int ret;

    ret = gpio_pin_configure(gpio_dev, 0, GPIO_OUTPUT);
    zassert_ok(ret, "Failed to configure GPIO");

    ret = gpio_pin_set(gpio_dev, 0, 1);
    zassert_ok(ret, "Failed to set GPIO high");

    ret = gpio_pin_set(gpio_dev, 0, 0);
    zassert_ok(ret, "Failed to set GPIO low");
}

ZTEST_SUITE(driver_tests, NULL, NULL, NULL, NULL, NULL);
```

### Testing Sensor Drivers

```c
#include <zephyr/ztest.h>
#include <zephyr/drivers/sensor.h>

static const struct device *sensor = DEVICE_DT_GET(DT_NODELABEL(temp_sensor));

ZTEST(sensor_tests, test_sensor_ready)
{
    zassert_true(device_is_ready(sensor), "Sensor not ready");
}

ZTEST(sensor_tests, test_sample_fetch)
{
    int ret = sensor_sample_fetch(sensor);
    zassert_ok(ret, "Failed to fetch sample");
}

ZTEST(sensor_tests, test_channel_get)
{
    struct sensor_value val;
    int ret;

    ret = sensor_sample_fetch(sensor);
    zassert_ok(ret);

    ret = sensor_channel_get(sensor, SENSOR_CHAN_AMBIENT_TEMP, &val);
    zassert_ok(ret, "Failed to get channel");

    /* Check reasonable range (-40 to +85°C for typical sensors) */
    zassert_between_inclusive(val.val1, -40, 85,
                              "Temperature out of range: %d", val.val1);
}

ZTEST(sensor_tests, test_unsupported_channel)
{
    struct sensor_value val;
    int ret;

    ret = sensor_sample_fetch(sensor);
    zassert_ok(ret);

    ret = sensor_channel_get(sensor, SENSOR_CHAN_GYRO_X, &val);
    zassert_equal(ret, -ENOTSUP, "Should not support gyro channel");
}

ZTEST_SUITE(sensor_tests, NULL, NULL, NULL, NULL, NULL);
```

### Testing I2C Drivers

```c
#include <zephyr/ztest.h>
#include <zephyr/drivers/i2c.h>

static const struct i2c_dt_spec dev_i2c = I2C_DT_SPEC_GET(DT_NODELABEL(my_device));

ZTEST(i2c_tests, test_bus_ready)
{
    zassert_true(i2c_is_ready_dt(&dev_i2c), "I2C bus not ready");
}

ZTEST(i2c_tests, test_read_chip_id)
{
    uint8_t chip_id;
    uint8_t reg = 0x00;  /* Chip ID register */
    int ret;

    ret = i2c_write_read_dt(&dev_i2c, &reg, 1, &chip_id, 1);
    zassert_ok(ret, "Failed to read chip ID");
    zassert_equal(chip_id, 0x5A, "Unexpected chip ID: 0x%02x", chip_id);
}

ZTEST_SUITE(i2c_tests, NULL, NULL, NULL, NULL, NULL);
```

---

## Emulators

Enable hardware-free testing on native_sim.

### Kconfig for Emulation

```kconfig
# prj.conf for tests
CONFIG_EMUL=y
CONFIG_I2C_EMUL=y
CONFIG_SPI_EMUL=y
CONFIG_GPIO_EMUL=y
```

### Devicetree for Emulation

```dts
/* boards/native_sim.overlay */
/ {
    aliases {
        my-sensor = &test_sensor;
    };
};

&i2c0 {
    status = "okay";

    test_sensor: sensor@48 {
        compatible = "vendor,my-sensor";
        reg = <0x48>;
    };
};
```

### Using Emulator Backend in Tests

```c
#include <zephyr/ztest.h>
#include <zephyr/drivers/sensor.h>
#include <zephyr/drivers/emul.h>

/* Get device and emulator */
static const struct device *sensor = DEVICE_DT_GET(DT_NODELABEL(test_sensor));
static const struct emul *emul = EMUL_DT_GET(DT_NODELABEL(test_sensor));

/* Emulator backend API (defined in emulator) */
struct my_sensor_emul_backend {
    void (*set_temperature)(const struct emul *target, int32_t temp_milli_c);
    void (*set_error)(const struct emul *target, bool inject_error);
};

ZTEST(emul_tests, test_read_emulated_value)
{
    const struct my_sensor_emul_backend *backend = emul->backend_api;
    struct sensor_value val;

    /* Set emulator to return 25.5°C */
    backend->set_temperature(emul, 25500);

    /* Read through driver */
    zassert_ok(sensor_sample_fetch(sensor));
    zassert_ok(sensor_channel_get(sensor, SENSOR_CHAN_AMBIENT_TEMP, &val));

    /* Verify driver correctly interprets emulated data */
    zassert_equal(val.val1, 25, "Expected 25, got %d", val.val1);
    zassert_within(val.val2, 500000, 1000, "Fractional mismatch");
}

ZTEST(emul_tests, test_error_handling)
{
    const struct my_sensor_emul_backend *backend = emul->backend_api;

    /* Inject error */
    backend->set_error(emul, true);

    /* Verify driver handles error correctly */
    int ret = sensor_sample_fetch(sensor);
    zassert_not_ok(ret, "Should fail with error injected");

    /* Clear error */
    backend->set_error(emul, false);
    ret = sensor_sample_fetch(sensor);
    zassert_ok(ret, "Should succeed after clearing error");
}

ZTEST_SUITE(emul_tests, NULL, NULL, NULL, NULL, NULL);
```

### GPIO Emulator

```c
#include <zephyr/drivers/gpio/gpio_emul.h>

static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(DT_ALIAS(led0), gpios);

ZTEST(gpio_emul_tests, test_gpio_output)
{
    gpio_flags_t flags;
    int val;

    /* Configure as output */
    gpio_pin_configure_dt(&led, GPIO_OUTPUT_INACTIVE);

    /* Get emulated pin state */
    gpio_emul_output_get(led.port, led.pin, &val);
    zassert_equal(val, 0, "Should start inactive");

    /* Set high */
    gpio_pin_set_dt(&led, 1);
    gpio_emul_output_get(led.port, led.pin, &val);
    zassert_equal(val, 1, "Should be high");
}

ZTEST(gpio_emul_tests, test_gpio_input)
{
    static const struct gpio_dt_spec button =
        GPIO_DT_SPEC_GET(DT_ALIAS(sw0), gpios);
    int val;

    gpio_pin_configure_dt(&button, GPIO_INPUT);

    /* Inject input value */
    gpio_emul_input_set(button.port, button.pin, 1);

    /* Read through driver */
    val = gpio_pin_get_dt(&button);
    zassert_equal(val, 1, "Should read injected value");
}

ZTEST_SUITE(gpio_emul_tests, NULL, NULL, NULL, NULL, NULL);
```

---

## Fake Devices

For testing application code without full driver emulation.

### Creating a Fake Driver

```c
/* fake_sensor.c */
#include <zephyr/device.h>
#include <zephyr/drivers/sensor.h>

static int32_t fake_temp_value = 25000;  /* 25.0°C in millicelsius */

void fake_sensor_set_temp(int32_t temp_mc)
{
    fake_temp_value = temp_mc;
}

static int fake_sample_fetch(const struct device *dev, enum sensor_channel chan)
{
    return 0;
}

static int fake_channel_get(const struct device *dev,
                            enum sensor_channel chan,
                            struct sensor_value *val)
{
    if (chan != SENSOR_CHAN_AMBIENT_TEMP) {
        return -ENOTSUP;
    }

    val->val1 = fake_temp_value / 1000;
    val->val2 = (fake_temp_value % 1000) * 1000;
    return 0;
}

static const struct sensor_driver_api fake_sensor_api = {
    .sample_fetch = fake_sample_fetch,
    .channel_get = fake_channel_get,
};

static int fake_sensor_init(const struct device *dev)
{
    return 0;
}

DEVICE_DEFINE(fake_sensor, "FAKE_SENSOR", fake_sensor_init, NULL,
              NULL, NULL, POST_KERNEL, CONFIG_SENSOR_INIT_PRIORITY,
              &fake_sensor_api);
```

### Using in Tests

```c
#include <zephyr/ztest.h>
#include <zephyr/device.h>
#include <zephyr/drivers/sensor.h>

/* Declare fake setter (from fake_sensor.c) */
void fake_sensor_set_temp(int32_t temp_mc);

ZTEST(app_tests, test_temp_alarm)
{
    const struct device *sensor = device_get_binding("FAKE_SENSOR");
    bool alarm_triggered = false;

    /* Test normal temperature */
    fake_sensor_set_temp(25000);  /* 25°C */
    alarm_triggered = check_temp_alarm(sensor);
    zassert_false(alarm_triggered, "No alarm at 25°C");

    /* Test high temperature */
    fake_sensor_set_temp(85000);  /* 85°C */
    alarm_triggered = check_temp_alarm(sensor);
    zassert_true(alarm_triggered, "Alarm should trigger at 85°C");
}

ZTEST_SUITE(app_tests, NULL, NULL, NULL, NULL, NULL);
```

---

## Test Fixtures

Setup and teardown for tests.

### Suite-Level Fixtures

```c
static const struct device *dev;

static void *suite_setup(void)
{
    dev = DEVICE_DT_GET(DT_NODELABEL(my_device));
    zassert_true(device_is_ready(dev), "Device not ready");

    /* Return state that can be passed to tests */
    return (void *)dev;
}

static void suite_teardown(void *fixture)
{
    /* Cleanup after all tests */
}

ZTEST_SUITE(driver_tests, NULL, suite_setup, NULL, NULL, suite_teardown);
```

### Per-Test Fixtures

```c
struct test_fixture {
    const struct device *dev;
    uint8_t original_config;
};

static void before_each(void *fixture)
{
    struct test_fixture *f = fixture;

    /* Reset device to known state before each test */
    f->dev = DEVICE_DT_GET(DT_NODELABEL(my_device));
    /* Save original config */
    /* read_config(f->dev, &f->original_config); */
}

static void after_each(void *fixture)
{
    struct test_fixture *f = fixture;

    /* Restore original config after each test */
    /* write_config(f->dev, f->original_config); */
}

static void *suite_setup(void)
{
    static struct test_fixture fixture;
    return &fixture;
}

ZTEST_SUITE(driver_tests, NULL, suite_setup, before_each, after_each, NULL);

ZTEST_F(driver_tests, test_with_fixture)
{
    /* Access fixture via 'fixture' pointer */
    zassert_true(device_is_ready(fixture->dev));
}
```

---

## Running Tests

### testcase.yaml

```yaml
tests:
  drivers.my_driver:
    tags: driver sensor
    platform_allow:
      - native_sim
      - nrf52840dk_nrf52840
    integration_platforms:
      - native_sim
    extra_configs:
      - CONFIG_MY_DRIVER=y
      - CONFIG_EMUL=y
```

### CMakeLists.txt for Tests

```cmake
cmake_minimum_required(VERSION 3.20.0)
find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(my_driver_test)

target_sources(app PRIVATE src/main.c)

# Include driver source if not built as module
# target_sources(app PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../my_driver.c)
```

### prj.conf for Tests

```ini
CONFIG_ZTEST=y
CONFIG_ZTEST_NEW_API=y
CONFIG_LOG=y

# For native_sim
CONFIG_EMUL=y
CONFIG_I2C_EMUL=y
CONFIG_GPIO_EMUL=y

# Driver under test
CONFIG_MY_DRIVER=y
CONFIG_MY_DRIVER_LOG_LEVEL=4
```

### Running with Twister

```bash
# Run all driver tests
west twister -T tests/drivers/

# Run specific test
west twister -T tests/drivers/my_driver/

# Run on native_sim only
west twister -T tests/drivers/ -p native_sim

# Verbose output
west twister -T tests/drivers/ -v

# Generate coverage report
west twister -T tests/drivers/ --coverage
```

### Running Locally

```bash
# Build for native_sim
west build -b native_sim tests/drivers/my_driver/

# Run
./build/zephyr/zephyr.exe

# Or with west
west build -b native_sim tests/drivers/my_driver/ -t run
```

### Test Output

```
*** Booting Zephyr OS build v3.x.x ***
Running TESTSUITE driver_tests
================================================================
START - test_device_ready
 PASS - test_device_ready in 0.001 seconds
================================================================
START - test_sample_fetch
 PASS - test_sample_fetch in 0.003 seconds
================================================================
START - test_channel_get
 PASS - test_channel_get in 0.002 seconds
================================================================
TESTSUITE driver_tests succeeded
------ TESTSUITE SUMMARY ------
SUITE PASS - 100.00% [driver_tests]: pass = 3, fail = 0, skip = 0
```
