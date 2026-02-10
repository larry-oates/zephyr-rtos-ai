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
        // Handle error
    }

    /* Load all settings from storage */
    settings_load();

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
