# Zephyr Kconfig Best Practices

## Table of Contents

1. [Defining vs. Configuring](#1-defining-vs-configuring)
2. [Naming Conventions](#2-naming-conventions)
3. [File Locations](#3-file-locations)
4. [Dependencies](#4-dependencies-depends-on-vs-select)
5. [Description Guidelines](#5-description-guidelines)
6. [Modules & Drivers](#6-modules--drivers)
7. [Overlay Configurations](#7-overlay-configurations)
8. [Anti-Patterns](#8-anti-patterns)

---

## 1. Defining vs. Configuring

| Action | File | Syntax |
|--------|------|--------|
| **Define** (create symbol) | `Kconfig` | `config MY_SYMBOL` |
| **Configure** (set value) | `prj.conf` | `CONFIG_MY_SYMBOL=y` |

**Key insight:** Kconfig files create options; prj.conf sets values for existing options.

---

## 2. Naming Conventions

### Prefix Rules

- In `Kconfig`: define as `MY_SYMBOL` (no prefix)
- In `prj.conf`: use `CONFIG_MY_SYMBOL=y` (with prefix)
- In C code: use `CONFIG_MY_SYMBOL`

### Namespacing

Use consistent prefixes to avoid collisions:

| Context | Prefix Pattern | Example |
|---------|---------------|---------|
| Driver | `<DRIVER_NAME>_` | `LIS2DH_TRIGGER` |
| Subsystem | `<SUBSYS>_` | `BT_L2CAP_MTU` |
| Application | `APP_` | `APP_MAX_USERS` |
| Board | `BOARD_` | `BOARD_HAS_USB` |
| SoC | `SOC_` | `SOC_FLASH_SIZE` |

---

## 3. File Locations

### Applications

| File | Purpose |
|------|---------|
| `prj.conf` | Main configuration |
| `boards/<board>.conf` | Board-specific overrides |
| `Kconfig` | App-specific symbol definitions |

### Modules / Drivers

| File | Purpose |
|------|---------|
| `Kconfig` | Symbol definitions |
| `zephyr/module.yml` | Module metadata |

**module.yml example:**
```yaml
build:
  cmake: .
  kconfig: Kconfig
```

### Subsystems

```
subsys/my_subsystem/
├── Kconfig           # Main subsystem Kconfig
├── Kconfig.feature_a # Optional: split large configs
└── CMakeLists.txt
```

---

## 4. Dependencies (`depends on` vs `select`)

### depends on (PREFERRED)

Use for hardware requirements or upstream subsystems.

```kconfig
config MY_DRIVER
    bool "My Driver"
    depends on SPI
    depends on GPIO
```

**Behavior:** Symbol invisible and disabled if dependency unmet.

### select (USE SPARINGLY)

Forces another symbol on. Bypasses dependency checking.

```kconfig
config MY_SUBSYSTEM
    bool "My Subsystem"
    select RING_BUFFER
    select POLL
```

**Risks:**
- Ignores `depends on` of selected symbol
- Can cause "unmet dependencies" warnings
- Hard to debug dependency chains

**When to use:** Only for strictly required, hidden implementation details.

### imply (PREFERRED over select)

Suggests a default, but user can override.

```kconfig
config MY_FEATURE
    bool "My Feature"
    imply LOG
    imply SENSOR
```

**Use when:** Dependency is "nice to have" but not strictly required.

### Decision Table

| Situation | Use |
|-----------|-----|
| Hardware requirement | `depends on` |
| Required internal detail | `select` |
| Optional enhancement | `imply` |
| User should decide | `depends on` |

---

## 5. Description Guidelines

### Prompt (visible in menuconfig)

Keep short and descriptive:
```kconfig
bool "Enable Foo Feature"
int "Maximum buffer size"
```

### Help Text

Indented, explains what and why:
```kconfig
config FOO_ENABLE
    bool "Enable Foo Feature"
    help
      Enables the Foo feature which provides XYZ functionality.
      Enable this if your application needs to do ABC.

      Requires approximately 2KB of RAM when enabled.
```

---

## 6. Modules & Drivers

### Directory Structure

```
my_module/
├── zephyr/
│   └── module.yml      # Required for Zephyr integration
├── Kconfig             # Symbol definitions
├── CMakeLists.txt      # Build rules
├── include/
│   └── my_module.h
└── src/
    └── my_module.c
```

### module.yml

```yaml
build:
  cmake: .
  kconfig: Kconfig
```

### Driver Kconfig Pattern

```kconfig
config MY_DRIVER
    bool "My Driver"
    default y
    depends on DT_HAS_VENDOR_MY_DEVICE_ENABLED
    select I2C if DT_ANY_INST_HAS_PROP_STATUS_OKAY(vendor_my_device_i2c)
    help
      Enable driver for Vendor My Device.

if MY_DRIVER

config MY_DRIVER_INIT_PRIORITY
    int "Init priority"
    default 80
    help
      Device driver initialization priority.

endif # MY_DRIVER
```

### Registering Module with West

In workspace `west.yml`:
```yaml
manifest:
  projects:
    - name: my_module
      path: modules/my_module
      url: https://github.com/...
```

Or add path to `ZEPHYR_EXTRA_MODULES` in CMake.

---

## 7. Overlay Configurations

### Board-Specific Overlays

```
my_app/
├── prj.conf                    # Base configuration
├── boards/
│   ├── nrf52840dk_nrf52840.conf  # nRF52840 DK specific
│   └── nucleo_f401re.conf        # Nucleo F401RE specific
```

### Build Type Overlays

```
my_app/
├── prj.conf              # Default
├── prj_debug.conf        # Debug build
└── prj_release.conf      # Release build
```

**Usage:**
```bash
west build -b nrf52840dk_nrf52840 -- -DCONF_FILE="prj_release.conf"
```

### Multiple Overlay Files

```bash
west build -- -DEXTRA_CONF_FILE="overlay1.conf;overlay2.conf"
```

---

## 8. Anti-Patterns

### DON'T: Overuse select

```kconfig
# BAD: Forces complex dependency chain
config MY_FEATURE
    select NETWORKING
    select WIFI
    select DNS_RESOLVER
```

**Better:**
```kconfig
config MY_FEATURE
    depends on NETWORKING && WIFI
    imply DNS_RESOLVER
```

### DON'T: Circular Dependencies

```kconfig
# BAD: Creates cycle
config A
    depends on B

config B
    depends on A
```

### DON'T: Skip help text

```kconfig
# BAD: No context for user
config MAGIC_NUMBER
    int
    default 42
```

**Better:**
```kconfig
config MAGIC_NUMBER
    int "Protocol version number"
    default 42
    help
      The protocol version to use. Must match server.
```

### DON'T: Duplicate CONFIG_ prefix

```kconfig
# BAD: Will become CONFIG_CONFIG_FOO
config CONFIG_FOO
    bool
```
