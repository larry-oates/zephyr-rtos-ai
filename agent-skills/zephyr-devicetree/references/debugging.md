# Devicetree Debugging and Troubleshooting

Common errors, debugging techniques, and resolution strategies for devicetree issues.

## Key Build Outputs

After building, examine these files:

| File | Purpose |
|------|---------|
| `build/zephyr/zephyr.dts` | Final merged devicetree (overlays applied) |
| `build/zephyr/zephyr.dts.pre` | Pre-processed DTS (includes resolved) |
| `build/zephyr/include/generated/devicetree_generated.h` | Generated C macros |
| `build/zephyr/dts.cmake` | CMake devicetree variables |

## Common Errors and Fixes

### 1. Binding Not Found

**Error:**
```
devicetree error: no binding for /soc/my-device@40000000
```

**Causes:**
- Missing `compatible` property
- `compatible` doesn't match any binding file
- Binding file not in search path

**Fix:**
```devicetree
/* Add or correct compatible */
my_device: my-device@40000000 {
    compatible = "vendor,my-device";  /* Must match binding filename */
    reg = <0x40000000 0x1000>;
};
```

Check binding exists at: `dts/bindings/*/vendor,my-device.yaml`

### 2. Required Property Missing

**Error:**
```
devicetree error: 'reg' is required by binding but not in node /soc/uart@40000000
```

**Fix:**
Add the required property:
```devicetree
&uart0 {
    reg = <0x40000000 0x1000>;  /* Add required property */
};
```

### 3. Property Type Mismatch

**Error:**
```
devicetree error: expected int for 'current-speed', got string
```

**Fix:**
```devicetree
/* Wrong */
current-speed = "115200";

/* Correct */
current-speed = <115200>;
```

### 4. DEVICE_DT_GET Returns NULL

**Symptom:** Device pointer is NULL at runtime.

**Causes:**
1. Node has `status = "disabled"` or missing status
2. Driver not enabled in Kconfig
3. Wrong node identifier

**Debug:**
```c
const struct device *dev = DEVICE_DT_GET(DT_NODELABEL(my_device));
if (!device_is_ready(dev)) {
    printk("Device not ready! Status: %d\n", dev->state->init_res);
}
```

**Fix:**
```devicetree
&my_device {
    status = "okay";  /* Enable the node */
};
```

Also check Kconfig:
```
CONFIG_MY_DRIVER=y
```

### 5. Linker Error: __device_dts_ord_N

**Error:**
```
undefined reference to `__device_dts_ord_42'
```

**Cause:** Node exists in DTS but driver isn't compiled.

**Fix:**
Enable the driver in `prj.conf`:
```
CONFIG_UART_DRIVER=y
CONFIG_UART_VENDOR=y
```

### 6. Duplicate Node or Property

**Error:**
```
devicetree error: duplicate node name 'uart@40000000'
```

**Fix:**
Use node label to modify existing node instead of creating new:
```devicetree
/* Wrong - creates duplicate */
/ {
    soc {
        uart@40000000 { ... };
    };
};

/* Correct - modifies existing */
&uart0 {
    status = "okay";
};
```

### 7. Phandle Resolution Failed

**Error:**
```
devicetree error: phandle reference '&nonexistent' not found
```

**Fix:**
Verify the referenced node exists and has a label:
```devicetree
/* Ensure label exists */
gpio0: gpio@50000000 {
    ...
};

/* Then reference works */
my_device {
    gpios = <&gpio0 5 0>;
};
```

### 8. Cell Count Mismatch

**Error:**
```
devicetree error: wrong number of cells for 'gpios' (got 2, expected 3)
```

**Fix:**
Check parent's `#*-cells` and provide correct number:
```devicetree
/* If gpio0 has #gpio-cells = <2> */
gpios = <&gpio0 5 GPIO_ACTIVE_LOW>;  /* 2 cells after phandle */

/* If has #gpio-cells = <3> */
gpios = <&gpio0 0 5 GPIO_ACTIVE_LOW>;  /* 3 cells after phandle */
```

## Debugging Commands

### View Final Devicetree

```bash
# After build, view merged DTS
cat build/zephyr/zephyr.dts

# Or use west
west build -t zephyr.dts
```

### Check Generated Macros

```bash
# Search for your node's macros
grep -r "my_device" build/zephyr/include/generated/devicetree_generated.h
```

### Validate Devicetree Manually

```bash
# Run dtc directly for detailed errors
dtc -I dts -O dtb -o /dev/null build/zephyr/zephyr.dts.pre 2>&1
```

### CMake Devicetree Info

```bash
# Show devicetree CMake variables
west build -t devicetree_info
```

## Overlay Debugging

### Verify Overlay Applied

1. Build with overlay
2. Check `build/zephyr/zephyr.dts` for your changes
3. If changes missing, verify overlay path:

```bash
# Explicit overlay
west build -b my_board -- -DDTC_OVERLAY_FILE=my.overlay

# Check what overlays were used
grep DTC_OVERLAY build/CMakeCache.txt
```

### Overlay Search Order

Zephyr looks for overlays in this order:
1. `DTC_OVERLAY_FILE` CMake variable
2. `boards/<BOARD>.overlay` in app directory
3. `app.overlay` in app directory

## Macro Debugging

### Print Macro Values

```c
/* Stringify macro for debugging */
#define STRINGIFY(x) #x
#define TOSTRING(x) STRINGIFY(x)

#define MY_NODE DT_NODELABEL(uart0)
#pragma message "REG_ADDR = " TOSTRING(DT_REG_ADDR(MY_NODE))
```

### Check Node Existence at Compile Time

```c
#if !DT_NODE_EXISTS(DT_NODELABEL(my_device))
#error "Required node my_device not found in devicetree"
#endif

BUILD_ASSERT(DT_NODE_HAS_STATUS(DT_NODELABEL(uart0), okay),
             "uart0 must be enabled");
```

## Common Pitfalls

### 1. Wrong Node Label Syntax

```devicetree
/* Wrong - using & in definition */
&my_label: node@1000 { };

/* Correct */
my_label: node@1000 { };

/* Reference uses & */
&my_label { status = "okay"; };
```

### 2. Forgetting Semicolons

```devicetree
/* Wrong */
node {
    property = <1>   /* Missing semicolon */
}

/* Correct */
node {
    property = <1>;
};
```

### 3. Case Sensitivity

Node names and properties are case-sensitive:
```devicetree
/* These are different nodes */
uart0: UART@40000000 { };
uart1: uart@40000000 { };
```

### 4. Unit Address Mismatch

```devicetree
/* Wrong - unit address doesn't match reg */
uart@40000000 {
    reg = <0x50000000 0x1000>;
};

/* Correct */
uart@50000000 {
    reg = <0x50000000 0x1000>;
};
```

## Kconfig Integration Issues

### Driver Not Found for Compatible

The compatible must match both:
1. A binding file
2. A driver's `DT_DRV_COMPAT`

```c
/* In driver */
#define DT_DRV_COMPAT vendor_my_device  /* Must match compatible */
```

### Check Driver is Compiled

```bash
# See if driver object exists
ls build/zephyr/drivers/*/my_driver.c.obj
```

## Tips

1. **Start simple** — Test with minimal overlay, add complexity gradually
2. **Check zephyr.dts first** — Most issues visible in merged output
3. **Use node labels** — Prefer `DT_NODELABEL()` over `DT_PATH()`
4. **Read binding files** — They document required properties
5. **Enable verbose build** — `west build -v` shows DTC commands
