# Devicetree Examples

## 1. GPIO LED (Blinky)
**DTS/Overlay:**
```devicetree
/ {
    leds {
        compatible = "gpio-leds";
        led0: led_0 {
            gpios = <&gpio0 13 GPIO_ACTIVE_LOW>;
        };
    };
    aliases {
        led0 = &led0;
    };
};
```
**C Code:**
```c
#define LED0_NODE DT_ALIAS(led0)
static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(LED0_NODE, gpios);
gpio_pin_configure_dt(&led, GPIO_OUTPUT_ACTIVE);
gpio_pin_set_dt(&led, 1);
```

## 2. I2C Sensor
**DTS/Overlay:**
```devicetree
&i2c1 {
    status = "okay";
    bme280@76 {
        compatible = "bosch,bme280";
        reg = <0x76>;
    };
};
```
**C Code:**
```c
#define BME280_NODE DT_INST(0, bosch_bme280)
const struct device *const dev = DEVICE_DT_GET(BME280_NODE);
```

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
        partitions {
            compatible = "fixed-partitions";
            #address-cells = <1>;
            #size-cells = <1>;
            storage_partition: partition@0 {
                label = "storage";
                reg = <0x00000000 0x00010000>;
            };
        };
    };
};
```

## 4. PWM Buzzer
**DTS/Overlay:**
```devicetree
/ {
    pwm_buzzer {
        compatible = "pwm-leds";
        buzzer: buzzer_0 {
            pwms = <&pwm0 2 10000 PWM_POLARITY_NORMAL>;
        };
    };
};
```
**C Code:**
```c
#define BUZZER_NODE DT_NODELABEL(buzzer)
static const struct pwm_dt_spec buzzer = PWM_DT_SPEC_GET(BUZZER_NODE);
pwm_set_pulse_dt(&buzzer, period / 2);
```
