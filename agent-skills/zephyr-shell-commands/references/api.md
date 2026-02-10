# Zephyr Shell API Reference

The shell pointer (`const struct shell *sh`) passed to command handlers provides access to these API functions for interaction and control.

> **CRITICAL RULE:** NEVER use `printk()` or `printf()` inside shell handlers. These functions bypass the shell backend, can corrupt the input line, and may not go to the same transport (e.g., if using shell over BLE or Telnet). ALWAYS use `shell_print()` and its variants.

## Output Functions

### shell_print
Prints a formatted message followed by a newline.
- **Parameters:**
  - `sh`: Pointer to the shell instance.
  - `fmt`: Format string (printf style).
  - `...`: Arguments for the format string.
- **Return Value:** None.

### shell_info
Prints an informational message in green.
- **Parameters:**
  - `sh`: Pointer to the shell instance.
  - `fmt`: Format string.
- **Return Value:** None.

### shell_warn
Prints a warning message in yellow.
- **Parameters:**
  - `sh`: Pointer to the shell instance.
  - `fmt`: Format string.
- **Return Value:** None.

### shell_error
Prints an error message in red.
- **Parameters:**
  - `sh`: Pointer to the shell instance.
  - `fmt`: Format string.
- **Return Value:** None.

### shell_fprintf
Prints a formatted message with a specific color.
- **Parameters:**
  - `sh`: Pointer to the shell instance.
  - `color`: Color code (see [Colors](#colors)).
  - `fmt`: Format string.
- **Return Value:** None.

### shell_vfprintf
The `vprintf` variant of `shell_fprintf`.
- **Parameters:**
  - `sh`: Pointer to the shell instance.
  - `color`: Color code.
  - `fmt`: Format string.
  - `args`: Variable arguments list (`va_list`).
- **Return Value:** None.

### shell_hexdump
Prints a hex dump of a data buffer.
- **Parameters:**
  - `sh`: Pointer to the shell instance.
  - `data`: Pointer to the data to dump.
  - `len`: Length of the data.
- **Return Value:** None.

### shell_hexdump_line
Prints a single line of a hex dump.
- **Parameters:**
  - `sh`: Pointer to the shell instance.
  - `offset`: Offset to print at the start of the line.
  - `data`: Pointer to the data.
  - `len`: Length of the data to print in this line.
- **Return Value:** None.

## Colors
Used with `shell_fprintf` and `shell_vfprintf`.
- `SHELL_NORMAL`: Default text color.
- `SHELL_INFO`: Green (Information).
- `SHELL_OPTION`: Cyan (Options).
- `SHELL_WARNING`: Yellow (Warning).
- `SHELL_ERROR`: Red (Error).

## Command Execution & Help

### shell_help
Prints the help message for the current command context.
- **Parameters:** `sh`: Shell instance pointer.
- **Return Value:** None.
- **Usage:** Typically used when `argc` is incorrect or a `-h` flag is detected.

### shell_execute_cmd
Programmatically executes a shell command string.
- **Parameters:**
  - `sh`: Shell instance pointer (can be NULL to use default).
  - `cmd`: The command string to execute.
- **Return Value:** `0` on success, or error code.

## Device Functions
Helpers for shell commands that interact with system devices.

### shell_device_get_binding
Get a device binding by name, but only if the device is ready.
- **Parameters:** `name`: Device name string.
- **Return Value:** Pointer to `struct device` or `NULL`.

### shell_device_get_binding_all
Get a device binding by name, including devices that are not ready.
- **Parameters:** `name`: Device name string.
- **Return Value:** Pointer to `struct device` or `NULL`.

### shell_device_lookup
Look up a device by index, filtered by a name prefix (ready devices only).
- **Parameters:**
  - `idx`: Device index.
  - `prefix`: Name prefix to filter by.
- **Return Value:** Pointer to `struct device` or `NULL`.

### shell_device_lookup_all
Look up any device by index with a prefix filter.
- **Parameters:**
  - `idx`: Device index.
  - `prefix`: Name prefix to filter by.
- **Return Value:** Pointer to `struct device` or `NULL`.

### shell_device_lookup_non_ready
Look up only non-ready devices by index with a prefix filter.
- **Parameters:**
  - `idx`: Device index.
  - `prefix`: Name prefix to filter by.
- **Return Value:** Pointer to `struct device` or `NULL`.

### shell_device_filter
Look up a device by index using a custom filter function.
- **Parameters:**
  - `idx`: Device index.
  - `filter`: Function pointer to a filter `bool (*)(const struct device *dev)`.
- **Return Value:** Pointer to `struct device` or `NULL`.

## Shell Control

### shell_prompt_change
Changes the prompt for the specified shell instance.
- **Parameters:**
  - `sh`: Shell instance.
  - `prompt`: New prompt string.
- **Return Value:** None.

### shell_set_bypass
Sets a bypass callback to handle raw input data directly.
- **Parameters:**
  - `sh`: Shell instance.
  - `bypass`: Function of type `shell_bypass_cb_t`.
- **Return Value:** None.

### shell_ready
Checks if the shell is ready to accept commands.
- **Parameters:** `sh`: Shell instance.
- **Return Value:** `true` if ready, `false` otherwise.

### shell_set_root_cmd
Sets a root command that will be active for all shell instances.
- **Parameters:** `cmd`: Pointer to a static command entry.
- **Return Value:** None.

### shell_get_return_value
Gets the return value of the last executed command.
- **Parameters:** `sh`: Shell instance.
- **Return Value:** Last command's integer return value.

## Configuration
Modify shell behavior at runtime.

- `shell_insert_mode_set(sh, val)`: Enable/disable insert mode.
- `shell_use_colors_set(sh, val)`: Enable/disable ANSI color output.
- `shell_use_vt100_set(sh, val)`: Enable/disable VT100 terminal support.
- `shell_echo_set(sh, val)`: Enable/disable local echo.
- `shell_obscure_set(sh, obscure)`: Enable/disable obscuring input (e.g., for passwords).
- `shell_mode_delete_set(sh, val)`: Change how the delete key is handled.

## Handler Prototypes

### shell_cmd_handler
Standard command handler.
```c
int (*)(const struct shell *sh, size_t argc, char **argv)
```

### shell_dict_cmd_handler
Handler for dictionary-based commands (where data is associated with the command).
```c
int (*)(const struct shell *sh, size_t argc, char **argv, void *data)
```

### shell_dynamic_get
Function used to dynamically generate subcommands or completions.
```c
void (*)(size_t idx, struct shell_static_entry *entry)
```

### shell_bypass_cb_t
Callback for bypass mode (raw data handling).
```c
void (*)(const struct shell *sh, uint8_t *data, size_t len)
```

## Return Values
Commands should return these standard values:

- `0`: Success.
- `1` (`SHELL_CMD_HELP_PRINTED`): Command requested help, and help was printed.
- `-EINVAL`: One or more arguments are invalid.
- `-ENOEXEC`: The command failed to execute or internal logic error.
