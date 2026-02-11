# Zephyr Settings API Reference

## Core API

### Initialization
- `int settings_subsys_init(void)`: Initialize the settings subsystem and backends. Call after FS is mounted if using a file backend.

### Handler Registration

#### Dynamic Registration
- `int settings_register(struct settings_handler *cf)`: Register a dynamic settings handler with default commit priority (0).
- `int settings_register_with_cprio(struct settings_handler *cf, int cprio)`: Register a handler with explicit commit priority.

#### Static Registration
- `SETTINGS_STATIC_HANDLER_DEFINE(name, tree, get, set, commit, export)`: Define a static settings handler with default priority.
- `SETTINGS_STATIC_HANDLER_DEFINE_WITH_CPRIO(name, tree, cprio, get, set, commit, export)`: Define a static handler with explicit commit priority.

**Commit Priority (`cprio`):**
- Lower values = Higher priority (executed first during commit)
- Default: 0
- Use negative values for handlers that others depend on
- Use positive values for handlers that depend on others

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

### Value Inspection
- `ssize_t settings_get_val_len(const char *name)`: Get the data length of a stored value without loading it.

**Use case:** Dynamic memory allocation for variable-length settings:
```c
ssize_t len = settings_get_val_len("my_app/config");
if (len > 0) {
    char *buf = k_malloc(len);
    if (buf) {
        settings_load_one("my_app/config", buf, len);
        /* Use buffer... */
        k_free(buf);
    }
}
```

### Runtime API (requires CONFIG_SETTINGS_RUNTIME)
- `int settings_runtime_set(const char *name, const void *data, size_t len)`: Inject a value into a handler in RAM.
- `int settings_runtime_get(const char *name, void *data, size_t len)`: Retrieve a value from a handler in RAM.

### Backend Registration (for custom backends)
- `void settings_src_register(struct settings_store *cs)`: Register a storage source (read from).
- `void settings_dst_register(struct settings_store *cs)`: Register a storage destination (write to).

---

## Structures and Types

### settings_handler
```c
struct settings_handler {
    const char *name;      /* Name of subtree (e.g., "my_app") */
    int cprio;             /* Commit priority (lower value = higher priority) */
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

### settings_store (for custom backends)
```c
struct settings_store {
    sys_snode_t cs_next;
    const struct settings_store_itf *cs_itf;
};

struct settings_store_itf {
    int (*csi_load)(struct settings_store *cs, const struct settings_load_arg *arg);
    int (*csi_save)(struct settings_store *cs, const char *name,
                    const char *value, size_t val_len);
};
```

---

## Key Name Processing
- `int settings_name_steq(const char *name, const char *key, const char **next)`: Compare start of name with key. Returns 1 if match.
- `int settings_name_next(const char *name, const char **next)`: Find number of characters before the first separator (`/`).

---

## Return Values

| Value | Meaning |
|-------|---------|
| `0` | Success |
| `-EINVAL` | Invalid argument (size mismatch, bad params) |
| `-ENOENT` | Key not found |
| `-ENOSPC` | No space (flash full) |
| `-EIO` | I/O error |
| `-ENOTSUP` | Feature not enabled |
| `-ENODEV` | Backend not initialized |
