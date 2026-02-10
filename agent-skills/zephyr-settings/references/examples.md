# Zephyr Settings Examples

## Static Handler Definition

```c
#include <zephyr/settings/settings.h>

static uint32_t my_val = 100;

static int my_set(const char *name, size_t len, settings_read_cb read_cb, void *cb_arg)
{
    const char *next;
    if (settings_name_steq(name, "val", &next) && !next) {
        if (len != sizeof(my_val)) {
            return -EINVAL;
        }
        return read_cb(cb_arg, &my_val, sizeof(my_val));
    }
    return -ENOENT;
}

static int my_export(int (*storage_func)(const char *name, const void *value, size_t val_len))
{
    return storage_func("my_app/val", &my_val, sizeof(my_val));
}

SETTINGS_STATIC_HANDLER_DEFINE(my_app, "my_app", NULL, my_set, NULL, my_export);
```

## Basic Usage (Init, Load, Save)

```c
int main(void)
{
    int rc;

    rc = settings_subsys_init();
    if (rc) {
        LOG_ERR("Settings init failed: %d", rc);
        return rc;
    }

    /* Load all settings from storage */
    rc = settings_load();
    if (rc) {
        LOG_WRN("Settings load failed: %d, using defaults", rc);
    }

    /* Modify value and save */
    my_val = 200;
    settings_save_one("my_app/val", &my_val, sizeof(my_val));

    /* Or save all modified values */
    settings_save();

    return 0;
}
```

## Handling Multiple Keys in a Subtree

```c
static int multi_set(const char *name, size_t len, settings_read_cb read_cb, void *cb_arg)
{
    const char *next;
    if (settings_name_steq(name, "key1", &next) && !next) {
        return read_cb(cb_arg, &val1, sizeof(val1));
    } else if (settings_name_steq(name, "key2", &next) && !next) {
        return read_cb(cb_arg, &val2, sizeof(val2));
    }
    return -ENOENT;
}
```

## Runtime Set/Get

```c
/* Inject value into RAM handler */
settings_runtime_set("my_app/val", &new_val, sizeof(new_val));

/* Get value from RAM handler */
settings_runtime_get("my_app/val", &buf, sizeof(buf));
```

---

## Real-World Use Cases

### Device Calibration Data

```c
#include <zephyr/settings/settings.h>

struct calibration {
    float offset;
    float gain;
    uint32_t timestamp;
};

static struct calibration sensor_cal = {0.0f, 1.0f, 0};

static int cal_set(const char *name, size_t len,
                   settings_read_cb read_cb, void *cb_arg)
{
    const char *next;
    if (settings_name_steq(name, "sensor", &next) && !next) {
        if (len != sizeof(sensor_cal)) {
            return -EINVAL;
        }
        return read_cb(cb_arg, &sensor_cal, sizeof(sensor_cal));
    }
    return -ENOENT;
}

static int cal_export(int (*storage_func)(const char *name,
                      const void *value, size_t val_len))
{
    return storage_func("cal/sensor", &sensor_cal, sizeof(sensor_cal));
}

SETTINGS_STATIC_HANDLER_DEFINE(cal, "cal", NULL, cal_set, NULL, cal_export);
```

### WiFi Credentials (String Handling)

```c
static char wifi_ssid[33] = "";
static char wifi_pass[64] = "";

static int wifi_set(const char *name, size_t len,
                    settings_read_cb read_cb, void *cb_arg)
{
    const char *next;

    if (settings_name_steq(name, "ssid", &next) && !next) {
        if (len >= sizeof(wifi_ssid)) {
            return -EINVAL;
        }
        int rc = read_cb(cb_arg, wifi_ssid, len);
        wifi_ssid[len] = '\0';  /* Ensure null termination */
        return rc;
    }

    if (settings_name_steq(name, "pass", &next) && !next) {
        if (len >= sizeof(wifi_pass)) {
            return -EINVAL;
        }
        int rc = read_cb(cb_arg, wifi_pass, len);
        wifi_pass[len] = '\0';
        return rc;
    }

    return -ENOENT;
}

static int wifi_export(int (*storage_func)(const char *name,
                       const void *value, size_t val_len))
{
    int rc = storage_func("wifi/ssid", wifi_ssid, strlen(wifi_ssid));
    if (rc) {
        return rc;
    }
    return storage_func("wifi/pass", wifi_pass, strlen(wifi_pass));
}

SETTINGS_STATIC_HANDLER_DEFINE(wifi, "wifi", NULL, wifi_set, NULL, wifi_export);
```

### Factory Reset Pattern

```c
void factory_reset(void)
{
    /* Delete all application settings */
    settings_delete("wifi/ssid");
    settings_delete("wifi/pass");
    settings_delete("cal/sensor");
    settings_delete("app/config");

    /* Reset to defaults in RAM */
    memset(wifi_ssid, 0, sizeof(wifi_ssid));
    memset(wifi_pass, 0, sizeof(wifi_pass));
    sensor_cal = (struct calibration){0.0f, 1.0f, 0};

    LOG_INF("Factory reset complete");
}
```

---

## Integration Examples

### Settings + Bluetooth

Store and restore Bluetooth device name:

```c
#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/settings/settings.h>

static char bt_name[CONFIG_BT_DEVICE_NAME_MAX + 1] = CONFIG_BT_DEVICE_NAME;

static int bt_settings_set(const char *name, size_t len,
                           settings_read_cb read_cb, void *cb_arg)
{
    const char *next;

    if (settings_name_steq(name, "name", &next) && !next) {
        if (len >= sizeof(bt_name)) {
            return -EINVAL;
        }
        int rc = read_cb(cb_arg, bt_name, len);
        bt_name[len] = '\0';
        return rc;
    }
    return -ENOENT;
}

static int bt_settings_commit(void)
{
    /* Apply the loaded name to Bluetooth stack */
    return bt_set_name(bt_name);
}

static int bt_settings_export(int (*storage_func)(const char *name,
                              const void *value, size_t val_len))
{
    return storage_func("bt_app/name", bt_name, strlen(bt_name));
}

SETTINGS_STATIC_HANDLER_DEFINE(bt_app, "bt_app", NULL,
    bt_settings_set, bt_settings_commit, bt_settings_export);
```

### Settings + Shell Commands

Runtime settings modification via shell:

```c
#include <zephyr/shell/shell.h>
#include <zephyr/settings/settings.h>
#include <stdlib.h>

static int cmd_settings_set(const struct shell *sh, size_t argc, char **argv)
{
    if (argc != 3) {
        shell_error(sh, "Usage: settings_set <key> <value>");
        return -EINVAL;
    }

    uint32_t value = strtoul(argv[2], NULL, 0);
    int rc = settings_save_one(argv[1], &value, sizeof(value));

    if (rc) {
        shell_error(sh, "Failed to save: %d", rc);
    } else {
        shell_print(sh, "Saved %s = %u", argv[1], value);
    }
    return rc;
}

static int cmd_settings_get(const struct shell *sh, size_t argc, char **argv)
{
    if (argc != 2) {
        shell_error(sh, "Usage: settings_get <key>");
        return -EINVAL;
    }

    uint32_t value;
    ssize_t len = settings_load_one(argv[1], &value, sizeof(value));

    if (len < 0) {
        shell_error(sh, "Failed to load: %zd", len);
        return len;
    }
    shell_print(sh, "%s = %u", argv[1], value);
    return 0;
}

static int cmd_settings_delete(const struct shell *sh, size_t argc, char **argv)
{
    if (argc != 2) {
        shell_error(sh, "Usage: settings_delete <key>");
        return -EINVAL;
    }

    int rc = settings_delete(argv[1]);
    if (rc) {
        shell_error(sh, "Failed to delete: %d", rc);
    } else {
        shell_print(sh, "Deleted %s", argv[1]);
    }
    return rc;
}

SHELL_STATIC_SUBCMD_SET_CREATE(settings_cmds,
    SHELL_CMD(set, NULL, "Set a setting value", cmd_settings_set),
    SHELL_CMD(get, NULL, "Get a setting value", cmd_settings_get),
    SHELL_CMD(delete, NULL, "Delete a setting", cmd_settings_delete),
    SHELL_SUBCMD_SET_END
);

SHELL_CMD_REGISTER(settings, &settings_cmds, "Settings commands", NULL);
```

### Settings + Logging Configuration

Persist log level across reboots:

```c
#include <zephyr/logging/log_ctrl.h>
#include <zephyr/settings/settings.h>

static uint32_t saved_log_level = LOG_LEVEL_INF;

static int log_settings_set(const char *name, size_t len,
                            settings_read_cb read_cb, void *cb_arg)
{
    const char *next;

    if (settings_name_steq(name, "level", &next) && !next) {
        if (len != sizeof(saved_log_level)) {
            return -EINVAL;
        }
        return read_cb(cb_arg, &saved_log_level, sizeof(saved_log_level));
    }
    return -ENOENT;
}

static int log_settings_commit(void)
{
    /* Apply saved log level to all modules */
    uint32_t modules_cnt = log_src_cnt_get(0);

    for (uint32_t i = 0; i < modules_cnt; i++) {
        log_filter_set(NULL, 0, i, saved_log_level);
    }

    LOG_INF("Log level set to %u", saved_log_level);
    return 0;
}

static int log_settings_export(int (*storage_func)(const char *name,
                               const void *value, size_t val_len))
{
    return storage_func("log/level", &saved_log_level, sizeof(saved_log_level));
}

SETTINGS_STATIC_HANDLER_DEFINE(log_cfg, "log", NULL,
    log_settings_set, log_settings_commit, log_settings_export);

/* Call this to change and persist log level */
void set_global_log_level(uint32_t level)
{
    saved_log_level = level;
    log_settings_commit();  /* Apply immediately */
    settings_save_one("log/level", &saved_log_level, sizeof(saved_log_level));
}
```

### Settings + Devicetree Partition

Reference storage partition from devicetree:

```dts
/* boards/my_board.overlay or app.overlay */
/ {
    chosen {
        zephyr,settings-partition = &storage_partition;
    };
};

&flash0 {
    partitions {
        compatible = "fixed-partitions";
        #address-cells = <1>;
        #size-cells = <1>;

        /* Application code */
        slot0_partition: partition@10000 {
            label = "image-0";
            reg = <0x00010000 0x000e0000>;
        };

        /* Settings storage (64KB) */
        storage_partition: partition@f0000 {
            label = "storage";
            reg = <0x000f0000 0x00010000>;
        };
    };
};
```

---

## Handler with Commit Priority

When handlers depend on each other:

```c
/* Network service - must initialize first (higher priority = lower cprio) */
SETTINGS_STATIC_HANDLER_DEFINE_WITH_CPRIO(net_cfg, "net", -10,
    NULL, net_set, net_commit, net_export);

/* App config - depends on network (lower priority = higher cprio) */
SETTINGS_STATIC_HANDLER_DEFINE_WITH_CPRIO(app_cfg, "app", 10,
    NULL, app_set, app_commit, app_export);
```

Or with dynamic registration:

```c
static struct settings_handler net_handler = {
    .name = "net",
    .h_set = net_set,
    .h_commit = net_commit,
    .h_export = net_export,
};

static struct settings_handler app_handler = {
    .name = "app",
    .h_set = app_set,
    .h_commit = app_commit,
    .h_export = app_export,
};

void init_settings(void)
{
    settings_subsys_init();

    /* Register with explicit priorities */
    settings_register_with_cprio(&net_handler, -10);  /* Higher priority */
    settings_register_with_cprio(&app_handler, 10);   /* Lower priority */

    settings_load();
}
```
