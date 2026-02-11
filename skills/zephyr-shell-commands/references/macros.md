# Zephyr Shell Macros

This reference document covers the macros provided by `shell.h` for registering commands, subcommands, and managing shell behavior.

## Root Command Registration

These macros register a command at the top level of the shell.

### `SHELL_CMD_REGISTER(syntax, subcmd, help, handler)`
Registers a root command without argument validation.
- **syntax**: Command name (string).
- **subcmd**: Pointer to a subcommand set (created via `SHELL_STATIC_SUBCMD_SET_CREATE`) or `NULL`.
- **help**: Help string displayed by the `help` command.
- **handler**: Function pointer to the command handler of type `shell_cmd_handler`.

### `SHELL_CMD_ARG_REGISTER(syntax, subcmd, help, handler, mandatory, optional)`
Registers a root command with argument validation.
- **syntax**: Command name (string).
- **subcmd**: Pointer to subcommands or `NULL`.
- **help**: Help string.
- **handler**: Command handler.
- **mandatory**: Number of mandatory arguments. **Note**: This count includes the command name itself. (e.g., `mandatory=2` means the command + 1 required argument).
- **optional**: Number of optional arguments.

### `SHELL_COND_CMD_REGISTER(flag, syntax, subcmd, help, handler)`
Conditionally registers a root command based on a Kconfig flag or macro existence.
- **flag**: If the flag evaluates to true (non-zero), the command is registered.

### `SHELL_COND_CMD_ARG_REGISTER(flag, syntax, subcmd, help, handler, mandatory, optional)`
Conditionally registers a root command with argument validation.

---

## Subcommand Creation

Macros used to define sets of subcommands.

### `SHELL_STATIC_SUBCMD_SET_CREATE(name, ...)`
Creates a static set of subcommands.
- **name**: The name of the subcommand set variable.
- **...**: A list of subcommand entries (e.g., `SHELL_CMD`, `SHELL_CMD_ARG`).
- **Note**: Must always be terminated with `SHELL_SUBCMD_SET_END`.

### `SHELL_SUBCMD_SET_CREATE(_name, _parent)`
Creates a subcommand set that can be extended using `SHELL_SUBCMD_ADD`.
- **_name**: Name of the set.
- **_parent**: Parent command name.

### `SHELL_SUBCMD_ADD(_parent, _syntax, _subcmd, _help, _handler, _mand, _opt)`
Adds a subcommand to a set created via `SHELL_SUBCMD_SET_CREATE`.
- **_parent**: Name of the parent subcommand set.
- **_syntax**: Subcommand name.
- **_subcmd**: Pointer to further subcommands or `NULL`.
- **_mand**: Mandatory arguments (including subcommand name).
- **_opt**: Optional arguments.

### `SHELL_SUBCMD_COND_ADD(_flag, _parent, _syntax, _subcmd, _help, _handler, _mand, _opt)`
Conditionally adds a subcommand to a set.

### `SHELL_SUBCMD_SET_END`
Mandatory terminator for `SHELL_STATIC_SUBCMD_SET_CREATE`.

---

## Subcommand Entries

Macros used within `SHELL_STATIC_SUBCMD_SET_CREATE` to define individual subcommands.

### `SHELL_CMD(syntax, subcmd, help, handler)`
Defines a subcommand entry without argument validation.

### `SHELL_CMD_ARG(syntax, subcmd, help, handler, mand, opt)`
Defines a subcommand entry with argument validation.
- **mand**: Mandatory arguments (including subcommand name).

### `SHELL_COND_CMD(flag, syntax, subcmd, help, handler)`
Conditionally defines a subcommand entry.

### `SHELL_COND_CMD_ARG(flag, syntax, subcmd, help, handler, mand, opt)`
Conditionally defines a subcommand entry with argument validation.

### `SHELL_EXPR_CMD(expr, syntax, subcmd, help, handler)`
Defines a subcommand entry that is enabled if `expr` is true at runtime.

### `SHELL_EXPR_CMD_ARG(expr, syntax, subcmd, help, handler, mand, opt)`
Defines a subcommand entry with runtime expression check and argument validation.

---

## Dynamic and Dictionary Commands

### `SHELL_DYNAMIC_CMD_CREATE(name, get)`
Creates a dynamic subcommand set.
- **name**: Name of the set.
- **get**: Function pointer to a function that returns a subcommand at a given index.

### `SHELL_SUBCMD_DICT_SET_CREATE(name, handler, ...)`
Creates a dictionary subcommand set. All subcommands in this set share the same handler, but pass a different value (from the dictionary) to it.
- **...**: List of dictionary entries: `(syntax, value, help)`.

---

## Helper Macros

### `SHELL_HELP(description, usage)`
Defines a help structure for a command.
- **description**: Brief description.
- **usage**: Detailed usage string.

---

## Constants

Special values used in `mandatory` or `optional` argument counts.

### `SHELL_OPT_ARG_RAW` (0xFE)
If used as the value for `optional` arguments, the shell will treat all remaining characters in the command line as a single, raw string and pass it as the last argument in `argv`.

### `SHELL_OPT_ARG_CHECK_SKIP` (0xFF)
Used to skip argument validation for optional arguments, allowing an unlimited number.

### `SHELL_OPT_ARG_MAX` (0xFD)
The maximum number of optional arguments that can be validated.

---

## Argument Counting Note

For all macros involving `mandatory` and `optional` arguments:
- **Mandatory count**: Includes the command (or subcommand) name itself.
- **Example**: A command `log level <val>` where `val` is required:
  - `mandatory = 2` (one for `level`, one for `<val>`)
  - `optional = 0`

## Example Usage

```c
static int cmd_demo_ping(const struct shell *sh, size_t argc, char **argv) {
    shell_print(sh, "pong");
    return 0;
}

static int cmd_demo_echo(const struct shell *sh, size_t argc, char **argv) {
    shell_print(sh, "%s", argv[1]);
    return 0;
}

/* Define subcommands */
SHELL_STATIC_SUBCMD_SET_CREATE(sub_demo,
    SHELL_CMD(ping, NULL, "Ping command", cmd_demo_ping),
    /* mandatory=2: 'echo' + 1 arg */
    SHELL_CMD_ARG(echo, NULL, "Echo command", cmd_demo_echo, 2, 0),
    SHELL_SUBCMD_SET_END
);

/* Register root command */
SHELL_CMD_REGISTER(demo, &sub_demo, "Demo commands", NULL);
```
