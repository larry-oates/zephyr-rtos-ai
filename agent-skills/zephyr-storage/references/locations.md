# Source Code and Documentation Locations

## Zephyr Repository Paths

All paths relative to Zephyr root (`zephyr/`).

### NVS

| Resource | Path |
|----------|------|
| Header | `include/zephyr/fs/nvs.h` |
| Implementation | `subsys/fs/nvs/nvs.c` |
| Private header | `subsys/fs/nvs/nvs_priv.h` |
| Kconfig | `subsys/fs/nvs/Kconfig` |
| Documentation | `doc/services/storage/nvs/nvs.rst` |
| Sample | `samples/subsys/nvs/` |
| Tests | `tests/subsys/fs/nvs/` |

### ZMS

| Resource | Path |
|----------|------|
| Header | `include/zephyr/fs/zms.h` |
| Implementation | `subsys/fs/zms/zms.c` |
| Private header | `subsys/fs/zms/zms_priv.h` |
| Kconfig | `subsys/fs/zms/Kconfig` |
| Documentation | `doc/services/storage/zms/zms.rst` |
| Tests | `tests/subsys/fs/zms/` |

### Settings Backend

| Resource | Path |
|----------|------|
| NVS backend header | `subsys/settings/include/settings/settings_nvs.h` |
| NVS backend impl | `subsys/settings/src/settings_nvs.c` |
| ZMS backend header | `subsys/settings/include/settings/settings_zms.h` |
| ZMS backend impl | `subsys/settings/src/settings_zms.c` |
| Settings Kconfig | `subsys/settings/Kconfig` |

### Flash Map

| Resource | Path |
|----------|------|
| Flash map header | `include/zephyr/storage/flash_map.h` |
| Flash driver header | `include/zephyr/drivers/flash.h` |

## Online Documentation

### Official Zephyr Docs

- NVS: https://docs.zephyrproject.org/latest/services/storage/nvs/nvs.html
- ZMS: https://docs.zephyrproject.org/latest/services/storage/zms/zms.html
- Settings: https://docs.zephyrproject.org/latest/services/settings/index.html
- Flash Map: https://docs.zephyrproject.org/latest/services/storage/flash_map/flash_map.html

### API Reference

- NVS API: https://docs.zephyrproject.org/latest/doxygen/html/group__nvs.html
- ZMS API: https://docs.zephyrproject.org/latest/doxygen/html/group__zms.html

## Sample Applications

### NVS Sample

Location: `samples/subsys/nvs/`

```
samples/subsys/nvs/
├── CMakeLists.txt
├── Kconfig
├── prj.conf
├── README.rst
├── sample.yaml
├── src/
│   └── main.c
└── boards/
    ├── nrf52840dk_nrf52840.overlay
    ├── nucleo_f429zi.overlay
    └── ...
```

Build and run:
```bash
west build -b <board> samples/subsys/nvs
west flash
```

### ZMS Sample

No dedicated sample as of Zephyr 3.6. Use NVS sample as template, replacing:
- `#include <zephyr/fs/nvs.h>` → `#include <zephyr/fs/zms.h>`
- `struct nvs_fs` → `struct zms_fs`
- `nvs_*` functions → `zms_*` functions
- `CONFIG_NVS=y` → `CONFIG_ZMS=y`

## Tests

### Running Tests

```bash
# NVS tests
west twister -T tests/subsys/fs/nvs/

# ZMS tests
west twister -T tests/subsys/fs/zms/

# Settings with NVS backend
west twister -T tests/subsys/settings/nvs/

# Settings with ZMS backend
west twister -T tests/subsys/settings/zms/
```

## Key Files to Reference

When implementing storage:

1. **API usage**: `samples/subsys/nvs/src/main.c`
2. **Board overlays**: `samples/subsys/nvs/boards/*.overlay`
3. **Kconfig options**: `subsys/fs/nvs/Kconfig` or `subsys/fs/zms/Kconfig`
4. **Error codes**: Check return values in `include/zephyr/fs/nvs.h` or `zms.h`

When debugging:

1. **Enable logging**: `CONFIG_NVS_LOG_LEVEL_DBG=y` or `CONFIG_ZMS_LOG_LEVEL_DBG=y`
2. **Check implementation**: `subsys/fs/nvs/nvs.c` or `subsys/fs/zms/zms.c`
