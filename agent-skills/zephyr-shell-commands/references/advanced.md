# Advanced Shell Usage

## Dictionary Commands

Dictionary commands map a string syntax to a data value (integer or pointer). Useful for commands like `set_gain <value>` where `<value>` is a specific string like `low`, `medium`, `high`.

### Macro

`SHELL_SUBCMD_DICT_SET_CREATE(name, handler, ...)`

### Example

```c
static int gain_cmd_handler(const struct shell *sh, size_t argc, char **argv, void *data) {
    int gain = (intptr_t)data;
    shell_print(sh, "Gain set to %d", gain);
    return 0;
}

SHELL_SUBCMD_DICT_SET_CREATE(sub_gain, gain_cmd_handler,
    (low, 1, "Low gain"),
    (high, 2, "High gain")
);

SHELL_CMD_REGISTER(gain, &sub_gain, "Set gain", NULL);
```

## Dynamic Commands

Dynamic commands allow adding or removing commands at runtime.

### Key Macros/Types

*   `SHELL_DYNAMIC_CMD_CREATE(name, get_func)`
*   `typedef void (*shell_dynamic_get)(size_t idx, struct shell_static_entry *entry)`

## Argument Validation

When using `SHELL_CMD_ARG` or `SHELL_CMD_ARG_REGISTER`, you specify `mandatory` and `optional` argument counts.

*   `mandatory`: Includes the command itself. So `mycmd arg1` has 2 mandatory args.
*   If `argc` doesn't match, the handler is **not called** and help is printed.
*   Use `SHELL_OPT_ARG_RAW` as `optional` count to treat remaining arguments as a single raw string.

## Parsing Arguments

*   Standard `strtol`, `strtoul` can be used.
*   `shell_strtoul` and similar helpers (if available) or standard `stdlib` functions.
*   Backends like `getopt` are supported if configured (`CONFIG_SHELL_GETOPT`).
