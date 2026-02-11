# ZMS (Zephyr Memory Storage) Reference

## Overview

ZMS is a key-value storage system designed for all types of non-volatile storage, including classical NOR flash and newer technologies like RRAM/MRAM that don't require erase operations.

**Key advantages over NVS:**
- Single-write sector invalidation (256x faster on RRAM/MRAM)
- 32-bit or 64-bit IDs (vs NVS 16-bit)
- Small data optimization (data stored in ATE if <=8 bytes)
- Built-in data CRC in ATE structure
- 64-bit address space for large partitions

## API Reference

### Header
```c
#include <zephyr/fs/zms.h>
```

### Data Structure

```c
struct zms_fs {
    off_t offset;                    // Flash offset
    uint32_t sector_size;            // Multiple of erase-block-size
    uint32_t sector_count;           // Minimum 2
    const struct device *flash_device;
    // Internal fields (initialized by zms_mount)
    uint64_t ate_wra;                // ATE write address (64-bit)
    uint64_t data_wra;               // Data write address (64-bit)
    uint8_t sector_cycle;            // Current cycle counter
    bool ready;
    struct k_mutex zms_lock;
    size_t ate_size;                 // ATE size (16 bytes)
};
```

### ID Type

```c
// Depends on CONFIG_ZMS_ID_64BIT
#if CONFIG_ZMS_ID_64BIT
typedef uint64_t zms_id_t;  // 64-bit IDs
#else
typedef uint32_t zms_id_t;  // 32-bit IDs (default)
#endif
```

### Functions

| Function | Description | Return |
|----------|-------------|--------|
| `zms_mount(fs)` | Initialize and mount ZMS | 0, -ENOTSUP, -EPROTONOSUPPORT, -EINVAL, -ENXIO, -EIO |
| `zms_clear(fs)` | Erase all data (must remount after) | 0, -EACCES, -ENXIO, -EIO, -EINVAL |
| `zms_write(fs, id, data, len)` | Write entry (max 64KB, len=0 deletes) | Bytes written, 0 if unchanged, -errno |
| `zms_read(fs, id, data, len)` | Read latest entry | Bytes read, -ENOENT if not found |
| `zms_read_hist(fs, id, data, len, cnt)` | Read historical entry | Bytes read |
| `zms_delete(fs, id)` | Delete entry | 0 on success |
| `zms_get_data_length(fs, id)` | Get stored data length | Length, -ENOENT if not found |
| `zms_calc_free_space(fs)` | Calculate free bytes (slow) | Free bytes |
| `zms_active_sector_free_space(fs)` | Free space in current sector | Bytes |
| `zms_sector_use_next(fs)` | Force sector switch (use sparingly) | 0 on success |

### Key Differences from NVS API

| Feature | NVS | ZMS |
|---------|-----|-----|
| ID type | `uint16_t` | `zms_id_t` (32 or 64-bit) |
| Max write size | Unlimited | 64 KB |
| Get data length | Not available | `zms_get_data_length()` |
| Remount after clear | Not required | Required |

## Kconfig Options

### Core
```kconfig
CONFIG_ZMS=y                      # Enable ZMS
```

### ID Size
```kconfig
CONFIG_ZMS_ID_64BIT=y             # Use 64-bit IDs (default: 32-bit)
```

**Warning**: Changing ID size makes existing storage incompatible.

### Performance
```kconfig
CONFIG_ZMS_LOOKUP_CACHE=y         # Enable lookup cache
CONFIG_ZMS_LOOKUP_CACHE_SIZE=128  # Cache entries (8 bytes RAM each)
CONFIG_ZMS_LOOKUP_CACHE_FOR_SETTINGS=y  # Optimized for Settings backend
CONFIG_ZMS_NO_DOUBLE_WRITE=y      # Avoid rewriting same data (slower writes)
```

### Advanced
```kconfig
CONFIG_ZMS_DATA_CRC=y             # Extra data CRC (not available with 64-bit IDs)
CONFIG_ZMS_CUSTOMIZE_BLOCK_SIZE=y # Custom internal buffer
CONFIG_ZMS_CUSTOM_BLOCK_SIZE=32   # Buffer size (default 32)
```

**Dependencies:**
```kconfig
CONFIG_FLASH=y
CONFIG_FLASH_MAP=y
```

## ATE (Allocation Table Entry) Format

### 32-bit ID Format (Default)

16-byte entry:
```
+-----+----------+-----+-----------+-------------+---------------+
| 0   | 1        | 2-3 | 4-7       | 8-11        | 12-15         |
+-----+----------+-----+-----------+-------------+---------------+
| crc8| cycle_cnt| len | id (32b)  | offset/data | data_crc/meta |
+-----+----------+-----+-----------+-------------+---------------+
```

- Small data (<=8 bytes): stored directly in bytes 8-15
- Large data: offset in bytes 8-11, CRC in 12-15

### 64-bit ID Format

16-byte entry:
```
+-----+----------+-----+-------------------------+-------------------+
| 0   | 1        | 2-3 | 4-11                    | 12-15             |
+-----+----------+-----+-------------------------+-------------------+
| crc8| cycle_cnt| len | id (64-bit)             | offset/data/meta  |
+-----+----------+-----+-------------------------+-------------------+
```

- Small data (<=4 bytes): stored directly in bytes 12-15
- Large data: offset in bytes 12-15

## Complete Example

```c
#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/flash.h>
#include <zephyr/storage/flash_map.h>
#include <zephyr/fs/zms.h>

static struct zms_fs fs;

#define STORAGE_PARTITION storage_partition
#define CONFIG_ID   1
#define COUNTER_ID  2
#define SENSOR_ID   3

int main(void)
{
    int rc;
    struct flash_pages_info info;
    uint32_t counter = 0;

    /* Setup ZMS */
    fs.flash_device = FIXED_PARTITION_DEVICE(STORAGE_PARTITION);
    if (!device_is_ready(fs.flash_device)) {
        printk("Flash device not ready\n");
        return -1;
    }

    fs.offset = FIXED_PARTITION_OFFSET(STORAGE_PARTITION);
    rc = flash_get_page_info_by_offs(fs.flash_device, fs.offset, &info);
    if (rc) {
        printk("Unable to get page info\n");
        return -1;
    }

    fs.sector_size = info.size;
    fs.sector_count = 4;  // Recommend 2x data size for optimal GC

    rc = zms_mount(&fs);
    if (rc) {
        printk("ZMS mount failed: %d\n", rc);
        return -1;
    }

    /* Check data length before reading */
    ssize_t len = zms_get_data_length(&fs, CONFIG_ID);
    if (len > 0) {
        char *config = k_malloc(len);
        zms_read(&fs, CONFIG_ID, config, len);
        printk("Config: %s\n", config);
        k_free(config);
    }

    /* Read, increment, and save counter */
    zms_read(&fs, COUNTER_ID, &counter, sizeof(counter));
    counter++;
    zms_write(&fs, COUNTER_ID, &counter, sizeof(counter));

    printk("Counter: %u\n", counter);
    return 0;
}
```

## Flash Wear and Lifetime

### Sector Layout

ZMS always keeps one sector empty for garbage collection:
- 4 sectors configured = 3 usable for data
- Header overhead: 80 bytes per sector (5 ATEs)

### Available Space Calculation

**Small data (<=8 bytes):**
```
Space = ((SECTOR_COUNT - 1) * (SECTOR_SIZE - 80) * 8) / 16
```

**Large data:**
```
Space = ((SECTOR_COUNT - 1) * (SECTOR_SIZE - 80)) / (DATA_SIZE + 16)
```

### Lifetime Formula

```
Lifetime (min) = (SECTOR_SIZE - 80) * SECTOR_COUNT * MAX_WRITES / (EFFECTIVE_SIZE * WRITES_PER_MIN)
```

Where `EFFECTIVE_SIZE`:
- Small data: 16 bytes
- Large data: 16 + sizeof(data)

**Example**: 4-byte counter every minute, 4 sectors of 1024 bytes, 20,000 write cycles:
- Effective size: 16 bytes (stored in ATE)
- Sector effective space: 944 bytes
- Lifetime: (944 * 4 * 20,000) / (16 * 1) = 4,720,000 minutes (~9 years)

### Best Practices

1. **Partition size**: 2x expected data size for optimal GC
2. **Sector size**: Large enough for max single entry
3. **Small data**: Keep values <=8 bytes when possible (stored in ATE)
4. **Settings paths**: Use <=8 byte path names for ZMS backend optimization

## Triggering Garbage Collection

For real-time applications needing predictable write latency:

```c
/* Check remaining space in current sector */
ssize_t free = zms_active_sector_free_space(&fs);

/* If running low, trigger GC proactively */
if (free < MINIMUM_REQUIRED) {
    zms_sector_use_next(&fs);  // Triggers GC on next sector
}
```

## Troubleshooting

### Mount Fails with -ENOTSUP or -EPROTONOSUPPORT
- Storage was initialized with different ZMS version or ATE format
- Solution: Erase partition and reinitialize

### Data CRC Errors After Enabling CONFIG_ZMS_DATA_CRC
- CRC feature change invalidates existing data
- Solution: Erase and reinitialize storage

### Changing Between 32-bit and 64-bit IDs
- Incompatible ATE formats
- Solution: Erase and reinitialize storage

### Slow Writes with CONFIG_ZMS_NO_DOUBLE_WRITE
- Expected behavior; searches entire storage before writing
- Only enable when write cycles are critical concern
