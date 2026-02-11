# File System Source Locations

Quick reference for Zephyr file system source code, headers, and samples.

## Headers

| Component | Location |
|-----------|----------|
| VFS API | `zephyr/include/zephyr/fs/fs.h` |
| VFS interface | `zephyr/include/zephyr/fs/fs_interface.h` |
| LittleFS | `zephyr/include/zephyr/fs/littlefs.h` |
| FCB | `zephyr/include/zephyr/fs/fcb.h` |

## Implementation

| Component | Location |
|-----------|----------|
| VFS core | `zephyr/subsys/fs/` |
| LittleFS wrapper | `zephyr/subsys/fs/littlefs_fs.c` |
| FAT/FatFs wrapper | `zephyr/subsys/fs/fat_fs.c` |
| ext2 wrapper | `zephyr/subsys/fs/ext2/` |
| FCB | `zephyr/subsys/fs/fcb/` |
| Shell commands | `zephyr/subsys/fs/shell.c` |

## Kconfig

| Component | Location |
|-----------|----------|
| Main FS config | `zephyr/subsys/fs/Kconfig` |
| LittleFS config | `zephyr/subsys/fs/Kconfig.littlefs` |
| FAT/FatFs config | `zephyr/subsys/fs/Kconfig.fatfs` |
| ext2 config | `zephyr/subsys/fs/Kconfig.ext2` |
| FCB config | `zephyr/subsys/fs/fcb/Kconfig` |

## Samples

### LittleFS Sample

**Location:** `zephyr/samples/subsys/fs/littlefs/`

Demonstrates LittleFS on internal flash with fstab automount.

```bash
west build -b <board> samples/subsys/fs/littlefs
```

**Key files:**
- `src/main.c` - Boot counter, file I/O example
- `boards/*.overlay` - Board-specific flash partition configs

### FAT/Disk Sample

**Location:** `zephyr/samples/subsys/fs/fs_sample/`

Demonstrates FAT filesystem on SD card or disk.

```bash
west build -b <board> samples/subsys/fs/fs_sample
```

**Key files:**
- `src/main.c` - Disk access and FAT mount example
- `prj_ext.conf` - ext2 filesystem variant

### Format Sample

**Location:** `zephyr/samples/subsys/fs/format/`

Demonstrates programmatic filesystem formatting.

```bash
west build -b <board> samples/subsys/fs/format
```

### ext2 with Fstab Sample

**Location:** `zephyr/samples/subsys/fs/ext2_fstab/`

Demonstrates ext2 filesystem with devicetree fstab configuration.

```bash
west build -b <board> samples/subsys/fs/ext2_fstab
```

### VirtioFS Sample

**Location:** `zephyr/samples/subsys/fs/virtiofs/`

Demonstrates filesystem access via virtio (QEMU).

```bash
west build -b qemu_x86 samples/subsys/fs/virtiofs
```

## Tests

| Component | Location |
|-----------|----------|
| VFS tests | `zephyr/tests/subsys/fs/` |
| LittleFS tests | `zephyr/tests/subsys/fs/littlefs/` |
| FAT tests | `zephyr/tests/subsys/fs/fat_fs_api/` |
| FCB tests | `zephyr/tests/subsys/fs/fcb/` |
| ext2 tests | `zephyr/tests/subsys/fs/ext2/` |

## Documentation

| Topic | Location |
|-------|----------|
| File System guide | `zephyr/doc/services/file_system/` |
| API docs | `zephyr/doc/services/file_system/api/` |

## Third-Party Libraries

Zephyr wraps these external libraries:

| Library | Zephyr Location | Upstream |
|---------|-----------------|----------|
| LittleFS | `modules/fs/littlefs/` | github.com/littlefs-project/littlefs |
| FatFs | `modules/fs/fatfs/` | elm-chan.org/fsw/ff/ |

## Common Board Configurations

Many samples include board-specific configurations in `boards/` subdirectory:

```
samples/subsys/fs/littlefs/boards/
├── nrf52840dk_nrf52840_qspi.overlay    # QSPI flash
├── nrf52840dk_nrf52840_spi.overlay     # SPI flash
├── stm32f746g_disco.overlay            # STM32 internal flash
└── ...
```

These overlays typically define:
- Flash partition layout
- Storage partition for filesystem
- Fstab mount point configuration
