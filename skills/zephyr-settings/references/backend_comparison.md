# Settings Backend Comparison

This guide helps you choose the right storage backend for your Zephyr Settings implementation.

## Backend Comparison Table

| Backend | Best For | Flash Wear | Speed | Memory | Status |
|---------|----------|------------|-------|--------|--------|
| **NVS** | General purpose | Low | Fast | Low | **Recommended** (Zephyr 4.1+) |
| **ZMS** | Memory-optimized | Low | Fast | Lower | **Recommended** (Zephyr 4.1+) |
| **FCB** | Legacy systems | Medium | Medium | Medium | Legacy option |
| **File** | Filesystem available | Varies | Slow | High | Requires mounted FS |

> **As of Zephyr 4.1**: NVS and ZMS are the recommended backends for non-filesystem storage.

## When to Use Each Backend

### NVS (Non-Volatile Storage)
- **Use when**: General-purpose persistent storage on flash
- **Advantages**: Battle-tested, good wear leveling, widely used
- **Disadvantages**: Slightly higher memory than ZMS

### ZMS (Zephyr Memory Storage)
- **Use when**: Memory is constrained, need efficient storage
- **Advantages**: Lower memory footprint, hash-based lookups
- **Disadvantages**: Potential hash collisions (configurable)

### FCB (Flash Circular Buffer)
- **Use when**: Maintaining legacy code
- **Advantages**: Simple circular buffer design
- **Disadvantages**: Not recommended for new designs

### File Backend
- **Use when**: Filesystem is already mounted (LittleFS, FAT, etc.)
- **Advantages**: Human-readable storage, easy debugging
- **Disadvantages**: Slower, requires filesystem overhead

---

## Backend Configuration

### NVS Backend

```c
#include <zephyr/settings/settings.h>
```

**Kconfig (`prj.conf`):**
```
CONFIG_SETTINGS=y
CONFIG_SETTINGS_NVS=y
CONFIG_FLASH=y
CONFIG_FLASH_MAP=y
CONFIG_NVS=y

# Optional: Speed up lookups
CONFIG_NVS_LOOKUP_CACHE=y
CONFIG_NVS_LOOKUP_CACHE_SIZE=128
```

**Devicetree (optional, for non-default partition):**
```dts
/ {
    chosen {
        zephyr,settings-partition = &storage_partition;
    };
};

&flash0 {
    partitions {
        compatible = "fixed-partitions";
        #address-cells = <1>;
        #size-cells = <1>;

        storage_partition: partition@f0000 {
            label = "storage";
            reg = <0x000f0000 0x00010000>;
        };
    };
};
```

---

### ZMS Backend

```c
#include <zephyr/settings/settings.h>
```

**Kconfig (`prj.conf`):**
```
CONFIG_SETTINGS=y
CONFIG_SETTINGS_ZMS=y
CONFIG_FLASH=y
CONFIG_FLASH_MAP=y
CONFIG_ZMS=y

# Handle hash collisions (2^n possible collisions)
CONFIG_SETTINGS_ZMS_MAX_COLLISIONS_BITS=2
```

**Devicetree:** Same as NVS (uses `zephyr,settings-partition`).

---

### File Backend

```c
#include <zephyr/settings/settings.h>
#include <zephyr/fs/fs.h>
```

**Kconfig (`prj.conf`):**
```
CONFIG_SETTINGS=y
CONFIG_SETTINGS_FILE=y
CONFIG_FILE_SYSTEM=y
CONFIG_FILE_SYSTEM_LITTLEFS=y

# Optional: Custom path (default: /settings/run)
CONFIG_SETTINGS_FILE_PATH="/lfs/settings"
```

**Important**: Filesystem must be mounted BEFORE `settings_subsys_init()`:
```c
int main(void)
{
    /* 1. Mount filesystem first */
    fs_mount(&lfs_mnt);

    /* 2. Then initialize settings */
    settings_subsys_init();
    settings_load();
}
```

---

### FCB Backend (Legacy)

```c
#include <zephyr/settings/settings.h>
```

**Kconfig (`prj.conf`):**
```
CONFIG_SETTINGS=y
CONFIG_SETTINGS_FCB=y
CONFIG_FLASH=y
CONFIG_FCB=y
```

---

## Custom Backend Implementation

For specialized storage (e.g., external EEPROM, cloud sync):

**Kconfig:**
```
CONFIG_SETTINGS=y
CONFIG_SETTINGS_CUSTOM=y
```

**Implementation:**
```c
#include <zephyr/settings/settings.h>

static int my_backend_load(struct settings_store *cs,
                           const struct settings_load_arg *arg)
{
    /* Load from custom storage */
    /* Call arg->cb for each key-value pair found */
    return 0;
}

static int my_backend_save(struct settings_store *cs, const char *name,
                           const char *value, size_t val_len)
{
    /* Save to custom storage */
    return 0;
}

static struct settings_store_itf my_backend_itf = {
    .csi_load = my_backend_load,
    .csi_save = my_backend_save,
};

static struct settings_store my_backend_store = {
    .cs_itf = &my_backend_itf
};

void my_backend_init(void)
{
    /* Register as both read source and write destination */
    settings_dst_register(&my_backend_store);  /* Write target */
    settings_src_register(&my_backend_store);  /* Read source */
}
```

---

## Advanced Kconfig Options

### Settings Subsystem
```
CONFIG_SETTINGS=y                          # Enable settings
CONFIG_SETTINGS_RUNTIME=y                  # Enable runtime API
CONFIG_SETTINGS_DYNAMIC_HANDLERS=y         # Allow runtime handler registration
CONFIG_SETTINGS_LOG_LEVEL_DBG=y            # Debug logging
CONFIG_SETTINGS_ENCODE_LEN=y               # Encode data length for integrity
```

### NVS Backend Tuning
```
CONFIG_NVS=y
CONFIG_NVS_LOOKUP_CACHE=y                  # Speed up lookups
CONFIG_NVS_LOOKUP_CACHE_SIZE=128           # Cache size
```

### ZMS Backend Tuning
```
CONFIG_ZMS=y
CONFIG_SETTINGS_ZMS_MAX_COLLISIONS_BITS=2  # Collision handling (2^n)
```

---

## Decision Flowchart

```
Is filesystem already required?
├── YES → Use File Backend
└── NO → Is memory extremely constrained?
          ├── YES → Use ZMS
          └── NO → Use NVS (safest default)
```

## Migration Notes

- **FCB → NVS/ZMS**: Settings keys are compatible; only backend configuration changes
- **NVS → ZMS**: Direct migration possible; both use flash partitions
- **File → NVS/ZMS**: May require re-provisioning settings on first boot
