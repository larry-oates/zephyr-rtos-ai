# Zephyr Settings API Reference

## Core API

### Initialization
- `int settings_subsys_init(void)`: Initialize the settings subsystem and backends. Call after FS is mounted if using a file backend.

### Handler Registration
- `int settings_register(struct settings_handler *cf)`: Register a dynamic settings handler.
- `SETTINGS_STATIC_HANDLER_DEFINE(name, tree, get, set, commit, export)`: Define a static settings handler.

### Loading Settings
- `int settings_load(void)`: Load all registered settings from persistent storage.
- `int settings_load_subtree(const char *subtree)`: Load a specific subtree.
- `ssize_t settings_load_one(const char *name, void *buf, size_t buf_len)`: Load a single setting into a buffer.
- `int settings_load_subtree_direct(const char *subtree, settings_load_direct_cb cb, void *param)`: Load a subtree using a custom callback, bypassing registered handlers.

### Saving Settings
- `int settings_save(void)`: Save all currently running settings that differ from persisted values.
- `int settings_save_subtree(const char *subtree)`: Save a specific subtree.
- `int settings_save_one(const char *name, const void *value, size_t val_len)`: Write a single value to storage.
- `int settings_delete(const char *name)`: Delete a single setting from storage (sets value to NULL).

### Runtime API (requires CONFIG_SETTINGS_RUNTIME)
- `int settings_runtime_set(const char *name, const void *data, size_t len)`: Inject a value into a handler in RAM.
- `int settings_runtime_get(const char *name, void *data, size_t len)`: Retrieve a value from a handler in RAM.

## Structures and Types

### settings_handler
```c
struct settings_handler {
    const char *name;      /* Name of subtree (e.g., "my_app") */
    int cprio;             /* Commit priority (lower is higher) */
    int (*h_get)(const char *key, char *val, int val_len_max);
    int (*h_set)(const char *key, size_t len, settings_read_cb read_cb, void *cb_arg);
    int (*h_commit)(void);
    int (*h_export)(int (*export_func)(const char *name, const void *val, size_t val_len));
};
```

### settings_read_cb
```c
typedef ssize_t (*settings_read_cb)(void *cb_arg, void *data, size_t len);
```
Used within `h_set` to read the actual data from the backend.

## Key Name Processing
- `int settings_name_steq(const char *name, const char *key, const char **next)`: Compare start of name with key.
- `int settings_name_next(const char *name, const char **next)`: Find number of characters before the first separator.
