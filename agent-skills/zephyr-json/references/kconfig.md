# JSON Kconfig Reference

## Required Configuration

```kconfig
CONFIG_JSON_LIBRARY=y
```

Enables the JSON parsing and encoding library.

## Optional Configuration

```kconfig
CONFIG_JSON_LIBRARY_FP_SUPPORT=y
```

Enables floating-point support (`float` and `double` types).

**Implications:**
- Automatically selects `CONFIG_CBPRINTF_FP_SUPPORT`
- Automatically selects `CONFIG_REQUIRES_FULL_LIBC`
- Requires libc with: `strtof()`, `strtod()`, `isnan()`, `isinf()`

**When to enable:**
- Parsing JSON with decimal numbers
- Sending sensor data with floating-point values
- Cloud protocols requiring float precision

## Example prj.conf

### Minimal (integers only)

```ini
CONFIG_JSON_LIBRARY=y
```

### With floating-point

```ini
CONFIG_JSON_LIBRARY=y
CONFIG_JSON_LIBRARY_FP_SUPPORT=y
```

### For newlib (common on ARM)

```ini
CONFIG_JSON_LIBRARY=y
CONFIG_JSON_LIBRARY_FP_SUPPORT=y
CONFIG_NEWLIB_LIBC=y
```

### For picolibc

```ini
CONFIG_JSON_LIBRARY=y
CONFIG_JSON_LIBRARY_FP_SUPPORT=y
CONFIG_PICOLIBC=y
```

## Memory Considerations

The JSON library is designed for minimal memory footprint:

- **No dynamic allocation**: All memory is stack/static
- **Descriptors**: Each descriptor is ~20-32 bytes (compile-time)
- **Buffer sizing**: Use `json_calc_encoded_len()` to determine exact buffer needs

### Estimating Buffer Size

```c
// Calculate exact size needed
ssize_t needed = json_calc_encoded_len(descr, ARRAY_SIZE(descr), &data);
if (needed < 0) {
    // Handle error
}

char *buffer = k_malloc(needed + 1);  // +1 for null terminator
```

## Common Integration Patterns

### HTTP Server

```ini
CONFIG_JSON_LIBRARY=y
CONFIG_NETWORKING=y
CONFIG_NET_SOCKETS=y
CONFIG_HTTP_SERVER=y
```

### MQTT/Cloud

```ini
CONFIG_JSON_LIBRARY=y
CONFIG_JSON_LIBRARY_FP_SUPPORT=y
CONFIG_NETWORKING=y
CONFIG_MQTT_LIB=y
```

### CoAP

```ini
CONFIG_JSON_LIBRARY=y
CONFIG_COAP=y
```
