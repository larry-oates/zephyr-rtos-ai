# Complete Driver Examples

## Table of Contents

1. [GPIO LED Driver](#gpio-led-driver)
2. [I2C Temperature Sensor](#i2c-temperature-sensor)
3. [SPI Flash Driver](#spi-flash-driver)
4. [UART GPS Module](#uart-gps-module)
5. [Complete Sensor with Triggers](#complete-sensor-with-triggers)

---

## GPIO LED Driver

Complete example of a simple GPIO-controlled LED driver.

### Files

```
led_driver/
├── CMakeLists.txt
├── Kconfig
├── led_driver.c
└── dts/bindings/
    └── custom,led.yaml
```

### Binding: `custom,led.yaml`

```yaml
description: Custom LED driver

compatible: "custom,led"

include: base.yaml

properties:
  led-gpios:
    type: phandle-array
    required: true
    description: GPIO connected to LED

  default-brightness:
    type: int
    default: 100
    description: Default brightness percentage (0-100)
```

### Kconfig

```kconfig
config CUSTOM_LED
    bool "Custom LED driver"
    default y
    depends on GPIO
    help
      Enable custom LED driver.

config CUSTOM_LED_INIT_PRIORITY
    int "Initialization priority"
    default 60
    depends on CUSTOM_LED
```

### Driver: `led_driver.c`

```c
#define DT_DRV_COMPAT custom_led

#include <zephyr/device.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(custom_led, CONFIG_LED_LOG_LEVEL);

struct led_config {
    struct gpio_dt_spec gpio;
    uint8_t default_brightness;
};

struct led_data {
    bool is_on;
    uint8_t brightness;
};

/* LED API */
static int led_on(const struct device *dev)
{
    const struct led_config *cfg = dev->config;
    struct led_data *data = dev->data;

    gpio_pin_set_dt(&cfg->gpio, 1);
    data->is_on = true;
    return 0;
}

static int led_off(const struct device *dev)
{
    const struct led_config *cfg = dev->config;
    struct led_data *data = dev->data;

    gpio_pin_set_dt(&cfg->gpio, 0);
    data->is_on = false;
    return 0;
}

static int led_toggle(const struct device *dev)
{
    struct led_data *data = dev->data;

    if (data->is_on) {
        return led_off(dev);
    } else {
        return led_on(dev);
    }
}

static int led_set_brightness(const struct device *dev, uint8_t brightness)
{
    const struct led_config *cfg = dev->config;
    struct led_data *data = dev->data;

    /* Simple on/off for GPIO LED */
    data->brightness = brightness;
    if (brightness > 0) {
        gpio_pin_set_dt(&cfg->gpio, 1);
        data->is_on = true;
    } else {
        gpio_pin_set_dt(&cfg->gpio, 0);
        data->is_on = false;
    }
    return 0;
}

/* Standard LED driver API */
static const struct led_driver_api led_api = {
    .on = led_on,
    .off = led_off,
    .set_brightness = led_set_brightness,
};

static int led_init(const struct device *dev)
{
    const struct led_config *cfg = dev->config;
    struct led_data *data = dev->data;

    if (!gpio_is_ready_dt(&cfg->gpio)) {
        LOG_ERR("GPIO device not ready");
        return -ENODEV;
    }

    int ret = gpio_pin_configure_dt(&cfg->gpio, GPIO_OUTPUT_INACTIVE);
    if (ret < 0) {
        LOG_ERR("Failed to configure GPIO: %d", ret);
        return ret;
    }

    data->is_on = false;
    data->brightness = cfg->default_brightness;

    LOG_INF("LED %s initialized", dev->name);
    return 0;
}

#define LED_DEFINE(inst)                                               \
    static struct led_data led_data_##inst;                            \
    static const struct led_config led_config_##inst = {               \
        .gpio = GPIO_DT_SPEC_INST_GET(inst, led_gpios),                \
        .default_brightness = DT_INST_PROP(inst, default_brightness),  \
    };                                                                 \
    DEVICE_DT_INST_DEFINE(inst, led_init, NULL,                        \
                          &led_data_##inst, &led_config_##inst,        \
                          POST_KERNEL, CONFIG_CUSTOM_LED_INIT_PRIORITY,\
                          &led_api);

DT_INST_FOREACH_STATUS_OKAY(LED_DEFINE)
```

### Overlay

```dts
/ {
    my_led: led_0 {
        compatible = "custom,led";
        led-gpios = <&gpio0 13 GPIO_ACTIVE_HIGH>;
        default-brightness = <100>;
    };
};
```

### Application Usage

```c
#include <zephyr/drivers/led.h>

const struct device *led = DEVICE_DT_GET(DT_NODELABEL(my_led));

int main(void)
{
    if (!device_is_ready(led)) {
        return -1;
    }

    while (1) {
        led_on(led, 0);
        k_sleep(K_MSEC(500));
        led_off(led, 0);
        k_sleep(K_MSEC(500));
    }
}
```

---

## I2C Temperature Sensor

Complete I2C temperature sensor driver with sensor API integration.

### Files

```
temp_sensor/
├── CMakeLists.txt
├── Kconfig
├── temp_sensor.c
└── dts/bindings/
    └── acme,tmp101.yaml
```

### Binding: `acme,tmp101.yaml`

```yaml
description: ACME TMP101 Temperature Sensor

compatible: "acme,tmp101"

include: [i2c-device.yaml]

properties:
  alert-gpios:
    type: phandle-array
    description: Alert/interrupt GPIO

  resolution:
    type: int
    default: 12
    enum: [9, 10, 11, 12]
    description: ADC resolution in bits
```

### Kconfig

```kconfig
config ACME_TMP101
    bool "ACME TMP101 temperature sensor"
    default y
    depends on I2C
    select SENSOR
    help
      Enable ACME TMP101 temperature sensor driver.

config ACME_TMP101_INIT_PRIORITY
    int "Init priority"
    default 90
    depends on ACME_TMP101
```

### Driver: `temp_sensor.c`

```c
#define DT_DRV_COMPAT acme_tmp101

#include <zephyr/device.h>
#include <zephyr/drivers/i2c.h>
#include <zephyr/drivers/sensor.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(tmp101, CONFIG_SENSOR_LOG_LEVEL);

/* Register addresses */
#define REG_TEMP        0x00
#define REG_CONFIG      0x01
#define REG_TLOW        0x02
#define REG_THIGH       0x03

/* Configuration bits */
#define CONFIG_OS       BIT(7)  /* One-shot */
#define CONFIG_RES_MASK (BIT(6) | BIT(5))
#define CONFIG_RES_SHIFT 5

struct tmp101_config {
    struct i2c_dt_spec i2c;
    struct gpio_dt_spec alert;
    uint8_t resolution;
};

struct tmp101_data {
    int16_t temp_raw;
};

/* Helper functions */
static int tmp101_read_reg(const struct i2c_dt_spec *i2c,
                           uint8_t reg, uint8_t *data, size_t len)
{
    return i2c_write_read_dt(i2c, &reg, 1, data, len);
}

static int tmp101_write_reg(const struct i2c_dt_spec *i2c,
                            uint8_t reg, uint8_t value)
{
    uint8_t buf[2] = {reg, value};
    return i2c_write_dt(i2c, buf, sizeof(buf));
}

/* Sensor API */
static int tmp101_sample_fetch(const struct device *dev,
                               enum sensor_channel chan)
{
    const struct tmp101_config *cfg = dev->config;
    struct tmp101_data *data = dev->data;
    uint8_t buf[2];
    int ret;

    if (chan != SENSOR_CHAN_ALL && chan != SENSOR_CHAN_AMBIENT_TEMP) {
        return -ENOTSUP;
    }

    ret = tmp101_read_reg(&cfg->i2c, REG_TEMP, buf, sizeof(buf));
    if (ret < 0) {
        LOG_ERR("Failed to read temperature: %d", ret);
        return ret;
    }

    /* Temperature is in 2's complement, MSB first */
    data->temp_raw = (buf[0] << 8) | buf[1];

    /* Right-justify based on resolution */
    data->temp_raw >>= (16 - cfg->resolution);

    return 0;
}

static int tmp101_channel_get(const struct device *dev,
                              enum sensor_channel chan,
                              struct sensor_value *val)
{
    const struct tmp101_config *cfg = dev->config;
    struct tmp101_data *data = dev->data;

    if (chan != SENSOR_CHAN_AMBIENT_TEMP) {
        return -ENOTSUP;
    }

    /* Calculate temperature based on resolution
     * 12-bit: 0.0625°C per LSB
     * 11-bit: 0.125°C per LSB
     * 10-bit: 0.25°C per LSB
     * 9-bit:  0.5°C per LSB
     */
    int32_t lsb_uc;  /* Micro-celsius per LSB */
    switch (cfg->resolution) {
    case 9:  lsb_uc = 500000; break;
    case 10: lsb_uc = 250000; break;
    case 11: lsb_uc = 125000; break;
    case 12:
    default: lsb_uc = 62500; break;
    }

    int64_t temp_uc = (int64_t)data->temp_raw * lsb_uc;
    val->val1 = temp_uc / 1000000;
    val->val2 = temp_uc % 1000000;

    return 0;
}

static const struct sensor_driver_api tmp101_api = {
    .sample_fetch = tmp101_sample_fetch,
    .channel_get = tmp101_channel_get,
};

static int tmp101_init(const struct device *dev)
{
    const struct tmp101_config *cfg = dev->config;
    uint8_t config;
    int ret;

    if (!i2c_is_ready_dt(&cfg->i2c)) {
        LOG_ERR("I2C bus not ready");
        return -ENODEV;
    }

    /* Read current config */
    ret = tmp101_read_reg(&cfg->i2c, REG_CONFIG, &config, 1);
    if (ret < 0) {
        LOG_ERR("Failed to read config: %d", ret);
        return ret;
    }

    /* Set resolution */
    config &= ~CONFIG_RES_MASK;
    config |= ((cfg->resolution - 9) << CONFIG_RES_SHIFT);

    ret = tmp101_write_reg(&cfg->i2c, REG_CONFIG, config);
    if (ret < 0) {
        LOG_ERR("Failed to write config: %d", ret);
        return ret;
    }

    LOG_INF("TMP101 %s initialized (resolution: %d-bit)",
            dev->name, cfg->resolution);

    return 0;
}

#define TMP101_DEFINE(inst)                                             \
    static struct tmp101_data tmp101_data_##inst;                       \
    static const struct tmp101_config tmp101_config_##inst = {          \
        .i2c = I2C_DT_SPEC_INST_GET(inst),                              \
        .alert = GPIO_DT_SPEC_INST_GET_OR(inst, alert_gpios, {0}),      \
        .resolution = DT_INST_PROP(inst, resolution),                   \
    };                                                                  \
    DEVICE_DT_INST_DEFINE(inst, tmp101_init, NULL,                      \
                          &tmp101_data_##inst,                          \
                          &tmp101_config_##inst,                        \
                          POST_KERNEL,                                  \
                          CONFIG_ACME_TMP101_INIT_PRIORITY,             \
                          &tmp101_api);

DT_INST_FOREACH_STATUS_OKAY(TMP101_DEFINE)
```

### Overlay

```dts
&i2c0 {
    status = "okay";

    tmp101: temperature@48 {
        compatible = "acme,tmp101";
        reg = <0x48>;
        resolution = <12>;
    };
};
```

### Application Usage

```c
#include <zephyr/drivers/sensor.h>

const struct device *temp = DEVICE_DT_GET(DT_NODELABEL(tmp101));

int main(void)
{
    struct sensor_value val;

    if (!device_is_ready(temp)) {
        return -1;
    }

    while (1) {
        sensor_sample_fetch(temp);
        sensor_channel_get(temp, SENSOR_CHAN_AMBIENT_TEMP, &val);
        printk("Temperature: %d.%06d C\n", val.val1, val.val2);
        k_sleep(K_SECONDS(1));
    }
}
```

---

## SPI Flash Driver

Complete SPI NOR flash driver example.

### Files

```
spi_flash/
├── CMakeLists.txt
├── Kconfig
├── spi_flash.c
└── dts/bindings/
    └── acme,spi-flash.yaml
```

### Binding: `acme,spi-flash.yaml`

```yaml
description: ACME SPI NOR Flash

compatible: "acme,spi-flash"

include: [spi-device.yaml]

properties:
  size:
    type: int
    required: true
    description: Flash size in bytes

  page-size:
    type: int
    default: 256
    description: Page size for programming

  sector-size:
    type: int
    default: 4096
    description: Sector size for erase

  jedec-id:
    type: uint8-array
    description: Expected JEDEC ID bytes

  wp-gpios:
    type: phandle-array
    description: Write protect GPIO

  hold-gpios:
    type: phandle-array
    description: Hold GPIO
```

### Driver: `spi_flash.c`

```c
#define DT_DRV_COMPAT acme_spi_flash

#include <zephyr/device.h>
#include <zephyr/drivers/spi.h>
#include <zephyr/drivers/flash.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(acme_flash, CONFIG_FLASH_LOG_LEVEL);

/* Flash commands */
#define CMD_READ_ID      0x9F
#define CMD_READ_STATUS  0x05
#define CMD_WRITE_ENABLE 0x06
#define CMD_READ         0x03
#define CMD_PAGE_PROGRAM 0x02
#define CMD_SECTOR_ERASE 0x20
#define CMD_CHIP_ERASE   0xC7

#define STATUS_WIP       BIT(0)  /* Write in progress */
#define STATUS_WEL       BIT(1)  /* Write enable latch */

struct flash_config {
    struct spi_dt_spec spi;
    struct gpio_dt_spec wp;
    uint32_t size;
    uint16_t page_size;
    uint16_t sector_size;
    uint8_t jedec_id[3];
};

struct flash_data {
    struct k_sem lock;
};

/* SPI transaction helpers */
static int flash_read_status(const struct spi_dt_spec *spi, uint8_t *status)
{
    uint8_t cmd = CMD_READ_STATUS;
    uint8_t rx[2];

    struct spi_buf tx_buf = {.buf = &cmd, .len = 1};
    struct spi_buf rx_buf = {.buf = rx, .len = 2};
    struct spi_buf_set tx = {.buffers = &tx_buf, .count = 1};
    struct spi_buf_set rx_set = {.buffers = &rx_buf, .count = 1};

    int ret = spi_transceive_dt(spi, &tx, &rx_set);
    if (ret == 0) {
        *status = rx[1];
    }
    return ret;
}

static int flash_wait_ready(const struct spi_dt_spec *spi, k_timeout_t timeout)
{
    int64_t end = k_uptime_get() + k_ticks_to_ms_floor64(timeout.ticks);
    uint8_t status;

    do {
        int ret = flash_read_status(spi, &status);
        if (ret < 0) {
            return ret;
        }
        if (!(status & STATUS_WIP)) {
            return 0;
        }
        k_sleep(K_MSEC(1));
    } while (k_uptime_get() < end);

    return -ETIMEDOUT;
}

static int flash_write_enable(const struct spi_dt_spec *spi)
{
    uint8_t cmd = CMD_WRITE_ENABLE;
    struct spi_buf buf = {.buf = &cmd, .len = 1};
    struct spi_buf_set tx = {.buffers = &buf, .count = 1};
    return spi_write_dt(spi, &tx);
}

/* Flash API implementation */
static int flash_read(const struct device *dev, off_t offset,
                      void *data, size_t len)
{
    const struct flash_config *cfg = dev->config;
    struct flash_data *drv = dev->data;
    uint8_t cmd[4] = {
        CMD_READ,
        (offset >> 16) & 0xFF,
        (offset >> 8) & 0xFF,
        offset & 0xFF,
    };
    int ret;

    if (offset + len > cfg->size) {
        return -EINVAL;
    }

    struct spi_buf tx_buf = {.buf = cmd, .len = sizeof(cmd)};
    struct spi_buf rx_bufs[] = {
        {.buf = NULL, .len = sizeof(cmd)},  /* Dummy for command */
        {.buf = data, .len = len},
    };
    struct spi_buf_set tx = {.buffers = &tx_buf, .count = 1};
    struct spi_buf_set rx = {.buffers = rx_bufs, .count = 2};

    k_sem_take(&drv->lock, K_FOREVER);
    ret = spi_transceive_dt(&cfg->spi, &tx, &rx);
    k_sem_give(&drv->lock);

    return ret;
}

static int flash_write(const struct device *dev, off_t offset,
                       const void *data, size_t len)
{
    const struct flash_config *cfg = dev->config;
    struct flash_data *drv = dev->data;
    const uint8_t *src = data;
    int ret;

    if (offset + len > cfg->size) {
        return -EINVAL;
    }

    k_sem_take(&drv->lock, K_FOREVER);

    while (len > 0) {
        /* Calculate bytes to write in current page */
        size_t page_offset = offset % cfg->page_size;
        size_t write_len = MIN(len, cfg->page_size - page_offset);

        /* Enable writes */
        ret = flash_write_enable(&cfg->spi);
        if (ret < 0) {
            goto out;
        }

        /* Send page program command */
        uint8_t cmd[4] = {
            CMD_PAGE_PROGRAM,
            (offset >> 16) & 0xFF,
            (offset >> 8) & 0xFF,
            offset & 0xFF,
        };

        struct spi_buf tx_bufs[] = {
            {.buf = cmd, .len = sizeof(cmd)},
            {.buf = (void *)src, .len = write_len},
        };
        struct spi_buf_set tx = {.buffers = tx_bufs, .count = 2};

        ret = spi_write_dt(&cfg->spi, &tx);
        if (ret < 0) {
            goto out;
        }

        /* Wait for write complete */
        ret = flash_wait_ready(&cfg->spi, K_MSEC(10));
        if (ret < 0) {
            goto out;
        }

        offset += write_len;
        src += write_len;
        len -= write_len;
    }

    ret = 0;

out:
    k_sem_give(&drv->lock);
    return ret;
}

static int flash_erase(const struct device *dev, off_t offset, size_t size)
{
    const struct flash_config *cfg = dev->config;
    struct flash_data *drv = dev->data;
    int ret;

    if ((offset % cfg->sector_size) || (size % cfg->sector_size)) {
        return -EINVAL;
    }

    k_sem_take(&drv->lock, K_FOREVER);

    while (size > 0) {
        ret = flash_write_enable(&cfg->spi);
        if (ret < 0) {
            goto out;
        }

        uint8_t cmd[4] = {
            CMD_SECTOR_ERASE,
            (offset >> 16) & 0xFF,
            (offset >> 8) & 0xFF,
            offset & 0xFF,
        };

        struct spi_buf buf = {.buf = cmd, .len = sizeof(cmd)};
        struct spi_buf_set tx = {.buffers = &buf, .count = 1};

        ret = spi_write_dt(&cfg->spi, &tx);
        if (ret < 0) {
            goto out;
        }

        ret = flash_wait_ready(&cfg->spi, K_SECONDS(1));
        if (ret < 0) {
            goto out;
        }

        offset += cfg->sector_size;
        size -= cfg->sector_size;
    }

    ret = 0;

out:
    k_sem_give(&drv->lock);
    return ret;
}

static const struct flash_parameters *flash_get_parameters(
    const struct device *dev)
{
    static const struct flash_parameters params = {
        .write_block_size = 1,
        .erase_value = 0xFF,
    };
    return &params;
}

static const struct flash_driver_api flash_api = {
    .read = flash_read,
    .write = flash_write,
    .erase = flash_erase,
    .get_parameters = flash_get_parameters,
};

static int flash_init(const struct device *dev)
{
    const struct flash_config *cfg = dev->config;
    struct flash_data *drv = dev->data;
    uint8_t jedec_id[3];
    int ret;

    if (!spi_is_ready_dt(&cfg->spi)) {
        LOG_ERR("SPI bus not ready");
        return -ENODEV;
    }

    k_sem_init(&drv->lock, 1, 1);

    /* Read JEDEC ID */
    uint8_t cmd = CMD_READ_ID;
    struct spi_buf tx_buf = {.buf = &cmd, .len = 1};
    struct spi_buf rx_bufs[] = {
        {.buf = NULL, .len = 1},
        {.buf = jedec_id, .len = 3},
    };
    struct spi_buf_set tx = {.buffers = &tx_buf, .count = 1};
    struct spi_buf_set rx = {.buffers = rx_bufs, .count = 2};

    ret = spi_transceive_dt(&cfg->spi, &tx, &rx);
    if (ret < 0) {
        LOG_ERR("Failed to read JEDEC ID: %d", ret);
        return ret;
    }

    LOG_INF("Flash %s: JEDEC ID %02x %02x %02x, size %u bytes",
            dev->name, jedec_id[0], jedec_id[1], jedec_id[2], cfg->size);

    return 0;
}

#define FLASH_DEFINE(inst)                                              \
    static struct flash_data flash_data_##inst;                         \
    static const struct flash_config flash_config_##inst = {            \
        .spi = SPI_DT_SPEC_INST_GET(inst,                               \
                   SPI_WORD_SET(8) | SPI_TRANSFER_MSB, 0),              \
        .wp = GPIO_DT_SPEC_INST_GET_OR(inst, wp_gpios, {0}),            \
        .size = DT_INST_PROP(inst, size),                               \
        .page_size = DT_INST_PROP(inst, page_size),                     \
        .sector_size = DT_INST_PROP(inst, sector_size),                 \
    };                                                                  \
    DEVICE_DT_INST_DEFINE(inst, flash_init, NULL,                       \
                          &flash_data_##inst,                           \
                          &flash_config_##inst,                         \
                          POST_KERNEL,                                  \
                          CONFIG_FLASH_INIT_PRIORITY,                   \
                          &flash_api);

DT_INST_FOREACH_STATUS_OKAY(FLASH_DEFINE)
```

### Overlay

```dts
&spi1 {
    status = "okay";
    cs-gpios = <&gpio0 25 GPIO_ACTIVE_LOW>;

    flash0: flash@0 {
        compatible = "acme,spi-flash";
        reg = <0>;
        spi-max-frequency = <8000000>;
        size = <0x100000>;  /* 1MB */
        page-size = <256>;
        sector-size = <4096>;
    };
};
```

### Application Usage

```c
#include <zephyr/drivers/flash.h>

const struct device *flash = DEVICE_DT_GET(DT_NODELABEL(flash0));

int main(void)
{
    uint8_t data[256];

    if (!device_is_ready(flash)) {
        return -1;
    }

    /* Erase sector */
    flash_erase(flash, 0, 4096);

    /* Write data */
    memset(data, 0xAA, sizeof(data));
    flash_write(flash, 0, data, sizeof(data));

    /* Read back */
    memset(data, 0, sizeof(data));
    flash_read(flash, 0, data, sizeof(data));

    return 0;
}
```

---

## UART GPS Module

Complete UART-based GPS module driver.

### Binding: `acme,uart-gps.yaml`

```yaml
description: ACME UART GPS Module

compatible: "acme,uart-gps"

include: [uart-device.yaml]

properties:
  reset-gpios:
    type: phandle-array
    description: Hardware reset GPIO

  enable-gpios:
    type: phandle-array
    description: Enable/power GPIO

  pps-gpios:
    type: phandle-array
    description: Pulse per second GPIO
```

### Driver: `uart_gps.c`

```c
#define DT_DRV_COMPAT acme_uart_gps

#include <zephyr/device.h>
#include <zephyr/drivers/uart.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(uart_gps, CONFIG_GPS_LOG_LEVEL);

#define RX_BUFFER_SIZE 256
#define NMEA_MAX_LEN   82

typedef void (*gps_nmea_callback_t)(const struct device *dev,
                                    const char *sentence);

struct gps_config {
    const struct device *uart;
    struct gpio_dt_spec reset;
    struct gpio_dt_spec enable;
    struct gpio_dt_spec pps;
};

struct gps_data {
    uint8_t rx_buf[RX_BUFFER_SIZE];
    size_t rx_pos;
    char nmea_sentence[NMEA_MAX_LEN + 1];
    gps_nmea_callback_t callback;
    bool enabled;
};

/* UART ISR */
static void gps_uart_isr(const struct device *uart, void *user_data)
{
    const struct device *dev = user_data;
    struct gps_data *data = dev->data;

    if (!uart_irq_update(uart)) {
        return;
    }

    while (uart_irq_rx_ready(uart)) {
        uint8_t c;

        if (uart_fifo_read(uart, &c, 1) != 1) {
            break;
        }

        /* Start of NMEA sentence */
        if (c == '$') {
            data->rx_pos = 0;
        }

        /* Store character */
        if (data->rx_pos < RX_BUFFER_SIZE - 1) {
            data->rx_buf[data->rx_pos++] = c;
        }

        /* End of NMEA sentence */
        if (c == '\n') {
            data->rx_buf[data->rx_pos] = '\0';

            /* Copy to callback buffer */
            if (data->callback && data->rx_pos > 0) {
                memcpy(data->nmea_sentence, data->rx_buf,
                       MIN(data->rx_pos + 1, NMEA_MAX_LEN));
                data->nmea_sentence[NMEA_MAX_LEN] = '\0';
                data->callback(dev, data->nmea_sentence);
            }

            data->rx_pos = 0;
        }
    }
}

/* GPS API */
static int gps_enable(const struct device *dev)
{
    const struct gps_config *cfg = dev->config;
    struct gps_data *data = dev->data;

    if (cfg->enable.port) {
        gpio_pin_set_dt(&cfg->enable, 1);
        k_sleep(K_MSEC(100));
    }

    uart_irq_rx_enable(cfg->uart);
    data->enabled = true;

    LOG_INF("GPS enabled");
    return 0;
}

static int gps_disable(const struct device *dev)
{
    const struct gps_config *cfg = dev->config;
    struct gps_data *data = dev->data;

    uart_irq_rx_disable(cfg->uart);

    if (cfg->enable.port) {
        gpio_pin_set_dt(&cfg->enable, 0);
    }

    data->enabled = false;
    return 0;
}

static int gps_reset(const struct device *dev)
{
    const struct gps_config *cfg = dev->config;

    if (!cfg->reset.port) {
        return -ENOTSUP;
    }

    gpio_pin_set_dt(&cfg->reset, 1);
    k_sleep(K_MSEC(100));
    gpio_pin_set_dt(&cfg->reset, 0);
    k_sleep(K_MSEC(500));

    return 0;
}

static int gps_set_callback(const struct device *dev,
                            gps_nmea_callback_t callback)
{
    struct gps_data *data = dev->data;
    data->callback = callback;
    return 0;
}

static int gps_send_command(const struct device *dev, const char *cmd)
{
    const struct gps_config *cfg = dev->config;

    for (size_t i = 0; cmd[i] != '\0'; i++) {
        uart_poll_out(cfg->uart, cmd[i]);
    }
    uart_poll_out(cfg->uart, '\r');
    uart_poll_out(cfg->uart, '\n');

    return 0;
}

struct gps_driver_api {
    int (*enable)(const struct device *dev);
    int (*disable)(const struct device *dev);
    int (*reset)(const struct device *dev);
    int (*set_callback)(const struct device *dev, gps_nmea_callback_t cb);
    int (*send_command)(const struct device *dev, const char *cmd);
};

static const struct gps_driver_api gps_api = {
    .enable = gps_enable,
    .disable = gps_disable,
    .reset = gps_reset,
    .set_callback = gps_set_callback,
    .send_command = gps_send_command,
};

static int gps_init(const struct device *dev)
{
    const struct gps_config *cfg = dev->config;
    struct gps_data *data = dev->data;

    if (!device_is_ready(cfg->uart)) {
        LOG_ERR("UART not ready");
        return -ENODEV;
    }

    /* Configure GPIOs */
    if (cfg->reset.port && gpio_is_ready_dt(&cfg->reset)) {
        gpio_pin_configure_dt(&cfg->reset, GPIO_OUTPUT_INACTIVE);
    }

    if (cfg->enable.port && gpio_is_ready_dt(&cfg->enable)) {
        gpio_pin_configure_dt(&cfg->enable, GPIO_OUTPUT_INACTIVE);
    }

    if (cfg->pps.port && gpio_is_ready_dt(&cfg->pps)) {
        gpio_pin_configure_dt(&cfg->pps, GPIO_INPUT);
    }

    data->rx_pos = 0;
    data->enabled = false;

    /* Set up UART ISR */
    uart_irq_callback_user_data_set(cfg->uart, gps_uart_isr, (void *)dev);

    LOG_INF("GPS %s initialized", dev->name);
    return 0;
}

#define GPS_DEFINE(inst)                                                \
    static struct gps_data gps_data_##inst;                             \
    static const struct gps_config gps_config_##inst = {                \
        .uart = DEVICE_DT_GET(DT_INST_BUS(inst)),                       \
        .reset = GPIO_DT_SPEC_INST_GET_OR(inst, reset_gpios, {0}),      \
        .enable = GPIO_DT_SPEC_INST_GET_OR(inst, enable_gpios, {0}),    \
        .pps = GPIO_DT_SPEC_INST_GET_OR(inst, pps_gpios, {0}),          \
    };                                                                  \
    DEVICE_DT_INST_DEFINE(inst, gps_init, NULL,                         \
                          &gps_data_##inst,                             \
                          &gps_config_##inst,                           \
                          POST_KERNEL,                                  \
                          CONFIG_GPS_INIT_PRIORITY,                     \
                          &gps_api);

DT_INST_FOREACH_STATUS_OKAY(GPS_DEFINE)
```

### Overlay

```dts
&uart1 {
    status = "okay";
    current-speed = <9600>;

    gps: gps {
        compatible = "acme,uart-gps";
        reset-gpios = <&gpio0 10 GPIO_ACTIVE_HIGH>;
        enable-gpios = <&gpio0 11 GPIO_ACTIVE_HIGH>;
    };
};
```

---

## Complete Sensor with Triggers

See [sensor-drivers.md](sensor-drivers.md) for a complete sensor driver with interrupt-based triggers.
