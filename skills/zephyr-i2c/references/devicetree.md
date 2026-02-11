# I2C Devicetree Reference

Complete devicetree binding reference for Zephyr I2C controllers and devices.

## Table of Contents

1. [I2C Controller Properties](#i2c-controller-properties)
2. [I2C Device Properties](#i2c-device-properties)
3. [Common Patterns](#common-patterns)
4. [Target/Slave Mode](#targetslave-mode)
5. [I2C Switches/Mux](#i2c-switchesmux)
6. [Vendor-Specific Properties](#vendor-specific-properties)

---

## I2C Controller Properties

From `dts/bindings/i2c/i2c-controller.yaml`:

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `#address-cells` | const | yes | Must be 1 |
| `#size-cells` | const | yes | Must be 0 |
| `clock-frequency` | int | no | Initial clock frequency in Hz |
| `sq-size` | int | no | RTIO submission queue size (default: 4) |
| `cq-size` | int | no | RTIO completion queue size (default: 4) |

### Basic Controller Example

```dts
&i2c0 {
    status = "okay";
    #address-cells = <1>;
    #size-cells = <0>;
    pinctrl-0 = <&i2c0_default>;
    pinctrl-names = "default";
    clock-frequency = <I2C_BITRATE_FAST>;
};
```

### Clock Frequency Constants

Use these in devicetree overlays:

| Constant | Value | Speed |
|----------|-------|-------|
| `I2C_BITRATE_STANDARD` | 100000 | 100 kHz |
| `I2C_BITRATE_FAST` | 400000 | 400 kHz |
| `I2C_BITRATE_FAST_PLUS` | 1000000 | 1 MHz |
| `I2C_BITRATE_HIGH` | 3400000 | 3.4 MHz |
| `I2C_BITRATE_ULTRA` | 5000000 | 5 MHz |

---

## I2C Device Properties

From `dts/bindings/i2c/i2c-device.yaml`:

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `reg` | int | yes | 7-bit I2C device address |

### From Included `power.yaml`

| Property | Type | Description |
|----------|------|-------------|
| `supply-gpios` | phandle-array | GPIO controlling device power |
| `vin-supply` | phandle | Reference to power regulator |

### Basic Device Example

```dts
&i2c0 {
    status = "okay";
    clock-frequency = <I2C_BITRATE_STANDARD>;

    /* Temperature sensor at address 0x48 */
    temp_sensor: tmp102@48 {
        compatible = "ti,tmp102";
        reg = <0x48>;
    };

    /* Accelerometer at address 0x1D */
    accel: lis2dh@1d {
        compatible = "st,lis2dh";
        reg = <0x1d>;
    };
};
```

### Device with Power Control

```dts
&i2c0 {
    sensor@48 {
        compatible = "vendor,sensor";
        reg = <0x48>;
        supply-gpios = <&gpio0 5 GPIO_ACTIVE_HIGH>;
        vin-supply = <&vdd_3v3>;
    };
};
```

---

## Common Patterns

### Using DT_NODELABEL

```dts
/* In board DTS */
&i2c0 {
    my_sensor: sensor@48 {
        compatible = "vendor,sensor";
        reg = <0x48>;
    };
};
```

```c
/* In application code */
#define SENSOR_NODE DT_NODELABEL(my_sensor)
static const struct i2c_dt_spec sensor = I2C_DT_SPEC_GET(SENSOR_NODE);
```

### Using DT_ALIAS

```dts
/* In board DTS */
/ {
    aliases {
        i2c-0 = &i2c0;
        temp-sensor = &tmp102;
    };
};

&i2c0 {
    tmp102: tmp102@48 {
        compatible = "ti,tmp102";
        reg = <0x48>;
    };
};
```

```c
/* In application code */
#define I2C_DEV DT_ALIAS(i2c_0)
#define SENSOR DT_ALIAS(temp_sensor)
```

### Multiple Devices on One Bus

```dts
&i2c0 {
    status = "okay";
    clock-frequency = <I2C_BITRATE_FAST>;

    eeprom@50 {
        compatible = "atmel,at24";
        reg = <0x50>;
    };

    rtc@68 {
        compatible = "nxp,pcf8563";
        reg = <0x68>;
    };

    gpio_expander@20 {
        compatible = "nxp,pca9535";
        reg = <0x20>;
        gpio-controller;
        #gpio-cells = <2>;
    };
};
```

### Overlay for Custom Board

```dts
/* boards/my_board.overlay */
&i2c1 {
    status = "okay";
    pinctrl-0 = <&i2c1_sda_pb7 &i2c1_scl_pb6>;
    pinctrl-names = "default";
    clock-frequency = <I2C_BITRATE_FAST>;

    custom_sensor: sensor@29 {
        compatible = "vendor,custom-sensor";
        reg = <0x29>;
    };
};
```

---

## Target/Slave Mode

### EEPROM Target (Zephyr Built-in)

```dts
&i2c0 {
    eeprom0: eeprom@52 {
        compatible = "zephyr,i2c-target-eeprom";
        reg = <0x52>;
        size = <256>;  /* EEPROM size in bytes */
    };
};
```

### Nordic nRF TWIS (Target Mode)

```dts
&pinctrl {
    i2c2_default: i2c2_default {
        group1 {
            psels = <NRF_PSEL(TWIS_SDA, 0, 26)>,
                    <NRF_PSEL(TWIS_SCL, 0, 25)>;
            bias-pull-up;
        };
    };

    i2c2_sleep: i2c2_sleep {
        group1 {
            psels = <NRF_PSEL(TWIS_SDA, 0, 26)>,
                    <NRF_PSEL(TWIS_SCL, 0, 25)>;
            low-power-enable;
        };
    };
};

&i2c2 {
    compatible = "nordic,nrf-twis";
    pinctrl-0 = <&i2c2_default>;
    pinctrl-1 = <&i2c2_sleep>;
    pinctrl-names = "default", "sleep";
    status = "okay";
};
```

### ITE Target Mode

```dts
&i2c0 {
    status = "okay";
    pinctrl-0 = <&i2c5_clk_gpa4_default &i2c5_data_gpa5_default>;
    pinctrl-names = "default";
    scl-gpios = <&gpioa 4 0>;
    sda-gpios = <&gpioa 5 0>;

    target-enable;  /* Enable target mode */

    i2c0_target: target@52 {
        compatible = "ite,target-i2c";
        reg = <0x52>;
    };
};
```

---

## I2C Switches/Mux

### TI TCA9546A Switch

```dts
&i2c0 {
    mux: tca9546a@77 {
        compatible = "ti,tca9546a";
        reg = <0x77>;
        status = "okay";
        #address-cells = <1>;
        #size-cells = <0>;
        reset-gpios = <&gpio5 3 GPIO_ACTIVE_LOW>;

        mux_i2c@0 {
            compatible = "ti,tca9546a-channel";
            reg = <0>;
            #address-cells = <1>;
            #size-cells = <0>;

            temp_sens_0: tmp11x@49 {
                compatible = "ti,tmp11x";
                reg = <0x49>;
            };
        };

        mux_i2c@1 {
            compatible = "ti,tca9546a-channel";
            reg = <1>;
            #address-cells = <1>;
            #size-cells = <0>;

            temp_sens_1: tmp11x@49 {
                compatible = "ti,tmp11x";
                reg = <0x49>;
            };
        };
    };
};
```

### TCA954x Properties

| Property | Type | Description |
|----------|------|-------------|
| `reset-gpios` | phandle-array | Active-low reset GPIO |
| `i2c-mux-idle-disconnect` | bool | Disconnect channels when idle |

---

## Vendor-Specific Properties

### STM32

```dts
&i2c1 {
    status = "okay";
    pinctrl-0 = <&i2c1_scl_pb8 &i2c1_sda_pb9>;
    pinctrl-names = "default";
    clock-frequency = <I2C_BITRATE_FAST>;

    /* Optional: DMA support */
    dmas = <&dma1 6 3 0x400>,
           <&dma1 7 3 0x400>;
    dma-names = "tx", "rx";

    /* Optional: precomputed timings */
    timings = <...>;
};
```

### Nordic nRF

```dts
&i2c0 {
    compatible = "nordic,nrf-twim";
    status = "okay";
    pinctrl-0 = <&i2c0_default>;
    pinctrl-names = "default";
    /* easydma-maxcnt-bits set in SoC DTS */
};
```

### ESP32

```dts
&i2c0 {
    status = "okay";
    clock-frequency = <I2C_BITRATE_FAST>;
    sda-gpios = <&gpio0 21 GPIO_OPEN_DRAIN>;
    scl-gpios = <&gpio0 22 GPIO_OPEN_DRAIN>;
    scl-timeout-us = <100000>;  /* Clock stretching timeout */
};
```

### GPIO Bitbang

```dts
i2c_gpio: i2c-gpio {
    compatible = "gpio-i2c";
    status = "okay";
    sda-gpios = <&gpio0 4 (GPIO_OPEN_DRAIN | GPIO_PULL_UP)>;
    scl-gpios = <&gpio0 5 (GPIO_OPEN_DRAIN | GPIO_PULL_UP)>;
    #address-cells = <1>;
    #size-cells = <0>;
};
```

### Common Vendor Properties

| Vendor | Properties |
|--------|------------|
| **STM32** | `timings`, `dmas`, `dma-names` |
| **ESP32** | `tx-lsb`, `rx-lsb`, `scl-timeout-us`, `scl-gpios`, `sda-gpios` |
| **Nordic** | `easydma-maxcnt-bits` (set in SoC DTS) |
| **NXP LPI2C** | `bus-idle-timeout`, `scl-gpios`, `sda-gpios` |
| **Renesas** | `rise-time-ns`, `fall-time-ns`, `duty-cycle-percent` |
| **DesignWare** | `lcnt-offset`, `hcnt-offset`, `sda-timeout-value`, `scl-timeout-value` |
| **ITE** | `port-num`, `channel-switch-sel`, `target-enable`, `target-pio-mode` |

---

## Bus Recovery GPIOs

Many drivers support bus recovery via GPIO bitbanging:

```dts
&i2c0 {
    /* SCL/SDA GPIOs for bus recovery */
    scl-gpios = <&gpio0 22 GPIO_OPEN_DRAIN>;
    sda-gpios = <&gpio0 21 GPIO_OPEN_DRAIN>;
};
```

Enable with corresponding Kconfig:
- `CONFIG_I2C_STM32_BUS_RECOVERY`
- `CONFIG_I2C_MCUX_LPI2C_BUS_RECOVERY`
- `CONFIG_I2C_OMAP_BUS_RECOVERY`
- etc.
