# NVS (Non-Volatile Storage) Reference

## Overview

NVS stores id-data pairs in flash using a FIFO-managed circular buffer. Flash is divided into sectors; elements are appended until a sector is full, then a new sector is prepared (erased) and valid data is copied.

- **ID**: 16-bit unsigned integer (0-65535)
- **Metadata**: 8 bytes per entry (id, offset, length, CRC)
- **Minimum sectors**: 2 (one always kept empty for garbage collection)

## API Reference

### Header
```c
#include <zephyr/fs/nvs.h>
```

### Data Structure

```c
struct nvs_fs {
    off_t offset;                    // Flash offset
    uint32_t sector_size;            // Must be multiple of erase-block-size
    uint16_t sector_count;           // Minimum 2
    const struct device *flash_device;
    // Internal fields (initialized by nvs_mount)
    uint32_t ate_wra;                // ATE write address
    uint32_t data_wra;               // Data write address
    bool ready;
    struct k_mutex nvs_lock;
};
```

### Functions

| Function | Description | Return |
|----------|-------------|--------|
| `nvs_mount(fs)` | Initialize and mount NVS | 0 on success, -errno on error |
| `nvs_clear(fs)` | Erase all data | 0 on success |
| `nvs_write(fs, id, data, len)` | Write entry (len=0 deletes) | Bytes written, 0 if unchanged, -errno |
| `nvs_read(fs, id, data, len)` | Read latest entry | Bytes read, -errno on error |
| `nvs_read_hist(fs, id, data, len, cnt)` | Read historical entry (cnt=0 is latest) | Bytes read |
| `nvs_delete(fs, id)` | Delete entry | 0 on success |
| `nvs_calc_free_space(fs)` | Calculate free bytes (slow) | Free bytes, -errno |
| `nvs_sector_max_data_size(fs)` | Free space in current sector | Bytes |
| `nvs_sector_use_next(fs)` | Force sector switch (use sparingly) | 0 on success |

### Write Behavior

- Writing with `len=0` is equivalent to `nvs_delete()`
- NVS checks if data is unchanged before writing; returns 0 if no write needed
- Each write consumes: 8 bytes metadata + data length (+ 4 bytes if `CONFIG_NVS_DATA_CRC`)

## Kconfig Options

```kconfig
CONFIG_NVS=y                      # Enable NVS
CONFIG_NVS_LOOKUP_CACHE=y         # Enable lookup cache (faster reads)
CONFIG_NVS_LOOKUP_CACHE_SIZE=128  # Cache entries (power of 2 recommended)
CONFIG_NVS_DATA_CRC=y             # CRC-32 on data (adds 4 bytes per entry)
CONFIG_NVS_INIT_BAD_MEMORY_REGION=y  # Auto-init corrupted regions
CONFIG_NVS_LOG_LEVEL_DBG=y        # Debug logging
```

**Dependencies:**
```kconfig
CONFIG_FLASH=y
CONFIG_FLASH_PAGE_LAYOUT=y
CONFIG_FLASH_MAP=y
```

## Complete Example

```c
#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/flash.h>
#include <zephyr/storage/flash_map.h>
#include <zephyr/fs/nvs.h>

static struct nvs_fs fs;

#define STORAGE_PARTITION storage_partition
#define ADDRESS_ID  1
#define COUNTER_ID  2

int main(void)
{
    int rc;
    struct flash_pages_info info;
    uint32_t counter = 0;
    char address[16];

    /* Setup NVS */
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
    fs.sector_count = 3;

    rc = nvs_mount(&fs);
    if (rc) {
        printk("NVS mount failed: %d\n", rc);
        return -1;
    }

    /* Read or initialize address */
    rc = nvs_read(&fs, ADDRESS_ID, address, sizeof(address));
    if (rc <= 0) {
        strcpy(address, "192.168.1.1");
        nvs_write(&fs, ADDRESS_ID, address, strlen(address) + 1);
    }

    /* Read, increment, and save counter */
    nvs_read(&fs, COUNTER_ID, &counter, sizeof(counter));
    counter++;
    nvs_write(&fs, COUNTER_ID, &counter, sizeof(counter));

    printk("Address: %s, Counter: %u\n", address, counter);
    return 0;
}
```

## Flash Wear Calculation

Expected device lifetime formula:

```
Lifetime (minutes) = (SECTOR_COUNT * SECTOR_SIZE * PAGE_ERASES) / (WRITES_PER_MIN * (DATA_SIZE + 8))
```

**Example**: 4-byte counter updated every minute, 2 sectors of 1024 bytes, 20,000 erase cycles:
- Storage per write: 4 + 8 = 12 bytes
- Writes per sector: 1024 / 12 = 85
- Time to fill both sectors: 85 * 2 = 170 minutes
- Lifetime: 170 * 20,000 = 3,400,000 minutes (~6.5 years)

**To extend lifetime:**
- Increase `SECTOR_COUNT`
- Increase `SECTOR_SIZE`
- Reduce write frequency
- Batch updates when possible

## Troubleshooting

### MPU Fault or -ETIMEDOUT

NVS using internal flash requires:
```kconfig
CONFIG_MPU_ALLOW_FLASH_WRITE=y
```

### Data Not Persisting

1. Check `nvs_mount()` return value
2. Verify partition exists in devicetree
3. Ensure `sector_size` is multiple of flash erase-block-size
4. Ensure `sector_size` is power of 2

### Slow Reads

Enable lookup cache:
```kconfig
CONFIG_NVS_LOOKUP_CACHE=y
CONFIG_NVS_LOOKUP_CACHE_SIZE=128
```

### Running Out of Space

- Increase partition size in devicetree
- Increase `sector_count`
- Delete unused entries with `nvs_delete()`
