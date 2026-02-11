# Flash Circular Buffer (FCB) Reference

## Overview

FCB provides a log-style storage mechanism optimized for flash. Data is appended to a circular buffer that automatically rotates through flash sectors, providing wear leveling and power-loss resilience.

## When to Use

- Logging/journaling data
- Sensor data history
- Event logs
- Append-only data patterns
- Need power-loss safety
- Need to minimize flash wear

## When NOT to Use

- Random access file storage → Use LittleFS
- PC-compatible files → Use FAT
- Key-value storage → Use NVS/ZMS (zephyr-storage skill)

## Kconfig Options

```kconfig
CONFIG_FCB=y
CONFIG_FLASH=y
CONFIG_FLASH_MAP=y
CONFIG_FLASH_PAGE_LAYOUT=y
CONFIG_CRC=y              # Auto-selected

# Optional: disable CRC for faster writes
CONFIG_FCB_ALLOW_FIXED_ENDMARKER=y
```

## Key Concepts

- **Sector**: Flash erase unit. FCB rotates through sectors.
- **Entry**: Single data record with length and optional CRC.
- **Scratch sector**: Reserved for garbage collection (configurable count).
- **Oldest/Active**: FCB tracks oldest and newest data positions.

## Data Structure

```c
#include <zephyr/fs/fcb.h>

struct fcb my_fcb = {
    .f_magic = 0x12345678,   /* Unique magic (not 0xFFFFFFFF) */
    .f_version = 1,          /* Data format version */
    .f_sector_cnt = 4,       /* Number of sectors */
    .f_scratch_cnt = 1,      /* Sectors to keep empty */
    .f_sectors = sectors,    /* Array of flash_sector structs */
};
```

## Basic Usage

### Initialization

```c
#include <zephyr/fs/fcb.h>
#include <zephyr/storage/flash_map.h>

#define FCB_FLASH_AREA_ID FIXED_PARTITION_ID(storage_partition)

static struct flash_sector sectors[4];
static struct fcb my_fcb;

int init_fcb(void)
{
    int rc;
    const struct flash_area *fa;
    uint32_t sector_cnt = ARRAY_SIZE(sectors);

    /* Get sector layout from flash area */
    rc = flash_area_open(FCB_FLASH_AREA_ID, &fa);
    if (rc) {
        return rc;
    }

    rc = flash_area_get_sectors(FCB_FLASH_AREA_ID, &sector_cnt, sectors);
    flash_area_close(fa);
    if (rc) {
        return rc;
    }

    /* Initialize FCB */
    my_fcb.f_magic = 0xABCD1234;
    my_fcb.f_version = 1;
    my_fcb.f_sector_cnt = sector_cnt;
    my_fcb.f_scratch_cnt = 1;
    my_fcb.f_sectors = sectors;

    rc = fcb_init(FCB_FLASH_AREA_ID, &my_fcb);
    if (rc) {
        /* Clear and retry if corrupted */
        fcb_clear(&my_fcb);
        rc = fcb_init(FCB_FLASH_AREA_ID, &my_fcb);
    }

    return rc;
}
```

### Writing Entries

```c
int write_log_entry(const void *data, uint16_t len)
{
    struct fcb_entry loc;
    int rc;

    /* Reserve space for entry */
    rc = fcb_append(&my_fcb, len, &loc);
    if (rc == -ENOSPC) {
        /* No space - rotate and retry */
        fcb_rotate(&my_fcb);
        rc = fcb_append(&my_fcb, len, &loc);
    }
    if (rc) {
        return rc;
    }

    /* Write data */
    rc = fcb_flash_write(&my_fcb, loc.fe_sector, loc.fe_data_off, data, len);
    if (rc) {
        return rc;
    }

    /* Finalize entry (writes length/CRC header) */
    rc = fcb_append_finish(&my_fcb, &loc);
    return rc;
}
```

### Reading Entries

```c
/* Callback for walking entries */
static int process_entry(struct fcb_entry_ctx *ctx, void *arg)
{
    uint8_t buf[256];
    int rc;

    /* Read entry data */
    rc = fcb_flash_read(&my_fcb, ctx->loc.fe_sector,
                        ctx->loc.fe_data_off, buf, ctx->loc.fe_data_len);
    if (rc == 0) {
        /* Process buf[0..fe_data_len-1] */
        printk("Entry: %u bytes\n", ctx->loc.fe_data_len);
    }

    return 0;  /* Return non-zero to stop walk */
}

/* Walk all entries (oldest to newest) */
void read_all_entries(void)
{
    fcb_walk(&my_fcb, NULL, process_entry, NULL);
}

/* Get specific entry by index from end */
int read_last_n_entry(uint8_t n, void *buf, size_t buf_len)
{
    struct fcb_entry loc;
    int rc;

    rc = fcb_offset_last_n(&my_fcb, n, &loc);
    if (rc) {
        return rc;
    }

    return fcb_flash_read(&my_fcb, loc.fe_sector, loc.fe_data_off,
                          buf, MIN(buf_len, loc.fe_data_len));
}
```

### Rotation and Cleanup

```c
/* Manual rotation (erase oldest sector) */
fcb_rotate(&my_fcb);

/* Check free sectors */
int free = fcb_free_sector_cnt(&my_fcb);

/* Clear all data */
fcb_clear(&my_fcb);

/* Check if empty */
if (fcb_is_empty(&my_fcb)) {
    printk("FCB is empty\n");
}
```

## Complete Example

```c
#include <zephyr/kernel.h>
#include <zephyr/fs/fcb.h>
#include <zephyr/storage/flash_map.h>

#define FCB_AREA_ID FIXED_PARTITION_ID(storage_partition)

static struct flash_sector sectors[4];
static struct fcb log_fcb;

struct log_entry {
    uint32_t timestamp;
    int16_t temperature;
    uint16_t humidity;
};

static int print_log(struct fcb_entry_ctx *ctx, void *arg)
{
    struct log_entry entry;

    if (ctx->loc.fe_data_len == sizeof(entry)) {
        fcb_flash_read(&log_fcb, ctx->loc.fe_sector,
                       ctx->loc.fe_data_off, &entry, sizeof(entry));
        printk("[%u] Temp: %d.%d C, Humidity: %u%%\n",
               entry.timestamp,
               entry.temperature / 10, entry.temperature % 10,
               entry.humidity);
    }
    return 0;
}

int main(void)
{
    uint32_t sector_cnt = ARRAY_SIZE(sectors);
    struct log_entry entry;
    struct fcb_entry loc;
    int rc;

    /* Initialize sectors */
    flash_area_get_sectors(FCB_AREA_ID, &sector_cnt, sectors);

    /* Configure FCB */
    log_fcb.f_magic = 0xLOG12345;
    log_fcb.f_version = 1;
    log_fcb.f_sector_cnt = sector_cnt;
    log_fcb.f_scratch_cnt = 1;
    log_fcb.f_sectors = sectors;

    /* Initialize */
    rc = fcb_init(FCB_AREA_ID, &log_fcb);
    if (rc) {
        printk("FCB init failed: %d, clearing...\n", rc);
        fcb_clear(&log_fcb);
        fcb_init(FCB_AREA_ID, &log_fcb);
    }

    /* Show existing entries */
    printk("Existing log entries:\n");
    fcb_walk(&log_fcb, NULL, print_log, NULL);

    /* Add new entry */
    entry.timestamp = k_uptime_get_32() / 1000;
    entry.temperature = 235;  /* 23.5 C */
    entry.humidity = 45;

    rc = fcb_append(&log_fcb, sizeof(entry), &loc);
    if (rc == -ENOSPC) {
        fcb_rotate(&log_fcb);
        rc = fcb_append(&log_fcb, sizeof(entry), &loc);
    }

    if (rc == 0) {
        fcb_flash_write(&log_fcb, loc.fe_sector, loc.fe_data_off,
                        &entry, sizeof(entry));
        fcb_append_finish(&log_fcb, &loc);
        printk("Added log entry\n");
    }

    printk("Free sectors: %d\n", fcb_free_sector_cnt(&log_fcb));

    return 0;
}
```

## API Reference

| Function | Description |
|----------|-------------|
| `fcb_init(area_id, fcb)` | Initialize FCB on flash area |
| `fcb_append(fcb, len, loc)` | Reserve space for new entry |
| `fcb_append_finish(fcb, loc)` | Finalize appended entry |
| `fcb_walk(fcb, sector, cb, arg)` | Walk entries (NULL sector = all) |
| `fcb_getnext(fcb, loc)` | Get next entry location |
| `fcb_rotate(fcb)` | Erase oldest sector |
| `fcb_clear(fcb)` | Erase all sectors |
| `fcb_is_empty(fcb)` | Check if FCB is empty |
| `fcb_free_sector_cnt(fcb)` | Count free sectors |
| `fcb_offset_last_n(fcb, n, loc)` | Get nth entry from end |
| `fcb_flash_read(fcb, sector, off, dst, len)` | Read from FCB flash |
| `fcb_flash_write(fcb, sector, off, src, len)` | Write to FCB flash |

## Sizing Considerations

- Maximum entry size: 16,383 bytes (`FCB_MAX_LEN`)
- Entry overhead: ~8 bytes per entry
- Reserve 1+ sectors for garbage collection (`f_scratch_cnt`)
- Total storage ≈ (sector_cnt - scratch_cnt) × sector_size

## Troubleshooting

### fcb_init Returns -ENOMEM

Sectors array too small or sector_cnt wrong:
```c
uint32_t sector_cnt = ARRAY_SIZE(sectors);
flash_area_get_sectors(FCB_AREA_ID, &sector_cnt, sectors);
```

### fcb_append Returns -ENOSPC

No space left. Rotate and retry:
```c
fcb_rotate(&fcb);
fcb_append(&fcb, len, &loc);
```

### Data Corruption After Power Loss

FCB is designed to handle this. If `fcb_init` fails:
```c
fcb_clear(&fcb);
fcb_init(area_id, &fcb);
```
