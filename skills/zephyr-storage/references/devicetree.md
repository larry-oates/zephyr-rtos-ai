# Devicetree Configuration for Storage

## Storage Partition Setup

Both NVS and ZMS use devicetree to define the flash partition for storage.

### Basic Partition Definition

```dts
&flash0 {
    partitions {
        compatible = "fixed-partitions";
        #address-cells = <1>;
        #size-cells = <1>;

        /* Application code */
        slot0_partition: partition@0 {
            label = "image-0";
            reg = <0x00000000 0x000e0000>;
        };

        /* Storage partition for NVS/ZMS */
        storage_partition: partition@e0000 {
            label = "storage";
            reg = <0x000e0000 0x00020000>;  /* 128KB */
        };
    };
};
```

### Using the Chosen Node

For Settings subsystem integration:

```dts
/ {
    chosen {
        zephyr,settings-partition = &storage_partition;
    };
};
```

## Partition Sizing Guidelines

### Minimum Requirements

| Requirement | NVS | ZMS |
|-------------|-----|-----|
| Minimum sectors | 2 | 2 |
| Sector size | >= flash erase block | >= flash erase block |
| Recommended sectors | 3+ | 4+ (2x data size) |

### Calculating Required Size

**NVS:**
```
Total size = SECTOR_COUNT * SECTOR_SIZE
Usable space ≈ (SECTOR_COUNT - 1) * (SECTOR_SIZE - overhead)
Overhead per entry = 8 bytes + data + (4 bytes if CRC enabled)
```

**ZMS:**
```
Total size = SECTOR_COUNT * SECTOR_SIZE
Usable space ≈ (SECTOR_COUNT - 1) * (SECTOR_SIZE - 80)
Overhead per entry = 16 bytes (+ data if > 8 bytes)
```

### Example Sizing

For 100 entries averaging 32 bytes each:

**NVS:**
- Per entry: 8 + 32 = 40 bytes
- Total data: 100 * 40 = 4,000 bytes
- With 3 sectors of 4KB: 2 * 4,096 = 8,192 bytes usable
- Sufficient

**ZMS:**
- Per entry: 16 + 32 = 48 bytes
- Total data: 100 * 48 = 4,800 bytes
- Recommended: 2x = 9,600 bytes
- With 4 sectors of 4KB: 3 * (4,096 - 80) = 12,048 bytes usable
- Sufficient with room for GC

## Board-Specific Overlays

### Creating a Board Overlay

Create `boards/<board>.overlay` in your application:

```dts
/* boards/nrf52840dk_nrf52840.overlay */

&flash0 {
    partitions {
        compatible = "fixed-partitions";
        #address-cells = <1>;
        #size-cells = <1>;

        storage_partition: partition@fc000 {
            label = "storage";
            reg = <0x000fc000 0x00004000>;  /* 16KB at end of flash */
        };
    };
};
```

### Common Board Examples

#### Nordic nRF52840 (1MB flash, 4KB pages)

```dts
storage_partition: partition@f8000 {
    label = "storage";
    reg = <0x000f8000 0x00008000>;  /* 32KB = 8 sectors */
};
```

#### STM32F4 (2KB pages typical)

```dts
storage_partition: partition@70000 {
    label = "storage";
    reg = <0x00070000 0x00010000>;  /* 64KB */
};
```

#### ESP32 (4KB pages)

```dts
storage_partition: partition@310000 {
    label = "storage";
    reg = <0x00310000 0x00006000>;  /* 24KB = 6 sectors */
};
```

## Accessing Partition in Code

### Using Flash Map Macros

```c
#include <zephyr/storage/flash_map.h>

#define STORAGE_PARTITION storage_partition
#define STORAGE_DEVICE    FIXED_PARTITION_DEVICE(STORAGE_PARTITION)
#define STORAGE_OFFSET    FIXED_PARTITION_OFFSET(STORAGE_PARTITION)
#define STORAGE_SIZE      FIXED_PARTITION_SIZE(STORAGE_PARTITION)
```

### Getting Flash Page Info

```c
#include <zephyr/drivers/flash.h>

struct flash_pages_info info;
int rc = flash_get_page_info_by_offs(fs.flash_device, fs.offset, &info);
if (rc == 0) {
    fs.sector_size = info.size;  /* Use actual page size */
}
```

## Multiple Storage Partitions

For separate NVS/ZMS instances:

```dts
&flash0 {
    partitions {
        /* Settings storage */
        settings_partition: partition@e0000 {
            label = "settings";
            reg = <0x000e0000 0x00010000>;
        };

        /* Application data storage */
        data_partition: partition@f0000 {
            label = "appdata";
            reg = <0x000f0000 0x00010000>;
        };
    };
};

/ {
    chosen {
        zephyr,settings-partition = &settings_partition;
    };
};
```

In code:

```c
static struct nvs_fs settings_fs;
static struct nvs_fs data_fs;

void init_storage(void)
{
    /* Settings partition */
    settings_fs.flash_device = FIXED_PARTITION_DEVICE(settings_partition);
    settings_fs.offset = FIXED_PARTITION_OFFSET(settings_partition);
    /* ... */
    nvs_mount(&settings_fs);

    /* Data partition */
    data_fs.flash_device = FIXED_PARTITION_DEVICE(data_partition);
    data_fs.offset = FIXED_PARTITION_OFFSET(data_partition);
    /* ... */
    nvs_mount(&data_fs);
}
```

## External Flash

### QSPI Flash Example

```dts
&qspi {
    status = "okay";

    mx25r64: mx25r6435f@0 {
        compatible = "nordic,qspi-nor";
        reg = <0>;
        /* ... flash properties ... */

        partitions {
            compatible = "fixed-partitions";
            #address-cells = <1>;
            #size-cells = <1>;

            storage_partition: partition@0 {
                label = "storage";
                reg = <0x00000000 0x00100000>;  /* 1MB */
            };
        };
    };
};
```

## Verifying Partition Setup

### At Runtime

```c
#include <zephyr/storage/flash_map.h>

void check_partition(void)
{
    const struct flash_area *fa;
    int rc = flash_area_open(FIXED_PARTITION_ID(storage_partition), &fa);
    if (rc == 0) {
        printk("Partition: offset=0x%lx, size=%u\n",
               (unsigned long)fa->fa_off, fa->fa_size);
        flash_area_close(fa);
    }
}
```

### Build-Time Check

Use `west build -t menuconfig` or check generated devicetree:

```bash
# View generated devicetree
cat build/zephyr/zephyr.dts

# Check partition table
west build -t partition_table  # If supported
```

## Common Issues

### Partition Overlaps

Ensure partitions don't overlap with:
- Bootloader
- Application slots (for DFU)
- Other storage areas

### Alignment Issues

- `reg` address must align to flash erase block
- Size should be multiple of erase block

### Partition Not Found

1. Check label matches code reference
2. Verify `compatible = "fixed-partitions"`
3. Ensure flash node is enabled (`status = "okay"`)
