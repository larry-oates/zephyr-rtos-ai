# Settings Troubleshooting Guide

This guide covers common issues, debugging strategies, and anti-patterns when working with Zephyr Settings.

## Common Issues

### 1. Settings Not Persisting After Reboot

**Symptoms:** Values reset to defaults after power cycle.

**Causes:**
- Forgot to call `settings_subsys_init()` before `settings_load()`
- Filesystem not mounted (for file backend)
- Flash partition not properly defined in devicetree
- Backend not registered (`CONFIG_SETTINGS_NVS=y` etc.)
- `h_export` not implemented (values can't be saved)

**Solution:**
```c
/* Correct initialization order */
int main(void)
{
    /* 1. Mount FS first (if using file backend) */
    fs_mount(&lfs_mnt);

    /* 2. Initialize settings subsystem */
    int rc = settings_subsys_init();
    if (rc) {
        LOG_ERR("Settings init failed: %d", rc);
    }

    /* 3. Register handlers (if dynamic) */
    settings_register(&my_handler);

    /* 4. Load settings from storage */
    settings_load();

    /* Now settings are available */
}
```

---

### 2. `h_set` Returns -EINVAL

**Symptoms:** Settings fail to load with `-EINVAL` error.

**Causes:**
- Size mismatch: `len` doesn't match expected variable size
- Incorrect `read_cb` usage
- Corrupted storage data

**Solution:**
```c
static int my_set(const char *name, size_t len,
                  settings_read_cb read_cb, void *cb_arg)
{
    const char *next;

    if (settings_name_steq(name, "val", &next) && !next) {
        /* Always validate size before reading */
        if (len != sizeof(my_val)) {
            LOG_WRN("Size mismatch: expected %zu, got %zu",
                    sizeof(my_val), len);
            return -EINVAL;
        }
        return read_cb(cb_arg, &my_val, sizeof(my_val));
    }
    return -ENOENT;
}
```

---

### 3. ZMS Backend Collision Errors

**Symptoms:** `-ENOSPC` errors or hash collision warnings in logs.

**Cause:** Too many unique keys for configured collision bits.

**Solution:**
```
# Increase collision handling capacity (2^n possible collisions)
CONFIG_SETTINGS_ZMS_MAX_COLLISIONS_BITS=4
```

---

### 4. `h_export` Not Being Called

**Symptoms:** `settings_save()` completes but values aren't persisted.

**Cause:** Handler doesn't implement `h_export`, so `settings_save()` can't persist values.

**Solution:**
```c
static int my_export(int (*storage_func)(const char *name,
                     const void *value, size_t val_len))
{
    /* Export all values that need persistence */
    int rc = storage_func("my_app/val", &my_val, sizeof(my_val));
    if (rc) {
        return rc;
    }
    return storage_func("my_app/name", my_name, strlen(my_name));
}

/* Include export function in handler definition */
SETTINGS_STATIC_HANDLER_DEFINE(my_app, "my_app", NULL, my_set, NULL, my_export);
```

---

### 5. Race Condition During `h_commit`

**Symptoms:** Dependent handlers fail during commit phase.

**Cause:** Wrong commit priority ordering - handlers execute in wrong order.

**Solution:**
```c
/* Service that others depend on (lower cprio = higher priority) */
settings_register_with_cprio(&base_handler, -10);

/* Service that depends on above (higher cprio = lower priority) */
settings_register_with_cprio(&dependent_handler, 10);
```

Or with static handlers:
```c
SETTINGS_STATIC_HANDLER_DEFINE_WITH_CPRIO(base, "base", -10,
    NULL, base_set, base_commit, base_export);

SETTINGS_STATIC_HANDLER_DEFINE_WITH_CPRIO(dependent, "dependent", 10,
    NULL, dep_set, dep_commit, dep_export);
```

---

### 6. Settings Load Partially Fails

**Symptoms:** Some settings load, others don't.

**Causes:**
- Key name mismatch between save and load
- Handler subtree doesn't match key prefix
- `h_set` returns `-ENOENT` for valid keys

**Debugging:**
```c
static int my_set(const char *name, size_t len,
                  settings_read_cb read_cb, void *cb_arg)
{
    LOG_DBG("Loading key: '%s', len: %zu", name, len);

    /* ... rest of implementation */
}
```

---

## Debugging Tips

### 1. Enable Settings Logging

```
CONFIG_SETTINGS_LOG_LEVEL_DBG=y
CONFIG_LOG=y
```

### 2. Verify Backend Registration

Check that backend init functions are called during startup. Add logging to confirm:
```c
LOG_INF("Settings subsys init returned: %d", settings_subsys_init());
```

### 3. Use `settings_load_one()` for Testing

Test individual settings loading without full handler setup:
```c
uint32_t test_val;
ssize_t len = settings_load_one("my_app/val", &test_val, sizeof(test_val));
if (len < 0) {
    LOG_ERR("Load failed: %zd", len);
} else {
    LOG_INF("Loaded value: %u (len: %zd)", test_val, len);
}
```

### 4. Check Flash Partition

Verify storage partition is properly defined:
```bash
west build -t partition_manager_report
```

### 5. Dump All Settings

Iterate through settings for debugging:
```c
static int print_cb(const char *key, size_t len,
                    settings_read_cb read_cb, void *cb_arg, void *param)
{
    printk("Key: %s, len: %zu\n", key, len);
    return 0;
}

void dump_all_settings(void)
{
    settings_load_subtree_direct("", print_cb, NULL);
}
```

---

## Common Anti-Patterns

### DON'T: Save Inside `h_set`

```c
/* WRONG: Don't save during load - causes infinite loop or corruption */
static int bad_set(const char *name, size_t len,
                   settings_read_cb read_cb, void *cb_arg)
{
    read_cb(cb_arg, &my_val, sizeof(my_val));
    settings_save_one("my/val", &my_val, sizeof(my_val));  /* BAD! */
    return 0;
}
```

**DO:** Separate load and save operations.

---

### DON'T: Ignore Return Values

```c
/* WRONG: Ignoring errors */
settings_subsys_init();  /* What if this fails? */
settings_load();         /* What if this fails? */
```

**DO:** Check return values:
```c
int rc = settings_subsys_init();
if (rc) {
    LOG_ERR("Settings init failed: %d", rc);
    /* Handle error - use defaults, retry, etc. */
}

rc = settings_load();
if (rc) {
    LOG_WRN("Settings load failed: %d, using defaults", rc);
}
```

---

### DON'T: Use Settings for High-Frequency Data

Settings is for **configuration**, not **telemetry** or **logging**.

| Good Uses | Bad Uses |
|-----------|----------|
| Device name | Sensor readings |
| Calibration data | Event counters |
| WiFi credentials | Timestamps |
| User preferences | Frequently changing state |

**Reason:** Flash wear leveling has limits. Frequent writes reduce flash lifespan.

**Alternative:** Use RAM buffers, logging subsystem, or battery-backed RTC RAM.

---

### DON'T: Forget Null Termination for Strings

```c
/* WRONG: String may not be null-terminated */
static int bad_string_set(const char *name, size_t len,
                          settings_read_cb read_cb, void *cb_arg)
{
    if (settings_name_steq(name, "name", &next) && !next) {
        return read_cb(cb_arg, my_name, len);  /* Missing null terminator! */
    }
    return -ENOENT;
}
```

**DO:** Always null-terminate strings:
```c
static int good_string_set(const char *name, size_t len,
                           settings_read_cb read_cb, void *cb_arg)
{
    if (settings_name_steq(name, "name", &next) && !next) {
        if (len >= sizeof(my_name)) {
            return -EINVAL;  /* Too long */
        }
        int rc = read_cb(cb_arg, my_name, len);
        my_name[len] = '\0';  /* Ensure null termination */
        return rc;
    }
    return -ENOENT;
}
```

---

### DON'T: Hardcode Key Names Inconsistently

```c
/* WRONG: Key mismatch between save and handler */
settings_save_one("myapp/value", &val, sizeof(val));  /* Note: "myapp" */

SETTINGS_STATIC_HANDLER_DEFINE(my_app, "my_app", ...);  /* Note: "my_app" */
```

**DO:** Use constants for key names:
```c
#define SETTINGS_KEY_VALUE "my_app/value"

settings_save_one(SETTINGS_KEY_VALUE, &val, sizeof(val));
```

---

## Error Code Reference

| Error | Meaning | Common Cause |
|-------|---------|--------------|
| `-EINVAL` | Invalid argument | Size mismatch, bad parameters |
| `-ENOENT` | Not found | Key doesn't exist, handler missing |
| `-ENOSPC` | No space | Flash full, ZMS collision limit |
| `-EIO` | I/O error | Flash write failure |
| `-ENOTSUP` | Not supported | Feature not enabled in Kconfig |
| `-ENODEV` | No device | Backend not initialized |
