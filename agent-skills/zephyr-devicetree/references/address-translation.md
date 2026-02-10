# Address Translation in Devicetree

Address translation describes how addresses are mapped between different levels of the hardware hierarchy using `#address-cells`, `#size-cells`, and `ranges`.

## Overview

Devicetree addresses are **hierarchical**. Child node addresses are in the parent's address space. Translation properties define how to convert between address spaces.

## Core Properties

| Property | Description |
|----------|-------------|
| `#address-cells` | Number of 32-bit cells for addresses in child nodes |
| `#size-cells` | Number of 32-bit cells for sizes in child nodes |
| `ranges` | Address translation from child to parent space |
| `reg` | Address and size of the node's resources |

## Basic Example

```devicetree
/ {
    #address-cells = <1>;  /* 32-bit addresses */
    #size-cells = <1>;     /* 32-bit sizes */

    soc@40000000 {
        compatible = "simple-bus";
        #address-cells = <1>;
        #size-cells = <1>;
        ranges = <0x0 0x40000000 0x10000000>;
        /* Child 0x0 = Parent 0x40000000, size 256MB */

        uart0: uart@1000 {
            reg = <0x1000 0x100>;
            /* Actual address: 0x40000000 + 0x1000 = 0x40001000 */
        };
    };
};
```

## #address-cells and #size-cells

These define the format of `reg` properties in child nodes:

```devicetree
/* 32-bit addresses, 32-bit sizes */
#address-cells = <1>;
#size-cells = <1>;
child { reg = <0x1000 0x100>; };  /* addr=0x1000, size=0x100 */

/* 64-bit addresses, 64-bit sizes */
#address-cells = <2>;
#size-cells = <2>;
child { reg = <0x0 0x80000000 0x0 0x1000>; };  /* addr=0x80000000, size=0x1000 */

/* 32-bit addresses, no size (e.g., I2C) */
#address-cells = <1>;
#size-cells = <0>;
child { reg = <0x48>; };  /* I2C address 0x48 */
```

## The ranges Property

`ranges` translates addresses from child to parent address space.

### Format
```
ranges = <child_addr parent_addr size> [, ...];
```

### Empty ranges (Identity Mapping)
```devicetree
soc {
    ranges;  /* Empty = identity mapping (1:1) */
    /* Child addresses = parent addresses */
};
```

### Simple Translation
```devicetree
soc@40000000 {
    #address-cells = <1>;
    #size-cells = <1>;
    ranges = <0x0 0x40000000 0x10000000>;
    /*
     * Child address 0x0 maps to parent 0x40000000
     * Translation window is 256MB (0x10000000)
     */
};
```

### Multiple Ranges
```devicetree
pcie@10000000 {
    #address-cells = <3>;  /* PCI uses 3 cells */
    #size-cells = <2>;
    ranges = <0x02000000 0x0 0x10000000   /* 32-bit memory */
              0x0 0x10000000
              0x0 0x01000000>,
             <0x01000000 0x0 0x00000000   /* I/O space */
              0x0 0x03000000
              0x0 0x00010000>;
};
```

## Common Patterns

### SoC with Peripherals
```devicetree
/ {
    #address-cells = <1>;
    #size-cells = <1>;

    soc {
        compatible = "simple-bus";
        #address-cells = <1>;
        #size-cells = <1>;
        ranges;  /* Identity - SoC addresses = CPU addresses */

        peripheral@40000000 {
            reg = <0x40000000 0x1000>;
        };
    };
};
```

### Memory Regions
```devicetree
/ {
    #address-cells = <1>;
    #size-cells = <1>;

    sram0: memory@20000000 {
        compatible = "mmio-sram";
        reg = <0x20000000 0x40000>;  /* 256KB SRAM */
    };

    flash0: flash@8000000 {
        compatible = "soc-nv-flash";
        reg = <0x08000000 0x100000>;  /* 1MB Flash */
    };
};
```

### External Memory Bus
```devicetree
external-bus@50000000 {
    compatible = "simple-bus";
    #address-cells = <2>;  /* chip-select + offset */
    #size-cells = <1>;
    ranges = <0 0 0x50000000 0x1000000>,  /* CS0 -> 0x50000000 */
             <1 0 0x51000000 0x1000000>,  /* CS1 -> 0x51000000 */
             <2 0 0x52000000 0x1000000>;  /* CS2 -> 0x52000000 */

    flash@0,0 {
        reg = <0 0x0 0x100000>;  /* CS0, offset 0, 1MB */
    };

    ethernet@1,0 {
        reg = <1 0x0 0x1000>;  /* CS1, offset 0, 4KB */
    };
};
```

### I2C Bus (No Size)
```devicetree
i2c0: i2c@40003000 {
    compatible = "vendor,i2c";
    reg = <0x40003000 0x1000>;
    #address-cells = <1>;
    #size-cells = <0>;  /* I2C has no size concept */

    sensor@48 {
        compatible = "ti,tmp102";
        reg = <0x48>;  /* Just the I2C address */
    };

    eeprom@50 {
        compatible = "atmel,24c32";
        reg = <0x50>;
    };
};
```

### SPI Bus (Chip Select)
```devicetree
spi0: spi@40004000 {
    compatible = "vendor,spi";
    reg = <0x40004000 0x1000>;
    #address-cells = <1>;
    #size-cells = <0>;

    flash@0 {
        compatible = "jedec,spi-nor";
        reg = <0>;  /* Chip select 0 */
        spi-max-frequency = <40000000>;
    };

    display@1 {
        compatible = "sitronix,st7789v";
        reg = <1>;  /* Chip select 1 */
    };
};
```

## Zephyr-Specific Patterns

### Chosen Memory Regions
```devicetree
/ {
    chosen {
        zephyr,sram = &sram0;
        zephyr,flash = &flash0;
        zephyr,code-partition = &slot0_partition;
    };
};
```

### Flash Partitions
```devicetree
&flash0 {
    partitions {
        compatible = "fixed-partitions";
        #address-cells = <1>;
        #size-cells = <1>;

        boot_partition: partition@0 {
            label = "mcuboot";
            reg = <0x0 0x10000>;
        };
        slot0_partition: partition@10000 {
            label = "image-0";
            reg = <0x10000 0x70000>;
        };
        storage_partition: partition@80000 {
            label = "storage";
            reg = <0x80000 0x80000>;
        };
    };
};
```

## C API

```c
/* Get register address and size */
#define MY_NODE DT_NODELABEL(uart0)

#define MY_REG_ADDR DT_REG_ADDR(MY_NODE)     /* Base address */
#define MY_REG_SIZE DT_REG_SIZE(MY_NODE)     /* Size */

/* Multiple register blocks */
DT_REG_ADDR_BY_IDX(node_id, idx)  /* Nth register address */
DT_REG_SIZE_BY_IDX(node_id, idx)  /* Nth register size */
DT_NUM_REGS(node_id)              /* Number of reg entries */

/* Named registers (if reg-names exists) */
DT_REG_ADDR_BY_NAME(node_id, name)
DT_REG_SIZE_BY_NAME(node_id, name)
```

## Tips

1. **Check parent's cells** — `reg` format depends on parent's `#address-cells` and `#size-cells`
2. **Empty ranges** — Use `ranges;` for identity mapping (most common in Zephyr)
3. **Bus nodes** — Buses like I2C/SPI use `#size-cells = <0>`
4. **Final addresses** — Check `build/zephyr/zephyr.dts` to see resolved addresses
5. **64-bit systems** — Use `#address-cells = <2>` for addresses > 4GB
