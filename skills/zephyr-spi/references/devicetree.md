# SPI Devicetree Reference

Complete reference for SPI devicetree configuration in Zephyr.

## Table of Contents

1. [Controller Properties](#controller-properties)
2. [Device Properties](#device-properties)
3. [Examples](#examples)
4. [Overlays](#overlays)

---

## Controller Properties

From `dts/bindings/spi/spi-controller.yaml`:

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `#address-cells` | int | Yes | Always `1` |
| `#size-cells` | int | Yes | Always `0` |
| `cs-gpios` | phandle-array | No | Array of CS GPIO specs |
| `clock-frequency` | int | No | Peripheral clock frequency (Hz) |
| `overrun-character` | int | No | Byte sent when TX exhausted but RX continues |

### cs-gpios

Array of GPIO specifications for chip select lines. Index corresponds to child node `reg` value.

```dts
&spi0 {
    cs-gpios = <&gpio0 4 GPIO_ACTIVE_LOW>,   /* CS0 */
               <&gpio0 5 GPIO_ACTIVE_LOW>;   /* CS1 */

    device0@0 { reg = <0>; ... };  /* Uses CS0 */
    device1@1 { reg = <1>; ... };  /* Uses CS1 */
};
```

If not defined, controller uses hardware CS or no CS management.

---

## Device Properties

From `dts/bindings/spi/spi-device.yaml`:

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `reg` | int | Yes | CS index (matches cs-gpios array) |
| `spi-max-frequency` | int | Yes | Maximum clock frequency (Hz) |
| `spi-cpol` | boolean | No | Clock polarity (idle high) |
| `spi-cpha` | boolean | No | Clock phase (sample on 2nd edge) |
| `spi-lsb-first` | boolean | No | LSB first bit order |
| `spi-hold-cs` | boolean | No | Keep CS active between transactions |
| `spi-cs-high` | boolean | No | CS active high (unusual) |
| `duplex` | int | No | Full (0) or half (2048) duplex |
| `frame-format` | int | No | Motorola (0) or TI (32768) |
| `spi-cs-setup-delay-ns` | int | No | CS setup time (ns) |
| `spi-cs-hold-delay-ns` | int | No | CS hold time (ns) |
| `spi-interframe-delay-ns` | int | No | Delay between words (ns) |

### SPI Modes

| Mode | CPOL | CPHA | Properties |
|------|------|------|------------|
| 0 | 0 | 0 | (none - default) |
| 1 | 0 | 1 | `spi-cpha;` |
| 2 | 1 | 0 | `spi-cpol;` |
| 3 | 1 | 1 | `spi-cpol; spi-cpha;` |

---

## Examples

### Basic SPI Controller with One Device

```dts
&spi0 {
    status = "okay";
    pinctrl-0 = <&spi0_default>;
    pinctrl-names = "default";
    cs-gpios = <&gpio0 4 GPIO_ACTIVE_LOW>;

    flash0: w25q128@0 {
        compatible = "jedec,spi-nor";
        reg = <0>;
        spi-max-frequency = <40000000>;  /* 40 MHz */
        /* Mode 0 (default) */
    };
};
```

### Multiple Devices on Same Bus

```dts
&spi1 {
    status = "okay";
    pinctrl-0 = <&spi1_default>;
    pinctrl-names = "default";
    cs-gpios = <&gpio0 10 GPIO_ACTIVE_LOW>,
               <&gpio0 11 GPIO_ACTIVE_LOW>,
               <&gpio0 12 GPIO_ACTIVE_LOW>;

    sensor0: bme280@0 {
        compatible = "bosch,bme280";
        reg = <0>;
        spi-max-frequency = <10000000>;
    };

    display0: ili9341@1 {
        compatible = "ilitek,ili9341";
        reg = <1>;
        spi-max-frequency = <20000000>;
        spi-cpol;  /* Mode 2 */
    };

    adc0: mcp3008@2 {
        compatible = "microchip,mcp3008";
        reg = <2>;
        spi-max-frequency = <1000000>;
    };
};
```

### Device with Mode 3 and CS Timing

```dts
eeprom0: at25@0 {
    compatible = "atmel,at25";
    reg = <0>;
    spi-max-frequency = <1000000>;
    spi-cpol;
    spi-cpha;
    spi-cs-setup-delay-ns = <100>;
    spi-cs-hold-delay-ns = <100>;
};
```

### Software Bit-Bang SPI

```dts
spi_bitbang: spi-bitbang {
    compatible = "zephyr,spi-bitbang";
    status = "okay";
    #address-cells = <1>;
    #size-cells = <0>;
    clk-gpios = <&gpio0 1 GPIO_ACTIVE_HIGH>;
    mosi-gpios = <&gpio0 2 GPIO_ACTIVE_HIGH>;
    miso-gpios = <&gpio0 3 GPIO_ACTIVE_HIGH>;
    cs-gpios = <&gpio0 4 GPIO_ACTIVE_LOW>;

    my_device@0 {
        reg = <0>;
        spi-max-frequency = <100000>;
    };
};
```

---

## Overlays

### Adding a Device to Existing Controller

```dts
/* boards/my_board.overlay */

&spi0 {
    status = "okay";

    my_sensor: sensor@0 {
        compatible = "vendor,sensor";
        reg = <0>;
        spi-max-frequency = <4000000>;
        label = "MY_SENSOR";
    };
};
```

### Overriding CS GPIO

```dts
&spi0 {
    cs-gpios = <&gpio0 20 GPIO_ACTIVE_LOW>;  /* Change CS pin */
};
```

### Changing Device Frequency

```dts
&flash0 {
    spi-max-frequency = <80000000>;  /* Increase to 80 MHz */
};
```

### Enabling Controller

```dts
&spi2 {
    status = "okay";
    pinctrl-0 = <&spi2_default>;
    pinctrl-names = "default";
};
```

---

## Pinctrl Integration

SPI controllers typically require pinctrl configuration:

```dts
&pinctrl {
    spi0_default: spi0_default {
        group1 {
            psels = <NRF_PSEL(SPIM_SCK, 0, 1)>,
                    <NRF_PSEL(SPIM_MOSI, 0, 2)>,
                    <NRF_PSEL(SPIM_MISO, 0, 3)>;
        };
    };
};

&spi0 {
    pinctrl-0 = <&spi0_default>;
    pinctrl-names = "default";
};
```

The exact pinctrl syntax varies by SoC family. Consult board-specific documentation.

---

## Common Binding Files

| File | Purpose |
|------|---------|
| `dts/bindings/spi/spi-controller.yaml` | Base controller binding |
| `dts/bindings/spi/spi-device.yaml` | Base device binding |
| `dts/bindings/spi/zephyr,spi-bitbang.yaml` | Software SPI |
| `dts/bindings/spi/<vendor>,<controller>.yaml` | Vendor-specific controllers |
