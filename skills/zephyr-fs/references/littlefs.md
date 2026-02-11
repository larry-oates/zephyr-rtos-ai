# LittleFS Reference

## Overview

LittleFS is a power-loss resilient filesystem designed for embedded systems with flash storage. It provides wear leveling and handles power failures gracefully.

## When to Use

- Internal MCU flash storage
- External SPI/QSPI flash
- Need power-loss resilience
- Need wear leveling
- Don't need PC compatibility

## Kconfig Options

```kconfig
# Required
CONFIG_FILE_SYSTEM=y
CONFIG_FILE_SYSTEM_LITTLEFS=y

# Flash support (choose based on hardware)
CONFIG_FLASH=y
CONFIG_FLASH_MAP=y
CONFIG_FLASH_PAGE_LAYOUT=y  # For explicit erase flash

# Performance tuning
CONFIG_FS_LITTLEFS_NUM_FILES=4       # Max concurrent open files
CONFIG_FS_LITTLEFS_NUM_DIRS=4        # Max concurrent open directories
CONFIG_FS_LITTLEFS_READ_SIZE=16      # Min read size
CONFIG_FS_LITTLEFS_PROG_SIZE=16      # Min program size
CONFIG_FS_LITTLEFS_CACHE_SIZE=64     # Cache size (RAM per file)
CONFIG_FS_LITTLEFS_LOOKAHEAD_SIZE=32 # Lookahead buffer
CONFIG_FS_LITTLEFS_BLOCK_CYCLES=512  # Erase cycles before moving data

# Block device support (for SD cards via LittleFS)
CONFIG_FS_LITTLEFS_BLK_DEV=y

# Disk version compatibility
CONFIG_FS_LITTLEFS_DISK_VERSION=y
```

## Mount Point Setup

### Option 1: Manual Mount (Programmatic)

```c
#include <zephyr/fs/fs.h>
#include <zephyr/fs/littlefs.h>
#include <zephyr/storage/flash_map.h>

/* Declare LittleFS config with default Kconfig values */
FS_LITTLEFS_DECLARE_DEFAULT_CONFIG(storage);

static struct fs_mount_t lfs_mount = {
    .type = FS_LITTLEFS,
    .fs_data = &storage,
    .storage_dev = (void *)FIXED_PARTITION_ID(storage_partition),
    .mnt_point = "/lfs",
};

int init_filesystem(void)
{
    int rc = fs_mount(&lfs_mount);
    if (rc < 0) {
        printk("Mount failed: %d\n", rc);
        /* Try formatting */
        rc = fs_mkfs(FS_LITTLEFS, (uintptr_t)lfs_mount.storage_dev, NULL, 0);
        if (rc == 0) {
            rc = fs_mount(&lfs_mount);
        }
    }
    return rc;
}
```

### Option 2: Devicetree Fstab (Automount)

```dts
/* In board overlay or app overlay */
/ {
    fstab {
        compatible = "zephyr,fstab";
        lfs1: lfs1 {
            compatible = "zephyr,fstab,littlefs";
            mount-point = "/lfs";
            partition = <&storage_partition>;
            automount;
            read-size = <16>;
            prog-size = <16>;
            cache-size = <64>;
            lookahead-size = <32>;
            block-cycles = <512>;
        };
    };
};

&flash0 {
    partitions {
        compatible = "fixed-partitions";
        #address-cells = <1>;
        #size-cells = <1>;

        storage_partition: partition@70000 {
            label = "storage";
            reg = <0x70000 0x10000>;  /* 64KB */
        };
    };
};
```

Access in code:

```c
#include <zephyr/fs/fs.h>

#define PARTITION_NODE DT_NODELABEL(lfs1)

#if DT_NODE_EXISTS(PARTITION_NODE)
FS_FSTAB_DECLARE_ENTRY(PARTITION_NODE);

void use_filesystem(void)
{
    struct fs_mount_t *mp = &FS_FSTAB_ENTRY(PARTITION_NODE);
    /* Already mounted if automount is set */

    struct fs_file_t file;
    fs_file_t_init(&file);
    fs_open(&file, "/lfs/test.txt", FS_O_CREATE | FS_O_WRITE);
    fs_write(&file, "data", 4);
    fs_close(&file);
}
#endif
```

### Option 3: Custom Configuration

```c
/* Custom cache sizes different from Kconfig defaults */
FS_LITTLEFS_DECLARE_CUSTOM_CONFIG(my_lfs,
    4,      /* alignment */
    16,     /* read_sz */
    16,     /* prog_sz */
    256,    /* cache_sz - larger cache for performance */
    64      /* lookahead_sz */
);

static struct fs_mount_t custom_mount = {
    .type = FS_LITTLEFS,
    .fs_data = &my_lfs,
    .storage_dev = (void *)FIXED_PARTITION_ID(storage_partition),
    .mnt_point = "/custom",
};
```

## Complete Example

```c
#include <zephyr/kernel.h>
#include <zephyr/fs/fs.h>
#include <zephyr/fs/littlefs.h>
#include <zephyr/storage/flash_map.h>

FS_LITTLEFS_DECLARE_DEFAULT_CONFIG(storage);

static struct fs_mount_t lfs_mnt = {
    .type = FS_LITTLEFS,
    .fs_data = &storage,
    .storage_dev = (void *)FIXED_PARTITION_ID(storage_partition),
    .mnt_point = "/lfs",
};

int main(void)
{
    struct fs_file_t file;
    struct fs_statvfs stat;
    uint32_t boot_count = 0;
    char path[64];
    int rc;

    /* Mount filesystem */
    rc = fs_mount(&lfs_mnt);
    if (rc != 0) {
        printk("Mount error: %d, formatting...\n", rc);
        fs_mkfs(FS_LITTLEFS, (uintptr_t)lfs_mnt.storage_dev, NULL, 0);
        rc = fs_mount(&lfs_mnt);
    }

    /* Check space */
    fs_statvfs(lfs_mnt.mnt_point, &stat);
    printk("FS: %lu/%lu blocks free\n", stat.f_bfree, stat.f_blocks);

    /* Read/update boot counter */
    snprintf(path, sizeof(path), "%s/boot_count", lfs_mnt.mnt_point);

    fs_file_t_init(&file);
    rc = fs_open(&file, path, FS_O_CREATE | FS_O_RDWR);
    if (rc == 0) {
        fs_read(&file, &boot_count, sizeof(boot_count));
        boot_count++;
        fs_seek(&file, 0, FS_SEEK_SET);
        fs_write(&file, &boot_count, sizeof(boot_count));
        fs_close(&file);
    }

    printk("Boot count: %u\n", boot_count);
    return 0;
}
```

## Sizing Considerations

### RAM Usage

Per-file cache memory:
- `cache_size` bytes per open file
- Plus `lookahead_size` bytes global
- Plus internal structures (~100 bytes)

Formula: `RAM ≈ NUM_FILES × cache_size + lookahead_size + overhead`

### Flash Usage

- Metadata overhead: ~4 bytes per 128 bytes of data
- Block size should match flash erase size
- Minimum 2 blocks required

## Troubleshooting

### Mount Fails with -ENODEV

Flash device not ready or partition not found:
```c
const struct device *flash = FIXED_PARTITION_DEVICE(storage_partition);
if (!device_is_ready(flash)) {
    printk("Flash not ready\n");
}
```

### Mount Fails with -ENOENT

Filesystem not formatted. Format first:
```c
fs_mkfs(FS_LITTLEFS, (uintptr_t)FIXED_PARTITION_ID(storage_partition), NULL, 0);
```

### Writes Fail

- Check `fs_statvfs()` for free space
- Verify partition is large enough
- Check flash write protection
