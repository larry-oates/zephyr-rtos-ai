# Devicetree Examples

Complete working examples for common hardware configurations.

---

## 1. GPIO LED (Blinky)

**DTS/Overlay:**
```devicetree
/ {
    leds {
        compatible = "gpio-leds";
        led0: led_0 {
            gpios = <&gpio0 13 GPIO_ACTIVE_LOW>;
            label = "Green LED";
        };
    };
    aliases {
        led0 = &led0;
    };
};
```

**C Code:**
```c
#include <zephyr/drivers/gpio.h>

#define LED0_NODE DT_ALIAS(led0)
static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(LED0_NODE, gpios);

int main(void) {
    if (!gpio_is_ready_dt(&led)) {
        return -ENODEV;
    }
    gpio_pin_configure_dt(&led, GPIO_OUTPUT_ACTIVE);
    gpio_pin_set_dt(&led, 1);
    return 0;
}
```

---

## 2. I2C Sensor

**DTS/Overlay:**
```devicetree
&i2c1 {
    status = "okay";
    clock-frequency = <I2C_BITRATE_FAST>;

    bme280: bme280@76 {
        compatible = "bosch,bme280";
        reg = <0x76>;
    };
};
```

**C Code:**
```c
#include <zephyr/drivers/sensor.h>

#define BME280_NODE DT_NODELABEL(bme280)
const struct device *const sensor = DEVICE_DT_GET(BME280_NODE);

int main(void) {
    if (!device_is_ready(sensor)) {
        return -ENODEV;
    }
    struct sensor_value temp;
    sensor_sample_fetch(sensor);
    sensor_channel_get(sensor, SENSOR_CHAN_AMBIENT_TEMP, &temp);
    printk("Temp: %d.%06d\n", temp.val1, temp.val2);
    return 0;
}
```

---

## 3. SPI Flash with Partitions

**DTS/Overlay:**
```devicetree
&spi1 {
    status = "okay";
    cs-gpios = <&gpio0 12 GPIO_ACTIVE_LOW>;

    mx25r64: flash@0 {
        compatible = "jedec,spi-nor";
        reg = <0>;
        spi-max-frequency = <80000000>;
        jedec-id = [c2 28 17];
        size = <67108864>;  /* 64 Mbit = 8 MB */

        partitions {
            compatible = "fixed-partitions";
            #address-cells = <1>;
            #size-cells = <1>;

            storage_partition: partition@0 {
                label = "storage";
                reg = <0x00000000 0x00100000>;  /* 1 MB */
            };
            littlefs_partition: partition@100000 {
                label = "littlefs";
                reg = <0x00100000 0x00700000>;  /* 7 MB */
            };
        };
    };
};

/ {
    chosen {
        zephyr,flash = &mx25r64;
    };
};
```

---

## 4. PWM Buzzer

**DTS/Overlay:**
```devicetree
/ {
    pwm_buzzer {
        compatible = "pwm-leds";
        buzzer: buzzer_0 {
            pwms = <&pwm0 2 1000000 PWM_POLARITY_NORMAL>;  /* 1ms period */
            label = "Buzzer";
        };
    };
};
```

**C Code:**
```c
#include <zephyr/drivers/pwm.h>

#define BUZZER_NODE DT_NODELABEL(buzzer)
static const struct pwm_dt_spec buzzer = PWM_DT_SPEC_GET(BUZZER_NODE);

void beep(uint32_t frequency_hz, uint32_t duration_ms) {
    uint32_t period = 1000000000U / frequency_hz;  /* ns */
    pwm_set_dt(&buzzer, period, period / 2);       /* 50% duty */
    k_msleep(duration_ms);
    pwm_set_pulse_dt(&buzzer, 0);                  /* Off */
}
```

---

## 5. UART with Pin Control

**DTS/Overlay (Nordic nRF):**
```devicetree
&pinctrl {
    uart1_default: uart1_default {
        group1 {
            psels = <NRF_PSEL(UART_TX, 1, 1)>,
                    <NRF_PSEL(UART_RX, 1, 2)>;
        };
    };
    uart1_sleep: uart1_sleep {
        group1 {
            psels = <NRF_PSEL(UART_TX, 1, 1)>,
                    <NRF_PSEL(UART_RX, 1, 2)>;
            low-power-enable;
        };
    };
};

&uart1 {
    status = "okay";
    current-speed = <115200>;
    pinctrl-0 = <&uart1_default>;
    pinctrl-1 = <&uart1_sleep>;
    pinctrl-names = "default", "sleep";
};
```

**C Code:**
```c
#include <zephyr/drivers/uart.h>

#define UART1_NODE DT_NODELABEL(uart1)
const struct device *const uart = DEVICE_DT_GET(UART1_NODE);

int main(void) {
    if (!device_is_ready(uart)) {
        return -ENODEV;
    }
    uart_poll_out(uart, 'H');
    uart_poll_out(uart, 'i');
    return 0;
}
```

---

## 6. ADC Channel Configuration

**DTS/Overlay:**
```devicetree
/ {
    zephyr,user {
        io-channels = <&adc0 0>, <&adc0 1>;
        io-channel-names = "voltage", "current";
    };
};

&adc0 {
    status = "okay";
    #address-cells = <1>;
    #size-cells = <0>;

    channel@0 {
        reg = <0>;
        zephyr,gain = "ADC_GAIN_1_6";
        zephyr,reference = "ADC_REF_INTERNAL";
        zephyr,acquisition-time = <ADC_ACQ_TIME_DEFAULT>;
        zephyr,resolution = <12>;
        zephyr,input-positive = <NRF_SAADC_AIN0>;
    };

    channel@1 {
        reg = <1>;
        zephyr,gain = "ADC_GAIN_1_6";
        zephyr,reference = "ADC_REF_INTERNAL";
        zephyr,acquisition-time = <ADC_ACQ_TIME_DEFAULT>;
        zephyr,resolution = <12>;
        zephyr,input-positive = <NRF_SAADC_AIN1>;
    };
};
```

**C Code:**
```c
#include <zephyr/drivers/adc.h>

#define ADC_NODE DT_NODELABEL(adc0)
#define ADC_CHANNEL_0 DT_CHILD(ADC_NODE, channel_0)

static const struct adc_dt_spec adc_voltage = ADC_DT_SPEC_GET(ADC_CHANNEL_0);

int read_voltage(void) {
    int16_t buf;
    struct adc_sequence seq = {
        .buffer = &buf,
        .buffer_size = sizeof(buf),
    };
    adc_sequence_init_dt(&adc_voltage, &seq);
    adc_read_dt(&adc_voltage, &seq);
    return buf;
}
```

---

## 7. CAN Bus Setup

**DTS/Overlay:**
```devicetree
&can1 {
    status = "okay";
    pinctrl-0 = <&can1_default>;
    pinctrl-names = "default";
    bitrate = <500000>;
    sample-point = <875>;
};
```

**C Code:**
```c
#include <zephyr/drivers/can.h>

#define CAN_NODE DT_NODELABEL(can1)
const struct device *const can = DEVICE_DT_GET(CAN_NODE);

int main(void) {
    if (!device_is_ready(can)) {
        return -ENODEV;
    }
    can_start(can);

    struct can_frame frame = {
        .id = 0x123,
        .dlc = 8,
        .data = {1, 2, 3, 4, 5, 6, 7, 8},
    };
    can_send(can, &frame, K_MSEC(100), NULL, NULL);
    return 0;
}
```

---

## 8. Timer/Counter Configuration

**DTS/Overlay:**
```devicetree
&timer0 {
    status = "okay";
};

/ {
    chosen {
        zephyr,counter = &timer0;
    };
};
```

**C Code:**
```c
#include <zephyr/drivers/counter.h>

#define COUNTER_NODE DT_CHOSEN(zephyr_counter)
const struct device *const counter = DEVICE_DT_GET(COUNTER_NODE);

void alarm_callback(const struct device *dev, uint8_t chan,
                    uint32_t ticks, void *user_data) {
    printk("Alarm fired!\n");
}

int main(void) {
    if (!device_is_ready(counter)) {
        return -ENODEV;
    }

    struct counter_alarm_cfg alarm = {
        .callback = alarm_callback,
        .ticks = counter_us_to_ticks(counter, 1000000),  /* 1 second */
        .flags = 0,
    };

    counter_start(counter);
    counter_set_channel_alarm(counter, 0, &alarm);
    return 0;
}
```

---

## 9. GPIO Keys (Buttons)

**DTS/Overlay:**
```devicetree
/ {
    buttons {
        compatible = "gpio-keys";
        button0: button_0 {
            gpios = <&gpio0 11 (GPIO_PULL_UP | GPIO_ACTIVE_LOW)>;
            label = "User Button";
            zephyr,code = <INPUT_KEY_0>;
        };
    };

    aliases {
        sw0 = &button0;
    };
};
```

**C Code:**
```c
#include <zephyr/drivers/gpio.h>

#define SW0_NODE DT_ALIAS(sw0)
static const struct gpio_dt_spec button = GPIO_DT_SPEC_GET(SW0_NODE, gpios);
static struct gpio_callback button_cb_data;

void button_pressed(const struct device *dev, struct gpio_callback *cb,
                    uint32_t pins) {
    printk("Button pressed!\n");
}

int main(void) {
    gpio_pin_configure_dt(&button, GPIO_INPUT);
    gpio_pin_interrupt_configure_dt(&button, GPIO_INT_EDGE_TO_ACTIVE);
    gpio_init_callback(&button_cb_data, button_pressed, BIT(button.pin));
    gpio_add_callback(button.port, &button_cb_data);
    return 0;
}
```

---

## 10. Display (SPI)

**DTS/Overlay:**
```devicetree
&spi2 {
    status = "okay";
    cs-gpios = <&gpio0 25 GPIO_ACTIVE_LOW>;

    st7789v: st7789v@0 {
        compatible = "sitronix,st7789v";
        reg = <0>;
        spi-max-frequency = <20000000>;
        cmd-data-gpios = <&gpio0 24 GPIO_ACTIVE_LOW>;
        reset-gpios = <&gpio0 23 GPIO_ACTIVE_LOW>;
        width = <240>;
        height = <320>;
        x-offset = <0>;
        y-offset = <0>;
        vcom = <0x19>;
        gctrl = <0x35>;
        vrhs = <0x12>;
        vdvs = <0x20>;
        mdac = <0x00>;
        gamma = <0x01>;
        colmod = <0x05>;
        lcm = <0x2c>;
        porch-param = [0c 0c 00 33 33];
        cmd2en-param = [5a 69 02 01];
        pwctrl1-param = [a4 a1];
        pvgam-param = [D0 04 0D 11 13 2B 3F 54 4C 18 0D 0B 1F 23];
        nvgam-param = [D0 04 0C 11 13 2C 3F 44 51 2F 1F 1F 20 23];
        ram-param = [00 F0];
        rgb-param = [CD 08 14];
    };
};

/ {
    chosen {
        zephyr,display = &st7789v;
    };
};
```

---

## 11. External Interrupt (EXTI)

**DTS/Overlay:**
```devicetree
/ {
    gpio_keys {
        compatible = "gpio-keys";
        motion_sensor: motion_sensor {
            gpios = <&gpio0 7 (GPIO_ACTIVE_HIGH | GPIO_PULL_DOWN)>;
            label = "Motion Sensor INT";
        };
    };
};
```

**C Code:**
```c
#define MOTION_NODE DT_NODELABEL(motion_sensor)
static const struct gpio_dt_spec motion = GPIO_DT_SPEC_GET(MOTION_NODE, gpios);

void motion_detected(const struct device *dev, struct gpio_callback *cb,
                     uint32_t pins) {
    printk("Motion detected!\n");
}
```

---

## 12. Watchdog Timer

**DTS/Overlay:**
```devicetree
&wdt0 {
    status = "okay";
};
```

**C Code:**
```c
#include <zephyr/drivers/watchdog.h>

#define WDT_NODE DT_NODELABEL(wdt0)
const struct device *const wdt = DEVICE_DT_GET(WDT_NODE);

int main(void) {
    struct wdt_timeout_cfg cfg = {
        .window.min = 0,
        .window.max = 5000,  /* 5 seconds */
        .callback = NULL,
        .flags = WDT_FLAG_RESET_SOC,
    };

    int wdt_channel = wdt_install_timeout(wdt, &cfg);
    wdt_setup(wdt, WDT_OPT_PAUSE_HALTED_BY_DBG);

    while (1) {
        wdt_feed(wdt, wdt_channel);
        k_msleep(1000);
    }
}
