# Zephyr Shell API

## Output Functions

Use these functions to print to the shell. Do **not** use `printk` or `printf` within shell handlers as they may bypass the shell backend or interfere with the prompt.

*   `shell_print(sh, fmt, ...)`: Print a message with a newline.
*   `shell_info(sh, fmt, ...)`: Print an informational message (green).
*   `shell_warn(sh, fmt, ...)`: Print a warning message (yellow).
*   `shell_error(sh, fmt, ...)`: Print an error message (red).
*   `shell_fprintf(sh, color, fmt, ...)`: Print a formatted message with a specific color.
    *   Colors: `SHELL_NORMAL`, `SHELL_INFO`, `SHELL_OPTION`, `SHELL_WARNING`, `SHELL_ERROR`.

## Hexdump

*   `shell_hexdump(sh, data, len)`: Print a hexdump of a data buffer.

## Helper Functions

*   `shell_help(sh)`: Print the help message for the current command.
*   `shell_execute_cmd(sh, cmd)`: Execute a command string programmatically.

## Handler Prototype

```c
typedef int (*shell_cmd_handler)(const struct shell *sh, size_t argc, char **argv);
```

*   `sh`: Pointer to the shell instance.
*   `argc`: Argument count.
*   `argv`: Argument vector. `argv[0]` is the command name itself.

## Return Values

*   `0`: Success.
*   `-EINVAL`: Invalid argument.
*   `-ENOEXEC`: Command execution failed.
