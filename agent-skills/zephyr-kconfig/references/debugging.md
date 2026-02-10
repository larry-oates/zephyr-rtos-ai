# Kconfig Debugging Guide

## Common Errors and Solutions

### 1. Unmet Direct Dependencies

**Error:**
```
warning: FOO (defined at drivers/Kconfig:10) has direct dependency BAR
but BAR is not currently enabled
```

**Cause:** Symbol `FOO` has `depends on BAR`, but `BAR` is not enabled.

**Fix:**
1. Enable the dependency first: `CONFIG_BAR=y`
2. Or check why `BAR` itself cannot be enabled (chain dependencies)

**Debug command:**
```bash
west build -t menuconfig
# Search for FOO, check its dependencies
```

### 2. Symbol Not Visible

**Symptom:** Setting `CONFIG_FOO=y` in `prj.conf` has no effect or produces warning.

**Causes:**
- `depends on` condition is false
- Symbol is defined but Kconfig file not sourced
- Wrong architecture/SoC/board

**Debug:**
```bash
# Check if symbol exists and its state
west build -t menuconfig
# Press / to search for the symbol
```

**Fix:**
1. Trace `depends on` chain — enable all required dependencies
2. Check `build/zephyr/Kconfig.modules` for module inclusion
3. Verify `zephyr/module.yml` points to correct Kconfig path

### 3. Unknown Symbol Warning

**Error:**
```
warning: attempt to assign nonexistent symbol FOO
```

**Causes:**
- Typo in symbol name
- Missing `CONFIG_` prefix in prj.conf (or extra prefix in Kconfig)
- Kconfig file not sourced by build system

**Fix:**
1. Verify exact symbol name in Kconfig definition
2. In `Kconfig`: `config FOO` (no prefix)
3. In `prj.conf`: `CONFIG_FOO=y` (with prefix)
4. For modules, check `zephyr/module.yml` has correct Kconfig path

### 4. Select Bypassing Dependencies

**Error:**
```
warning: FOO selects BAR, which has unmet direct dependencies (QWERTY)
```

**Cause:** `select` forces a symbol on without checking its `depends on`.

**Fix:**
1. Add the same dependencies to the selecting symbol:
   ```kconfig
   config FOO
       bool "Foo"
       depends on QWERTY  # Add same deps as BAR
       select BAR
   ```
2. Or use `imply` instead of `select` if optional:
   ```kconfig
   config FOO
       bool "Foo"
       imply BAR
   ```

### 5. Recursive Dependency Detected

**Error:**
```
Kconfig:XX: error: recursive dependency detected!
```

**Cause:** Circular reference in `depends on` or `select` chains.

**Debug:**
The error message shows the cycle. Example:
```
FOO -> BAR -> BAZ -> FOO
```

**Fix:**
1. Break the cycle by removing one dependency
2. Restructure to use `imply` instead of `select`
3. Introduce an intermediate symbol

### 6. Symbol Value Unexpectedly Changed

**Symptom:** `CONFIG_FOO` is `n` even though you set it to `y`.

**Causes:**
- Another config file overrides it (board, SoC, or defconfig)
- `default n if SOME_CONDITION` applies
- `depends on` became false

**Debug:**
```bash
# Check final resolved value
grep CONFIG_FOO build/zephyr/.config

# Check where it's set
grep -r "CONFIG_FOO" boards/ soc/
```

---

## Debugging Techniques

### 1. Search in Menuconfig

```bash
west build -t menuconfig
# Press / to search
# Shows: defined at, depends on, selected by, implied by
```

### 2. Check Final Configuration

```bash
# View resolved .config
cat build/zephyr/.config | grep FOO
```

### 3. Trace Module Inclusion

```bash
# Check if module Kconfig is sourced
cat build/zephyr/Kconfig.modules
```

### 4. Verbose Build Output

```bash
west build -v 2>&1 | grep -i kconfig
```

### 5. Compare Configurations

```bash
# Save current config
cp build/zephyr/.config config_before

# Make changes, rebuild
west build

# Compare
diff config_before build/zephyr/.config
```

---

## Configuration Precedence

Lower entries override higher ones:

1. Kconfig `default` values
2. Board defconfig (`boards/<board>/<board>_defconfig`)
3. SoC Kconfig defaults
4. Application `prj.conf`
5. Board-specific overlay (`boards/<board>.conf`)
6. CMake `-DCONFIG_*` flags
7. `menuconfig` changes (saved to `build/zephyr/.config`)

---

## Quick Checklist

| Issue | Check |
|-------|-------|
| Symbol not found | Spelling, CONFIG_ prefix, module.yml |
| Symbol not visible | `depends on` chain |
| Value ignored | Override in defconfig or board.conf |
| Build warning | Read full message, trace dependencies |
| Unexpected default | Check conditional `default` statements |
