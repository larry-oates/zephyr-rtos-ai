# FAT Filesystem Reference

## Overview

FAT (File Allocation Table) filesystem using ELM FatFs library. Provides PC compatibility for removable media like SD cards and USB drives.

## When to Use

- SD cards
- USB mass storage
- Need to exchange files with PC/Mac/Linux
- Removable media
- Don't need power-loss resilience

## Kconfig Options

```kconfig
# Required
CONFIG_FILE_SYSTEM=y
CONFIG_FAT_FILESYSTEM_ELM=y
CONFIG_DISK_ACCESS=y         # Auto-selected

# Long file names (recommended)
CONFIG_FS_FATFS_LFN=y
CONFIG_FS_FATFS_MAX_LFN=255

# LFN memory mode (choose one)
CONFIG_FS_FATFS_LFN_MODE_BSS=y    # Static buffer (not thread-safe)
CONFIG_FS_FATFS_LFN_MODE_STACK=y  # Stack buffer (thread-safe)
CONFIG_FS_FATFS_LFN_MODE_HEAP=y   # Heap buffer (thread-safe)

# exFAT support (for >32GB)
CONFIG_FS_FATFS_EXFAT=y

# Formatting support
CONFIG_FS_FATFS_MKFS=y
CONFIG_FS_FATFS_MOUNT_MKFS=y  # Auto-format on failed mount

# File/directory limits
CONFIG_FS_FATFS_NUM_FILES=4
CONFIG_FS_FATFS_NUM_DIRS=4

# Sector size (match your hardware)
CONFIG_FS_FATFS_MAX_SS=512
CONFIG_FS_FATFS_MIN_SS=512

# Code page (character set)
CONFIG_FS_FATFS_CODEPAGE=437  # US English

# Thread safety
CONFIG_FS_FATFS_REENTRANT=y

# Read-only (reduces code size)
CONFIG_FS_FATFS_READ_ONLY=y
```

## Mount Points

FAT FS has restricted mount point names. Valid options:

- `/RAM:`, `/NAND:`, `/CF:`, `/SD:`, `/SD2:`
- `/USB:`, `/USB2:`, `/USB3:`
- Single digits: `/0:`, `/1:`, `/2:`, etc.

Or use `CONFIG_FS_FATFS_CUSTOM_MOUNT_POINTS` for custom names.

## SD Card Setup

### With SDHC/SDMMC Controller

```c
#include <zephyr/fs/fs.h>
#include <zephyr/storage/disk_access.h>
#include <ff.h>

static FATFS fat_fs;
static struct fs_mount_t mount_point = {
    .type = FS_FATFS,
    .fs_data = &fat_fs,
    .mnt_point = "/SD:",
};

int mount_sd_card(void)
{
    static const char *disk_name = "SD";
    int rc;

    /* Initialize disk (optional - mount does this too) */
    rc = disk_access_init(disk_name);
    if (rc != 0) {
        printk("Disk init failed: %d\n", rc);
        return rc;
    }

    /* Mount filesystem */
    rc = fs_mount(&mount_point);
    if (rc != 0) {
        printk("Mount failed: %d\n", rc);
        return rc;
    }

    printk("SD card mounted at %s\n", mount_point.mnt_point);
    return 0;
}
```

### With SPI SD Card

Add to prj.conf:
```kconfig
CONFIG_SPI=y
CONFIG_DISK_DRIVER_SDMMC=y
CONFIG_SDMMC_STACK=y
CONFIG_SDHC=y
```

Devicetree overlay:
```dts
&spi1 {
    status = "okay";
    cs-gpios = <&gpio0 4 GPIO_ACTIVE_LOW>;

    sdhc0: sdhc@0 {
        compatible = "zephyr,sdhc-spi-slot";
        reg = <0>;
        spi-max-frequency = <25000000>;
        mmc {
            compatible = "zephyr,sdmmc-disk";
            disk-name = "SD";
        };
    };
};
```

## Complete Example

```c
#include <zephyr/kernel.h>
#include <zephyr/fs/fs.h>
#include <zephyr/storage/disk_access.h>
#include <ff.h>

#define DISK_NAME "SD"
#define MOUNT_POINT "/SD:"

static FATFS fat_fs;
static struct fs_mount_t mp = {
    .type = FS_FATFS,
    .fs_data = &fat_fs,
    .mnt_point = MOUNT_POINT,
};

static int list_directory(const char *path)
{
    struct fs_dir_t dir;
    struct fs_dirent entry;
    int rc;

    fs_dir_t_init(&dir);
    rc = fs_opendir(&dir, path);
    if (rc != 0) {
        return rc;
    }

    printk("Contents of %s:\n", path);
    while (fs_readdir(&dir, &entry) == 0 && entry.name[0] != 0) {
        if (entry.type == FS_DIR_ENTRY_DIR) {
            printk("  [DIR]  %s\n", entry.name);
        } else {
            printk("  [FILE] %s (%zu bytes)\n", entry.name, entry.size);
        }
    }

    fs_closedir(&dir);
    return 0;
}

int main(void)
{
    struct fs_file_t file;
    uint32_t block_count, block_size;
    int rc;

    /* Get disk info */
    disk_access_init(DISK_NAME);
    disk_access_ioctl(DISK_NAME, DISK_IOCTL_GET_SECTOR_COUNT, &block_count);
    disk_access_ioctl(DISK_NAME, DISK_IOCTL_GET_SECTOR_SIZE, &block_size);
    printk("SD Card: %u sectors of %u bytes = %u MB\n",
           block_count, block_size, (block_count * block_size) >> 20);

    /* Mount */
    rc = fs_mount(&mp);
    if (rc != 0) {
        printk("Mount failed: %d\n", rc);
        return 0;
    }

    /* List root */
    list_directory(MOUNT_POINT);

    /* Create a file */
    fs_file_t_init(&file);
    rc = fs_open(&file, MOUNT_POINT "/hello.txt", FS_O_CREATE | FS_O_WRITE);
    if (rc == 0) {
        fs_write(&file, "Hello from Zephyr!\n", 19);
        fs_close(&file);
        printk("Created hello.txt\n");
    }

    /* Unmount before removing card */
    fs_unmount(&mp);
    printk("Unmounted\n");

    return 0;
}
```

## Devicetree Fstab (Automount)

```dts
/ {
    fstab {
        compatible = "zephyr,fstab";
        fatfs: fatfs {
            compatible = "zephyr,fstab,fatfs";
            mount-point = "/SD:";
            disk-name = "SD";
            automount;
        };
    };
};
```

Enable in Kconfig:
```kconfig
CONFIG_FS_FATFS_FSTAB_AUTOMOUNT=y
```

## Multi-Partition Support

For multiple FAT partitions on one disk:

```kconfig
CONFIG_FS_FATFS_MULTI_PARTITION=y
```

Define `VolToPart[]` in your application:
```c
#include <ff.h>

/* Map logical drives to physical partitions */
PARTITION VolToPart[] = {
    {3, 1},  /* /0: = Physical drive 3, partition 1 */
    {3, 2},  /* /1: = Physical drive 3, partition 2 */
};
```

## Format SD Card

```c
#include <ff.h>

/* Format as FAT32 */
BYTE work_buf[512];
MKFS_PARM mkfs_opt = {
    .fmt = FM_FAT32,
    .n_fat = 2,      /* Number of FATs */
    .align = 0,      /* Auto-align */
    .n_root = 512,   /* Root directory entries */
    .au_size = 0,    /* Auto cluster size */
};

FRESULT res = f_mkfs("SD:", &mkfs_opt, work_buf, sizeof(work_buf));
```

Or using Zephyr VFS:
```c
fs_mkfs(FS_FATFS, (uintptr_t)"SD:", NULL, 0);
```

## Troubleshooting

### Mount Returns -ENOENT

SD card not detected:
- Check SPI/SDIO connections
- Verify CS GPIO configuration
- Try lower SPI frequency
- Check power supply (SD cards need stable 3.3V)

### Long File Names Not Working

Enable in Kconfig:
```kconfig
CONFIG_FS_FATFS_LFN=y
CONFIG_FS_FATFS_MAX_LFN=255
```

### Files Not Visible on PC

- Call `fs_sync()` before removing card
- Always `fs_unmount()` before removal
- Check that LFN is enabled for long names
