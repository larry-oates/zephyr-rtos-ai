# Kconfig Functions

Zephyr extends Kconfig with functions for build-time evaluation, particularly for devicetree integration.

## Devicetree Functions

These functions query devicetree properties at Kconfig evaluation time.

### dt_chosen_enabled

Check if a chosen node is enabled.

```kconfig
config MY_FEATURE
    bool "My Feature"
    default y if $(dt_chosen_enabled,zephyr,console)
```

**Returns:** `y` if the chosen node exists and has `status = "okay"`, empty otherwise.

### dt_nodelabel_enabled

Check if a node with given label is enabled.

```kconfig
config USE_EXTERNAL_FLASH
    bool "Use external flash"
    default y if $(dt_nodelabel_enabled,mx25r64)
```

### dt_node_has_prop

Check if a node has a specific property.

```kconfig
config HAS_CUSTOM_MAC
    bool
    default y if $(dt_node_has_prop,/soc/ethernet,local-mac-address)
```

### dt_compat_enabled

Check if any node with compatible string is enabled.

```kconfig
config SENSOR_BME280
    bool "BME280 support"
    default y if $(dt_compat_enabled,bosch$(COMMA)bme280)
```

**Note:** Use `$(COMMA)` for commas in compatible strings.

### dt_alias_enabled

Check if an alias points to an enabled node.

```kconfig
config HAS_LED0
    bool
    default y if $(dt_alias_enabled,led0)
```

---

## String Functions

### dt_chosen_label

Get the label of a chosen node.

```kconfig
# Mostly used in visible symbols for display
```

### dt_node_str_prop_equals

Check if a string property equals a value.

```kconfig
config IS_UART_BACKEND
    bool
    default y if $(dt_node_str_prop_equals,/chosen/zephyr$(COMMA)console,compatible,ns16550)
```

---

## Common Patterns

### Conditional Default Based on Hardware

```kconfig
config SPI_FLASH_DRIVER
    bool "SPI Flash driver"
    default y if $(dt_compat_enabled,jedec$(COMMA)spi-nor)
    help
      Auto-enabled when compatible SPI NOR flash is in devicetree.
```

### Feature Auto-Enable

```kconfig
config USB_DEVICE_STACK
    bool "USB Device Stack"
    default y if $(dt_chosen_enabled,zephyr,usb-device)
```

### Board-Specific Hardware Detection

```kconfig
config DISPLAY_DRIVER
    bool "Display driver"
    default y if $(dt_nodelabel_enabled,display0)
    depends on DISPLAY
```

---

## Function Reference

| Function | Purpose | Example |
|----------|---------|---------|
| `dt_chosen_enabled` | Chosen node enabled? | `$(dt_chosen_enabled,zephyr,console)` |
| `dt_nodelabel_enabled` | Node label enabled? | `$(dt_nodelabel_enabled,uart0)` |
| `dt_compat_enabled` | Compatible enabled? | `$(dt_compat_enabled,nordic$(COMMA)nrf-uart)` |
| `dt_alias_enabled` | Alias target enabled? | `$(dt_alias_enabled,led0)` |
| `dt_node_has_prop` | Node has property? | `$(dt_node_has_prop,/soc,interrupt-parent)` |

---

## Special Variables

| Variable | Meaning |
|----------|---------|
| `$(COMMA)` | Literal comma (for compatible strings) |
| `$(ZEPHYR_BASE)` | Path to Zephyr root |
| `$(BOARD)` | Current board name |
| `$(ARCH)` | Current architecture |

---

## Debugging Function Results

Functions are evaluated during CMake configuration. To see results:

```bash
# Check generated Kconfig.modules
cat build/zephyr/Kconfig.modules

# Run menuconfig and search for symbol
west build -t menuconfig
# The "Depends on" will show evaluated function results
```
