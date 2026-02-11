# GPIO Kconfig Reference

Complete reference for GPIO-related Kconfig options.

## Core Options

### CONFIG_GPIO

Enable GPIO driver subsystem.

```kconfig
CONFIG_GPIO=y
```

**Type:** bool
**Default:** n
**Required:** Yes, for any GPIO usage

### CONFIG_GPIO_INIT_PRIORITY

GPIO device initialization priority.

```kconfig
CONFIG_GPIO_INIT_PRIORITY=40
```

**Type:** int
**Default:** 40
**Range:** 0-99

Higher priority (lower number) initializes earlier. Default 40 runs after basic bus drivers.

## Logging Options

### CONFIG_GPIO_LOG_LEVEL

Set GPIO subsystem log level.

```kconfig
# Options: LOG_LEVEL_NONE, LOG_LEVEL_ERR, LOG_LEVEL_WRN, LOG_LEVEL_INF, LOG_LEVEL_DBG
CONFIG_GPIO_LOG_LEVEL_DBG=y
```

**Shortcuts:**
```kconfig
CONFIG_GPIO_LOG_LEVEL_OFF=y   # No logging
CONFIG_GPIO_LOG_LEVEL_ERR=y   # Errors only
CONFIG_GPIO_LOG_LEVEL_WRN=y   # Warnings and errors
CONFIG_GPIO_LOG_LEVEL_INF=y   # Info, warnings, errors
CONFIG_GPIO_LOG_LEVEL_DBG=y   # All messages including debug
```

## Shell Commands

### CONFIG_GPIO_SHELL

Enable GPIO shell commands for debugging.

```kconfig
CONFIG_GPIO_SHELL=y
CONFIG_SHELL=y  # Required dependency
```

**Type:** bool
**Default:** n

**Available shell commands:**
```
gpio conf <device> <pin> <mode>   # Configure pin
gpio get <device> <pin>           # Read pin
gpio set <device> <pin> <value>   # Write pin
gpio blink <device> <pin>         # Toggle pin
```

## Hardware-Specific Options

### Nordic nRF

```kconfig
CONFIG_GPIO_NRF=y           # Nordic GPIO driver
CONFIG_NRF_GPIO_MISC=y      # Extra GPIO features
```

### STM32

```kconfig
CONFIG_GPIO_STM32=y         # STM32 GPIO driver
```

### ESP32

```kconfig
CONFIG_GPIO_ESP32=y         # ESP32 GPIO driver
```

### NXP

```kconfig
CONFIG_GPIO_MCUX=y          # NXP Kinetis GPIO
CONFIG_GPIO_MCUX_LPC=y      # NXP LPC GPIO
CONFIG_GPIO_MCUX_IGPIO=y    # NXP i.MX GPIO
```

## GPIO Expanders

### I2C GPIO Expanders

```kconfig
CONFIG_GPIO_PCA95XX=y       # NXP PCA95xx series (PCA9535, PCA9555, etc.)
CONFIG_GPIO_PCAL6524=y      # NXP PCAL6524
CONFIG_GPIO_MCP23S17=y      # Microchip MCP23017/MCP23S17
CONFIG_GPIO_SX1509B=y       # Semtech SX1509B
```

### SPI GPIO Expanders

```kconfig
CONFIG_GPIO_MCP23SXX=y      # Microchip MCP23Sxx SPI series
```

### Interrupt Support for Expanders

```kconfig
CONFIG_GPIO_PCA95XX_INTERRUPT=y  # Enable interrupt support
```

## Debug Options

### CONFIG_GPIO_HOGS

Enable GPIO hogs (auto-configured GPIOs from devicetree).

```kconfig
CONFIG_GPIO_HOGS=y
```

Allows devicetree to specify GPIOs that should be configured at boot:

```dts
&gpio0 {
    gpio-hog-example {
        gpio-hog;
        gpios = <13 GPIO_ACTIVE_HIGH>;
        output-high;
        line-name = "power-enable";
    };
};
```

### CONFIG_GPIO_GET_DIRECTION

Enable `gpio_pin_get_direction()` API.

```kconfig
CONFIG_GPIO_GET_DIRECTION=y
```

**Type:** bool
**Default:** n

Enables querying pin direction at runtime:
```c
int dir = gpio_pin_get_direction(port, pin);
/* Returns GPIO_INPUT, GPIO_OUTPUT, or 0 */
```

### CONFIG_GPIO_GET_CONFIG

Enable `gpio_pin_get_config()` API.

```kconfig
CONFIG_GPIO_GET_CONFIG=y
```

Enables querying full pin configuration at runtime.

## Typical Configurations

### Minimal Application

```kconfig
CONFIG_GPIO=y
```

### Development/Debug

```kconfig
CONFIG_GPIO=y
CONFIG_GPIO_LOG_LEVEL_DBG=y
CONFIG_GPIO_SHELL=y
CONFIG_SHELL=y
```

### With I2C GPIO Expander

```kconfig
CONFIG_GPIO=y
CONFIG_I2C=y
CONFIG_GPIO_PCA95XX=y
CONFIG_GPIO_PCA95XX_INTERRUPT=y
```

### Low-Power Application

```kconfig
CONFIG_GPIO=y
CONFIG_GPIO_LOG_LEVEL_OFF=y
# Disable unused drivers
CONFIG_GPIO_SHELL=n
```

## Defconfig Examples

### prj.conf for LED Blinky

```kconfig
# Basic GPIO support
CONFIG_GPIO=y
```

### prj.conf for Button with Interrupt

```kconfig
CONFIG_GPIO=y
CONFIG_LOG=y
CONFIG_GPIO_LOG_LEVEL_INF=y
```

### prj.conf for GPIO Shell Testing

```kconfig
CONFIG_GPIO=y
CONFIG_SHELL=y
CONFIG_GPIO_SHELL=y
CONFIG_SHELL_BACKEND_SERIAL=y
CONFIG_UART_CONSOLE=y
```

## Dependencies

GPIO typically requires:

```kconfig
# For interrupt-driven GPIO
CONFIG_EXTI=y               # External interrupt controller (STM32)

# For GPIO expanders
CONFIG_I2C=y                # I2C bus support
CONFIG_SPI=y                # SPI bus support
```

## Verification

Check enabled GPIO options:

```bash
# In build directory
cat zephyr/.config | grep GPIO
```

Check available GPIO devices:

```bash
# In Zephyr shell
device list
gpio conf gpio@50000000 0 in  # Try configuring pin
```
