# NVS vs ZMS Comparison

## Feature Comparison

| Feature | NVS | ZMS |
|---------|-----|-----|
| **ID Size** | 16-bit (65,535 max) | 32-bit or 64-bit |
| **ATE Size** | 8 bytes | 16 bytes |
| **Max Write Size** | No limit | 64 KB |
| **Address Space** | 32-bit | 64-bit |
| **Small Data Optimization** | No | Yes (<=8 bytes stored in ATE) |
| **Built-in Data CRC** | Optional (adds 4 bytes) | In ATE (no extra space) |
| **Erase Optimization** | Standard flash erase | Single-write invalidation |
| **Cycle Counter** | Per-entry | Per-sector |
| **Get Data Length API** | No | Yes (`zms_get_data_length`) |
| **Since Zephyr Version** | 1.12 | 3.6 |

## When to Use Each

### Use NVS When

- Using **classical NOR flash** (most common MCUs)
- Need **proven, battle-tested** storage
- ID count is **under 65,535**
- Memory footprint is critical (smaller ATEs)
- Working with **existing NVS-based** codebase

### Use ZMS When

- Using **RRAM, MRAM**, or other non-erase memory
- Need **more than 65K unique IDs**
- Storing many **small values** (<=8 bytes) - they fit in ATE
- Need **built-in data integrity** without extra overhead
- Working with **large flash partitions** (>4GB address space)
- Starting a **new project** (recommended for new designs)

## Performance Comparison

### Write Performance

| Scenario | NVS | ZMS |
|----------|-----|-----|
| Small data (4 bytes) | 8 + 4 = 12 bytes | 16 bytes (in ATE) |
| Medium data (32 bytes) | 8 + 32 = 40 bytes | 16 + 32 = 48 bytes |
| Large data (1KB) | 8 + 1024 = 1032 bytes | 16 + 1024 = 1040 bytes |
| Sector erase (RRAM) | 256 writes | 1 write |

### Read Performance

Both have O(n) lookup without cache, O(1) with cache enabled.

```kconfig
# NVS cache
CONFIG_NVS_LOOKUP_CACHE=y
CONFIG_NVS_LOOKUP_CACHE_SIZE=128

# ZMS cache
CONFIG_ZMS_LOOKUP_CACHE=y
CONFIG_ZMS_LOOKUP_CACHE_SIZE=128  # Uses 8 bytes RAM each
```

## API Comparison

### Initialization

```c
// NVS
struct nvs_fs nvs;
nvs.flash_device = FIXED_PARTITION_DEVICE(storage_partition);
nvs.offset = FIXED_PARTITION_OFFSET(storage_partition);
nvs.sector_size = page_size;
nvs.sector_count = 3;
nvs_mount(&nvs);

// ZMS (identical pattern)
struct zms_fs zms;
zms.flash_device = FIXED_PARTITION_DEVICE(storage_partition);
zms.offset = FIXED_PARTITION_OFFSET(storage_partition);
zms.sector_size = page_size;
zms.sector_count = 4;  // Recommend 2x data size
zms_mount(&zms);
```

### Read/Write

```c
// NVS
nvs_write(&nvs, id, data, len);          // id is uint16_t
nvs_read(&nvs, id, buffer, len);
nvs_delete(&nvs, id);

// ZMS
zms_write(&zms, id, data, len);          // id is zms_id_t (32 or 64-bit)
zms_read(&zms, id, buffer, len);
zms_delete(&zms, id);
zms_get_data_length(&zms, id);           // ZMS-only API
```

### Clear Storage

```c
// NVS - can continue using after clear
nvs_clear(&nvs);
nvs_write(&nvs, 1, data, len);  // OK

// ZMS - MUST remount after clear
zms_clear(&zms);
zms_mount(&zms);                // Required!
zms_write(&zms, 1, data, len);
```

## Memory Overhead

### RAM Usage

| Component | NVS | ZMS |
|-----------|-----|-----|
| Base structure | ~32 bytes | ~48 bytes |
| Mutex | ~24 bytes | ~24 bytes |
| Cache (per entry) | 4 bytes | 8 bytes |
| **Typical (128 cache)** | ~568 bytes | ~1096 bytes |

### Flash Usage Per Entry

| Data Size | NVS | ZMS |
|-----------|-----|-----|
| 1-4 bytes | 12 bytes (+CRC: 16) | 16 bytes |
| 5-8 bytes | 16 bytes (+CRC: 20) | 16 bytes |
| 9-16 bytes | 24 bytes (+CRC: 28) | 32 bytes |
| 32 bytes | 40 bytes (+CRC: 44) | 48 bytes |
| 128 bytes | 136 bytes (+CRC: 140) | 144 bytes |

## Migration Considerations

### NVS to ZMS

1. Data format is **incompatible** - cannot mount NVS partition with ZMS
2. Must migrate data programmatically:
   ```c
   // Read from NVS
   nvs_read(&old_nvs, id, buffer, len);
   // Write to ZMS
   zms_write(&new_zms, id, buffer, len);
   ```
3. Or erase and reinitialize on first boot

### Settings Backend Migration

Settings subsystem abstracts the backend:
```kconfig
# Change backend in prj.conf
# FROM:
CONFIG_SETTINGS_NVS=y

# TO:
CONFIG_SETTINGS_ZMS=y
```

**Warning**: Existing settings data will be lost; device needs reprovisioning.

## Recommended Configurations

### Memory-Constrained Device (NVS)

```kconfig
CONFIG_FLASH=y
CONFIG_FLASH_PAGE_LAYOUT=y
CONFIG_FLASH_MAP=y
CONFIG_NVS=y
CONFIG_NVS_LOOKUP_CACHE=y
CONFIG_NVS_LOOKUP_CACHE_SIZE=64
```

### RRAM/MRAM Device (ZMS)

```kconfig
CONFIG_FLASH=y
CONFIG_FLASH_MAP=y
CONFIG_ZMS=y
CONFIG_ZMS_LOOKUP_CACHE=y
CONFIG_ZMS_LOOKUP_CACHE_SIZE=128
CONFIG_ZMS_NO_DOUBLE_WRITE=y  # Maximize cell lifespan
```

### High-Reliability (ZMS with CRC)

```kconfig
CONFIG_FLASH=y
CONFIG_FLASH_MAP=y
CONFIG_ZMS=y
CONFIG_ZMS_DATA_CRC=y  # Only with 32-bit IDs
CONFIG_ZMS_LOOKUP_CACHE=y
```

### Large ID Space (ZMS 64-bit)

```kconfig
CONFIG_FLASH=y
CONFIG_FLASH_MAP=y
CONFIG_ZMS=y
CONFIG_ZMS_ID_64BIT=y
CONFIG_ZMS_LOOKUP_CACHE=y
```

## Decision Flowchart

```
START
  │
  ├─ Using RRAM/MRAM? ─────────────────────────────► ZMS
  │
  ├─ Need >65K unique IDs? ────────────────────────► ZMS
  │
  ├─ Starting new project? ────────────────────────► ZMS (recommended)
  │
  ├─ Existing NVS codebase? ───────────────────────► NVS (unless migrating)
  │
  ├─ Extreme memory constraints? ──────────────────► NVS (smaller ATEs)
  │
  └─ Default / Unsure ─────────────────────────────► NVS (battle-tested)
```
