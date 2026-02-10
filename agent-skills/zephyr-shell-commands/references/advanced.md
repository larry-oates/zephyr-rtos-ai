# Advanced Shell Usage

This document covers advanced Zephyr shell features, including dynamic command generation, dictionary-based subcommands, modular registration, and custom backends.

## Dynamic Commands

Dynamic commands are determined at runtime. This is useful for commands that depend on the current state of the system, such as listing available devices, files, or active threads.

### Purpose
Commands whose subcommands are not known at compile time or change during execution (e.g., listing connected BLE peers or mounted filesystems).

### Callback Signature
The dynamic command system relies on a callback that retrieves command entries by index.

```c
void (*shell_dynamic_get)(size_t idx, struct shell_static_entry *entry);
```

### Key Requirements
- **Populating `shell_static_entry`**: The callback should fill the `entry` pointer with the syntax, handler, subcommands, and help text for the given `idx`.
- **Alphabetical Sorting**: The entries returned by the callback MUST be sorted alphabetically to allow the shell to perform binary searches for completion and execution.
- **NULL Termination**: When `idx` is out of range, the callback must set `entry->syntax` to `NULL` to signify the end of the list.

### Example: Device Enumeration
```c
#include <zephyr/shell/shell.h>
#include <zephyr/device.h>

static void device_name_get(size_t idx, struct shell_static_entry *entry)
{
    const struct device *dev = shell_device_lookup(idx, NULL);

    if (dev != NULL) {
        entry->syntax = dev->name;
        entry->handler = NULL;
        entry->subcmd = NULL;
        entry->help = "Device name";
    } else {
        entry->syntax = NULL;
    }
}

SHELL_DYNAMIC_CMD_CREATE(dsub_device_name, device_name_get);
SHELL_CMD_REGISTER(device, &dsub_device_name, "Device commands", NULL);
```

---

## Dictionary Commands

Dictionary commands map string syntax to specific data values (integers or pointers). They are ideal for "set" style commands where you want to provide a fixed list of named options.

### Purpose
Simplifying handlers that would otherwise require multiple `strcmp` calls to map a string argument to a configuration value.

### Macro
```c
SHELL_SUBCMD_DICT_SET_CREATE(name, handler, (syntax, value, help), ...);
```

### Handler Prototype
Dictionary handlers receive an extra `void *data` parameter containing the value associated with the chosen syntax.

```c
int (*shell_dict_cmd_handler)(const struct shell *sh, size_t argc, char **argv, void *data);
```

### Triplet Format
The macro takes triplets in the form `(syntax, value, help)`.
- `syntax`: The string the user types.
- `value`: The data (cast to `void *`) passed to the handler.
- `help`: Help string for this specific option.

### Example: Gain Settings
```c
static int gain_handler(const struct shell *sh, size_t argc, char **argv, void *data)
{
    /* Data is passed as the value defined in the triplet */
    int value = (intptr_t)data;
    shell_print(sh, "Setting gain to: %d", value);
    return 0;
}

SHELL_SUBCMD_DICT_SET_CREATE(sub_gain, gain_handler,
    (low, 1, "Low gain (1x)"),
    (medium, 5, "Medium gain (5x)"),
    (high, 10, "High gain (10x)")
);

SHELL_CMD_REGISTER(gain, &sub_gain, "Configure gain", NULL);
```

---

## Distributed Subcommand Registration

Distributed registration allows subcommands to be defined in different source files, facilitating modularity without modifying a central command list.

### Usage Pattern
1.  **Define the Set**: Create an extensible subcommand set in a header or common file.
    ```c
    SHELL_SUBCMD_SET_CREATE(extensible_subcmds, (parent_command));
    ```
2.  **Add Commands**: Use `SHELL_SUBCMD_ADD` or `SHELL_SUBCMD_COND_ADD` in any compilation unit.
    ```c
    /* In sensor_a.c */
    SHELL_SUBCMD_ADD(extensible_subcmds, sensor_a, NULL, "Sensor A help", handler_a, 1, 0);

    /* In sensor_b.c */
    SHELL_SUBCMD_COND_ADD(CONFIG_SENSOR_B, extensible_subcmds, sensor_b, NULL, "Sensor B help", handler_b, 1, 0);
    ```

### Use Case
A "sensor" command where different drivers can register their own subcommands (`sensor read sensor_a`, `sensor read sensor_b`) only if the driver is enabled in Kconfig.

---

## Argument Parsing

The shell provides several mechanisms for handling and validating arguments.

### Special Constants
- `SHELL_OPT_ARG_RAW`: If used as the number of optional arguments, all remaining text after the mandatory arguments is passed as a single string in `argv[mandatory]`. This is useful for `echo`-like commands.
- `SHELL_OPT_ARG_CHECK_SKIP`: Disables the shell's built-in argument count checking for that command, allowing the handler to perform custom validation.

### Parsing Techniques
- **Standard Parsing**: Use `strtol`, `strtoul`, or `strtobool` for numeric and boolean parsing.
- **Parent Context**: To access the parent command name, use `argv[-1]`.
- **Getopt Support**: If `CONFIG_SHELL_GETOPT` is enabled, you can use `getopt` for complex flag parsing.

```c
static int cmd_complex(const struct shell *sh, size_t argc, char **argv)
{
    int c;
    /* argv[0] is the command name, so getopt starts at index 1 */
    while ((c = getopt(argc, argv, "ab:")) != -1) {
        switch (c) {
        case 'a': /* handle flag a */ break;
        case 'b': /* handle optarg */ break;
        }
    }
    return 0;
}
```

---

## Structured Help

Structured help ensures consistent formatting and allows the shell to programmatically query command usage.

### Purpose
Provides a standardized way to define multi-line descriptions and usage strings that the shell can format appropriately for the terminal width.

### Macro Syntax
```c
SHELL_HELP(description, usage)
```

### Functions
- `shell_help_is_structured()`: Can be used within a handler to check if the help provided is in the structured format.

### Example
```c
#define MY_HELP SHELL_HELP( \
    "This is a multi-line description of the command.\n" \
    "It explains what the command does in detail.", \
    "usage: <arg1> [arg2]" \
)

SHELL_CMD_REGISTER(mycmd, NULL, MY_HELP, cmd_handler);
```

---

## Shell Bypass Mode

Bypass mode allows a callback to take direct control of the shell's input stream, bypassing the command processor.

### Purpose
Handling raw data transfers, implementing terminal emulators, or supporting special protocols like XMODEM/YMODEM where binary data would otherwise trigger shell control sequences.

### API and Callback
```c
void shell_set_bypass(const struct shell *sh, shell_bypass_cb_t cb);

/* Callback signature */
void (*shell_bypass_cb_t)(const struct shell *sh, uint8_t *data, size_t len);
```

### Use Case
A command like `transfer_file` that sets a bypass callback to receive raw bytes until a termination sequence is detected, then restores normal shell operation by calling `shell_set_bypass(sh, NULL)`.

---

## Conditional Commands

Commands can be included or excluded at compile-time based on Kconfig options or arbitrary expressions, reducing code size for unused features.

- `SHELL_COND_CMD` / `SHELL_COND_CMD_ARG`: Include command if a Kconfig option is `y`.
- `SHELL_EXPR_CMD` / `SHELL_EXPR_CMD_ARG`: Include command if a C expression evaluates to true.

```c
/* Only included if CONFIG_STATS is enabled */
SHELL_COND_CMD(CONFIG_STATS, stats, NULL, "Show statistics", cmd_stats);

/* Only included on 64-bit architectures */
SHELL_EXPR_CMD(sizeof(void *) == 8, arch64, NULL, "64-bit specific", cmd_64);
```

---

## Custom Shell Backends

You can define custom transport backends (e.g., Bluetooth, SPI, custom hardware) by implementing the `shell_transport_api`.

### Required API Callbacks
A backend must provide a `struct shell_transport_api` with:
- `init` / `uninit`: Life-cycle management.
- `enable`: Activate the backend.
- `write`: Send data from shell to backend.
- `read`: Receive data from backend to shell.
- `update`: Optional periodic maintenance.

### Implementation Macro
Use `SHELL_DEFINE` to create a shell instance tied to your custom transport.

```c
struct my_transport_ctx { ... };
const struct shell_transport_api my_api = { ... };

#define MY_SHELL_DEFINE(_name) \
    static struct my_transport_ctx _name##_ctx; \
    static struct shell_transport _name##_transport = { \
        .api = &my_api, \
        .ctx = &_name##_ctx \
    }; \
    SHELL_DEFINE(_name, "prompt> ", &_name##_transport, 10, 0, SHELL_FLAG_USE_COLORS)
```
