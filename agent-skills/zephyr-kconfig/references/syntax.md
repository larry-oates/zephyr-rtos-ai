# Zephyr Kconfig Syntax Guide

This guide details the Kconfig language syntax used in Zephyr OS for defining configuration symbols.

## Basic Symbol Definition

Symbols are defined in `Kconfig` files.

```kconfig
config MY_SYMBOL
    bool "Description of my symbol"
    default y
    depends on OTHER_SYMBOL
    help
      Detailed help text goes here.
      It can span multiple lines.
```

### Types

- **bool**: Boolean (y/n). Most common.
- **int**: Integer value.
- **string**: String value.
- **hex**: Hexadecimal value.

### Properties

- **default**: Sets the initial value. Can be conditional.
  ```kconfig
  default y if DEBUG
  default n
  ```
- **depends on**: Sets visibility/validity. If unmet, symbol is invisible and disabled.
  ```kconfig
  depends on GPIO && I2C
  ```
- **select**: Reverse dependency. Forces another symbol to 'y' if this one is 'y'.
  *Warning: Ignores `depends on` of the selected symbol. Use carefully.*
  ```kconfig
  select SERIAL
  ```
- **imply**: Weak reverse dependency. Enables another symbol but allows user to disable it.
  ```kconfig
  imply LOG
  ```
- **range**: Limits valid values for int/hex.
  ```kconfig
  range 1 100
  ```

## Menus and Organization

Group related symbols to keep the interactive menu clean (e.g., in `menuconfig`).

```kconfig
menu "My Subsystem Configuration"

config MY_SUBSYSTEM_ENABLE
    bool "Enable My Subsystem"

if MY_SUBSYSTEM_ENABLE

config MY_PARAM
    int "Parameter"
    default 10

endif # MY_SUBSYSTEM_ENABLE

endmenu
```

## Choices

Mutually exclusive options.

```kconfig
choice
    prompt "Select Protocol"
    default PROTOCOL_A

config PROTOCOL_A
    bool "Protocol A"

config PROTOCOL_B
    bool "Protocol B"

endchoice
```

## Sourcing Files

Include other Kconfig files.

```kconfig
source "drivers/sensor/my_sensor/Kconfig"
```

In Zephyr, paths are relative to `ZEPHYR_BASE` or the module root.

## Conditionals

Blocks can be conditional.

```kconfig
if SOC_NRF52832

config MY_NRF_FEATURE
    bool "Feature for nRF52"

endif
```
