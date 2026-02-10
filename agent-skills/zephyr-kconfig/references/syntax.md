# Zephyr Kconfig Syntax Guide

Detailed Kconfig language syntax for Zephyr OS configuration symbols.

## Table of Contents

1. [Basic Symbol Definition](#basic-symbol-definition)
2. [Properties](#properties)
3. [Menus and Organization](#menus-and-organization)
4. [Choices](#choices)
5. [Sourcing Files](#sourcing-files)
6. [Conditionals](#conditionals)
7. [Hidden Symbols](#hidden-symbols)
8. [Expressions](#expressions)

---

## Basic Symbol Definition

Symbols are defined in `Kconfig` files.

```kconfig
config MY_SYMBOL
    bool "Description of my symbol"
    default y
    depends on OTHER_SYMBOL
    help
      Detailed help text goes here.
      It can span multiple lines (indented).
```

### Types

| Type | Values | Example |
|------|--------|---------|
| `bool` | `y` / `n` | `bool "Enable feature"` |
| `int` | Integer | `int "Buffer size"` |
| `hex` | Hexadecimal | `hex "Base address"` |
| `string` | Text | `string "Device name"` |

---

## Properties

### default

Sets initial value. Can be conditional. Multiple defaults evaluated top-to-bottom.

```kconfig
default y if DEBUG
default n
```

### depends on

Sets visibility AND validity. If unmet, symbol is invisible and forced to `n`.

```kconfig
depends on GPIO && I2C
depends on (ARCH_HAS_FOO || ARCH_HAS_BAR)
```

### select

Reverse dependency. Forces target to `y` when this symbol is `y`.

```kconfig
select SERIAL
select RING_BUFFER if ASYNC_MODE
```

**Warning:** Ignores `depends on` of selected symbol. Use sparingly.

### imply

Weak reverse dependency. Sets target default to `y`, but user can override.

```kconfig
imply LOG
imply SENSOR_TRIGGER if GPIO
```

**Preferred** over `select` when dependency is optional.

### range

Limits valid values for `int` / `hex`.

```kconfig
range 1 100
range 0x1000 0xFFFF
range 10 1000 if HIGH_MEMORY
```

### visible if

Controls visibility without affecting value. Different from `depends on`.

```kconfig
config INTERNAL_BUFFER
    int "Buffer size"
    visible if ADVANCED_OPTIONS
    default 256
```

---

## Menus and Organization

### menu / endmenu

Group related symbols visually.

```kconfig
menu "My Subsystem Configuration"

config MY_SUBSYSTEM_ENABLE
    bool "Enable My Subsystem"

endmenu
```

### menuconfig

Collapsible menu that is also a symbol.

```kconfig
menuconfig MY_SUBSYSTEM
    bool "My Subsystem"

if MY_SUBSYSTEM

config MY_PARAM
    int "Parameter"
    default 10

endif # MY_SUBSYSTEM
```

### comment

Display-only text in menus.

```kconfig
comment "Advanced options below"
    depends on EXPERT_MODE
```

---

## Choices

Mutually exclusive options.

```kconfig
choice PROTOCOL_TYPE
    prompt "Select Protocol"
    default PROTOCOL_A

config PROTOCOL_A
    bool "Protocol A"

config PROTOCOL_B
    bool "Protocol B"

endchoice
```

### Optional Choice

```kconfig
choice
    prompt "Optional backend"
    optional

config BACKEND_X
    bool "Backend X"

endchoice
```

---

## Sourcing Files

### source

Include other Kconfig files. File must exist.

```kconfig
source "drivers/sensor/my_sensor/Kconfig"
```

### rsource

Relative source (relative to current file).

```kconfig
rsource "subdir/Kconfig"
```

### osource

Optional source. No error if file doesn't exist.

```kconfig
osource "Kconfig.local"
```

### orsource

Optional relative source.

```kconfig
orsource "optional/Kconfig"
```

**Paths:** Relative to `ZEPHYR_BASE`, module root, or current file (rsource).

---

## Conditionals

### if / endif

Wrap multiple symbols in a condition.

```kconfig
if SOC_NRF52832

config MY_NRF_FEATURE
    bool "Feature for nRF52"

config NRF_BUFFER_SIZE
    int "Buffer size"
    default 512

endif # SOC_NRF52832
```

---

## Hidden Symbols

Symbols without a prompt are "hidden" — not visible in menuconfig but can be selected or depend on.

```kconfig
config HAS_HARDWARE_FPU
    bool
    default y if CPU_HAS_FPU

config MY_MATH_LIB
    bool "Math library"
    select HAS_HARDWARE_FPU
```

### Common Hidden Pattern

```kconfig
# Hidden capability symbol
config HAS_SPI_ASYNC
    bool

# Visible feature depending on capability
config USE_SPI_ASYNC
    bool "Use async SPI"
    depends on HAS_SPI_ASYNC
```

---

## Expressions

### Operators

| Operator | Meaning |
|----------|---------|
| `&&` | AND |
| `\|\|` | OR |
| `!` | NOT |
| `=` | Equals |
| `!=` | Not equals |
| `<`, `>`, `<=`, `>=` | Comparison (int/hex) |
| `()` | Grouping |

### Examples

```kconfig
depends on (GPIO && I2C) || SPI
depends on BUFFER_SIZE > 256
depends on !LEGACY_MODE
default y if SOC_FAMILY = "nordic"
```

### String Comparison

```kconfig
default y if BOARD = "nrf52840dk_nrf52840"
```
