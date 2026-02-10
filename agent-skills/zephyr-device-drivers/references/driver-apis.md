# Using Existing Driver APIs

## Table of Contents

1. [Getting Device Handles](#getting-device-handles)
2. [GPIO API](#gpio-api)
3. [I2C API](#i2c-api)
4. [SPI API](#spi-api)
5. [UART API](#uart-api)
6. [ADC API](#adc-api)
7. [PWM API](#pwm-api)
8. [Sensor API](#sensor-api)

---

## Getting Device Handles

### From Devicetree Node Label

```c
#include <zephyr/device.h>

/* Most common pattern */
const struct device *dev = DEVICE_DT_GET(DT_NODELABEL(gpio0));

/* ALWAYS check readiness before use */
if (!device_is_ready(dev)) {
    printk("Device not ready\n");
    return -ENODEV;
}
```

### Other Methods

```c
/* From alias (defined in DT) */
const struct device *led = DEVICE_DT_GET(DT_ALIAS(led0));

/* From chosen node */
const struct device *console = DEVICE_DT_GET(DT_CHOSEN(zephyr_console));

/* First device with compatible */
const struct device *sensor = DEVICE_DT_GET_ANY(bosch_bme280);

/* From devicetree path */
const struct device *spi = DEVICE_DT_GET(DT_PATH(soc, spi_40003000));
```

---

## GPIO API

**Header**: `<zephyr/drivers/gpio.h>`
**Kconfig**: `CONFIG_GPIO=y`

### Using gpio_dt_spec (Recommended)

```c
#include <zephyr/drivers/gpio.h>

/* Define from devicetree */
static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(DT_ALIAS(led0), gpios);
static const struct gpio_dt_spec button = GPIO_DT_SPEC_GET(DT_ALIAS(sw0), gpios);

int main(void)
{
    int ret;

    /* Check device ready */
    if (!gpio_is_ready_dt(&led)) {
        return -ENODEV;
    }

    /* Configure as output */
    ret = gpio_pin_configure_dt(&led, GPIO_OUTPUT_ACTIVE);
    if (ret < 0) {
        return ret;
    }

    /* Set pin high */
    gpio_pin_set_dt(&led, 1);

    /* Toggle pin */
    gpio_pin_toggle_dt(&led);

    /* Configure as input with interrupt */
    gpio_pin_configure_dt(&button, GPIO_INPUT);
    gpio_pin_interrupt_configure_dt(&button, GPIO_INT_EDGE_TO_ACTIVE);

    return 0;
}
```

### GPIO Interrupt Callback

```c
static struct gpio_callback button_cb_data;

void button_pressed(const struct device *dev, struct gpio_callback *cb,
                    uint32_t pins)
{
    printk("Button pressed at %" PRIu32 "\n", pins);
}

int setup_button_interrupt(void)
{
    gpio_pin_configure_dt(&button, GPIO_INPUT);
    gpio_pin_interrupt_configure_dt(&button, GPIO_INT_EDGE_TO_ACTIVE);

    gpio_init_callback(&button_cb_data, button_pressed, BIT(button.pin));
    gpio_add_callback(button.port, &button_cb_data);

    return 0;
}
```

### GPIO Flags

| Flag | Description |
|------|-------------|
| `GPIO_OUTPUT` | Configure as output |
| `GPIO_INPUT` | Configure as input |
| `GPIO_OUTPUT_ACTIVE` | Output, initially active |
| `GPIO_OUTPUT_INACTIVE` | Output, initially inactive |
| `GPIO_PULL_UP` | Enable pull-up |
| `GPIO_PULL_DOWN` | Enable pull-down |
| `GPIO_ACTIVE_LOW` | Active low polarity |
| `GPIO_INT_EDGE_RISING` | Interrupt on rising edge |
| `GPIO_INT_EDGE_FALLING` | Interrupt on falling edge |
| `GPIO_INT_EDGE_BOTH` | Interrupt on both edges |

---

## I2C API

**Header**: `<zephyr/drivers/i2c.h>`
**Kconfig**: `CONFIG_I2C=y`

### Using i2c_dt_spec (Recommended)

```c
#include <zephyr/drivers/i2c.h>

/* From devicetree node with reg property */
static const struct i2c_dt_spec dev_i2c = I2C_DT_SPEC_GET(DT_NODELABEL(my_sensor));

int main(void)
{
    uint8_t reg_addr = 0x00;
    uint8_t data[4];

    if (!i2c_is_ready_dt(&dev_i2c)) {
        return -ENODEV;
    }

    /* Write single byte */
    uint8_t val = 0x42;
    i2c_write_dt(&dev_i2c, &val, 1);

    /* Read into buffer */
    i2c_read_dt(&dev_i2c, data, sizeof(data));

    /* Write register then read (common pattern) */
    i2c_write_read_dt(&dev_i2c, &reg_addr, 1, data, sizeof(data));

    return 0;
}
```

### Register Access Pattern

```c
/* Read register */
static int read_reg(const struct i2c_dt_spec *i2c, uint8_t reg, uint8_t *val)
{
    return i2c_write_read_dt(i2c, &reg, 1, val, 1);
}

/* Write register */
static int write_reg(const struct i2c_dt_spec *i2c, uint8_t reg, uint8_t val)
{
    uint8_t buf[2] = {reg, val};
    return i2c_write_dt(i2c, buf, sizeof(buf));
}

/* Read multiple registers */
static int read_regs(const struct i2c_dt_spec *i2c, uint8_t start_reg,
                     uint8_t *buf, size_t len)
{
    return i2c_write_read_dt(i2c, &start_reg, 1, buf, len);
}
```

### Burst/Multi-Message Transfer

```c
struct i2c_msg msgs[2];
uint8_t reg = 0x10;
uint8_t data[6];

/* First message: write register address */
msgs[0].buf = &reg;
msgs[0].len = 1;
msgs[0].flags = I2C_MSG_WRITE;

/* Second message: read data */
msgs[1].buf = data;
msgs[1].len = sizeof(data);
msgs[1].flags = I2C_MSG_READ | I2C_MSG_STOP;

i2c_transfer_dt(&dev_i2c, msgs, 2);
```

---

## SPI API

**Header**: `<zephyr/drivers/spi.h>`
**Kconfig**: `CONFIG_SPI=y`

### Using spi_dt_spec (Recommended)

```c
#include <zephyr/drivers/spi.h>

/* From devicetree - includes bus, CS GPIO, and config */
static const struct spi_dt_spec spi_dev = SPI_DT_SPEC_GET(
    DT_NODELABEL(my_spi_device),
    SPI_WORD_SET(8) | SPI_TRANSFER_MSB,
    0  /* delay */
);

int main(void)
{
    uint8_t tx_buf[4] = {0x01, 0x02, 0x03, 0x04};
    uint8_t rx_buf[4];

    if (!spi_is_ready_dt(&spi_dev)) {
        return -ENODEV;
    }

    /* Set up buffers */
    struct spi_buf tx = {.buf = tx_buf, .len = sizeof(tx_buf)};
    struct spi_buf rx = {.buf = rx_buf, .len = sizeof(rx_buf)};
    struct spi_buf_set tx_set = {.buffers = &tx, .count = 1};
    struct spi_buf_set rx_set = {.buffers = &rx, .count = 1};

    /* Full duplex transfer */
    spi_transceive_dt(&spi_dev, &tx_set, &rx_set);

    /* Write only */
    spi_write_dt(&spi_dev, &tx_set);

    /* Read only */
    spi_read_dt(&spi_dev, &rx_set);

    return 0;
}
```

### Register Access Over SPI

```c
/* Read register (typical: send reg addr with read bit, then read) */
static int spi_read_reg(const struct spi_dt_spec *spi, uint8_t reg,
                        uint8_t *val)
{
    uint8_t tx = reg | 0x80;  /* Set read bit */
    uint8_t rx[2];

    struct spi_buf tx_buf = {.buf = &tx, .len = 1};
    struct spi_buf rx_buf = {.buf = rx, .len = 2};
    struct spi_buf_set tx_set = {.buffers = &tx_buf, .count = 1};
    struct spi_buf_set rx_set = {.buffers = &rx_buf, .count = 1};

    int ret = spi_transceive_dt(spi, &tx_set, &rx_set);
    *val = rx[1];
    return ret;
}

/* Write register */
static int spi_write_reg(const struct spi_dt_spec *spi, uint8_t reg,
                         uint8_t val)
{
    uint8_t tx[2] = {reg & 0x7F, val};  /* Clear read bit */
    struct spi_buf buf = {.buf = tx, .len = 2};
    struct spi_buf_set buf_set = {.buffers = &buf, .count = 1};

    return spi_write_dt(spi, &buf_set);
}
```

### SPI Configuration Flags

| Flag | Description |
|------|-------------|
| `SPI_WORD_SET(n)` | Word size in bits (8, 16, etc.) |
| `SPI_TRANSFER_MSB` | MSB first (most common) |
| `SPI_TRANSFER_LSB` | LSB first |
| `SPI_MODE_CPOL` | Clock polarity high |
| `SPI_MODE_CPHA` | Clock phase: sample on trailing edge |
| `SPI_MODE_GET(n)` | SPI mode 0-3 |

---

## UART API

**Header**: `<zephyr/drivers/uart.h>`
**Kconfig**: `CONFIG_SERIAL=y`

### Polling API

```c
#include <zephyr/drivers/uart.h>

const struct device *uart = DEVICE_DT_GET(DT_NODELABEL(uart0));

/* Transmit */
void uart_send(const uint8_t *data, size_t len)
{
    for (size_t i = 0; i < len; i++) {
        uart_poll_out(uart, data[i]);
    }
}

/* Receive (blocking) */
int uart_receive_byte(uint8_t *c)
{
    return uart_poll_in(uart, c);  /* Returns 0 on success, -1 if no data */
}
```

### Interrupt-Driven API

```c
#include <zephyr/drivers/uart.h>

const struct device *uart = DEVICE_DT_GET(DT_NODELABEL(uart0));

static uint8_t rx_buf[64];
static volatile size_t rx_count = 0;

void uart_isr(const struct device *dev, void *user_data)
{
    if (!uart_irq_update(dev)) {
        return;
    }

    if (uart_irq_rx_ready(dev)) {
        uint8_t c;
        while (uart_fifo_read(dev, &c, 1) > 0) {
            if (rx_count < sizeof(rx_buf)) {
                rx_buf[rx_count++] = c;
            }
        }
    }
}

int setup_uart_irq(void)
{
    if (!device_is_ready(uart)) {
        return -ENODEV;
    }

    uart_irq_callback_set(uart, uart_isr);
    uart_irq_rx_enable(uart);

    return 0;
}
```

### Async API (DMA-based)

Enable with `CONFIG_UART_ASYNC_API=y`:

```c
static uint8_t rx_buf[256];

void uart_async_callback(const struct device *dev,
                         struct uart_event *evt,
                         void *user_data)
{
    switch (evt->type) {
    case UART_RX_RDY:
        /* Data received: evt->data.rx.buf, evt->data.rx.len */
        break;
    case UART_TX_DONE:
        /* Transmission complete */
        break;
    case UART_RX_DISABLED:
        /* Re-enable RX */
        uart_rx_enable(dev, rx_buf, sizeof(rx_buf), SYS_FOREVER_US);
        break;
    default:
        break;
    }
}

int setup_uart_async(void)
{
    uart_callback_set(uart, uart_async_callback, NULL);
    uart_rx_enable(uart, rx_buf, sizeof(rx_buf), SYS_FOREVER_US);
    return 0;
}
```

---

## ADC API

**Header**: `<zephyr/drivers/adc.h>`
**Kconfig**: `CONFIG_ADC=y`

### Basic ADC Reading

```c
#include <zephyr/drivers/adc.h>

/* Define channel from devicetree */
static const struct adc_dt_spec adc_channel = ADC_DT_SPEC_GET(DT_PATH(zephyr_user));

int main(void)
{
    int16_t buf;
    int ret;

    if (!adc_is_ready_dt(&adc_channel)) {
        return -ENODEV;
    }

    /* Configure channel */
    ret = adc_channel_setup_dt(&adc_channel);
    if (ret < 0) {
        return ret;
    }

    /* Create sequence */
    struct adc_sequence sequence = {
        .buffer = &buf,
        .buffer_size = sizeof(buf),
    };
    adc_sequence_init_dt(&adc_channel, &sequence);

    /* Read ADC */
    ret = adc_read_dt(&adc_channel, &sequence);
    if (ret < 0) {
        return ret;
    }

    /* Convert to millivolts */
    int32_t mv = buf;
    adc_raw_to_millivolts_dt(&adc_channel, &mv);
    printk("ADC: %d mV\n", mv);

    return 0;
}
```

### Devicetree for ADC

```dts
/ {
    zephyr,user {
        io-channels = <&adc 0>;  /* ADC channel 0 */
    };
};

&adc {
    #address-cells = <1>;
    #size-cells = <0>;
    status = "okay";

    channel@0 {
        reg = <0>;
        zephyr,gain = "ADC_GAIN_1_6";
        zephyr,reference = "ADC_REF_INTERNAL";
        zephyr,acquisition-time = <ADC_ACQ_TIME_DEFAULT>;
        zephyr,resolution = <12>;
    };
};
```

---

## PWM API

**Header**: `<zephyr/drivers/pwm.h>`
**Kconfig**: `CONFIG_PWM=y`

### Basic PWM Control

```c
#include <zephyr/drivers/pwm.h>

static const struct pwm_dt_spec pwm_led = PWM_DT_SPEC_GET(DT_ALIAS(pwm_led0));

int main(void)
{
    if (!pwm_is_ready_dt(&pwm_led)) {
        return -ENODEV;
    }

    /* Set 50% duty cycle at 1kHz */
    uint32_t period_ns = 1000000U;  /* 1ms = 1kHz */
    uint32_t pulse_ns = period_ns / 2;

    pwm_set_pulse_dt(&pwm_led, pulse_ns);

    /* Or set with explicit period */
    pwm_set_dt(&pwm_led, period_ns, pulse_ns);

    return 0;
}
```

### Devicetree for PWM

```dts
/ {
    aliases {
        pwm-led0 = &pwm_led0;
    };

    pwmleds {
        compatible = "pwm-leds";
        pwm_led0: pwm_led_0 {
            pwms = <&pwm0 0 PWM_MSEC(20) PWM_POLARITY_NORMAL>;
        };
    };
};
```

---

## Sensor API

**Header**: `<zephyr/drivers/sensor.h>`
**Kconfig**: `CONFIG_SENSOR=y`

### Reading Sensor Data

```c
#include <zephyr/drivers/sensor.h>

const struct device *sensor = DEVICE_DT_GET_ANY(bosch_bme280);

int main(void)
{
    struct sensor_value temp, press, humidity;

    if (!device_is_ready(sensor)) {
        return -ENODEV;
    }

    while (1) {
        /* Fetch all channels */
        sensor_sample_fetch(sensor);

        /* Get specific channels */
        sensor_channel_get(sensor, SENSOR_CHAN_AMBIENT_TEMP, &temp);
        sensor_channel_get(sensor, SENSOR_CHAN_PRESS, &press);
        sensor_channel_get(sensor, SENSOR_CHAN_HUMIDITY, &humidity);

        /* sensor_value: val1 = integer part, val2 = fractional (micro) */
        printk("Temp: %d.%06d C\n", temp.val1, temp.val2);
        printk("Press: %d.%06d kPa\n", press.val1, press.val2);
        printk("Humidity: %d.%06d %%\n", humidity.val1, humidity.val2);

        k_sleep(K_SECONDS(1));
    }
}
```

### Sensor Triggers

```c
static void trigger_handler(const struct device *dev,
                            const struct sensor_trigger *trigger)
{
    struct sensor_value val;
    sensor_sample_fetch(dev);
    sensor_channel_get(dev, SENSOR_CHAN_ACCEL_XYZ, &val);
    printk("Motion detected!\n");
}

int setup_trigger(void)
{
    struct sensor_trigger trig = {
        .type = SENSOR_TRIG_MOTION,
        .chan = SENSOR_CHAN_ACCEL_XYZ,
    };

    return sensor_trigger_set(sensor, &trig, trigger_handler);
}
```

### Common Sensor Channels

| Channel | Description |
|---------|-------------|
| `SENSOR_CHAN_AMBIENT_TEMP` | Temperature (°C) |
| `SENSOR_CHAN_PRESS` | Pressure (kPa) |
| `SENSOR_CHAN_HUMIDITY` | Relative humidity (%) |
| `SENSOR_CHAN_ACCEL_X/Y/Z` | Acceleration (m/s²) |
| `SENSOR_CHAN_GYRO_X/Y/Z` | Angular velocity (rad/s) |
| `SENSOR_CHAN_LIGHT` | Light intensity (lux) |
| `SENSOR_CHAN_VOLTAGE` | Voltage (V) |
| `SENSOR_CHAN_CURRENT` | Current (A) |
