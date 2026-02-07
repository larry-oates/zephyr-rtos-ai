# Zephyr Shell Macros

## Command Registration Macros

These macros are used to register commands with the Zephyr shell subsystem.

### Root Commands

*   `SHELL_CMD_REGISTER(syntax, subcmd, help, handler)`: Register a root command.
    *   `syntax`: Command name (string).
    *   `subcmd`: Pointer to a subcommand set (or `NULL`).
    *   `help`: Help string.
    *   `handler`: Function pointer to the command handler (or `NULL` if it only has subcommands).

*   `SHELL_COND_CMD_REGISTER(flag, syntax, subcmd, help, handler)`: Conditionally register a root command based on a Kconfig flag.

*   `SHELL_CMD_ARG_REGISTER(syntax, subcmd, help, handler, mandatory, optional)`: Register a root command with argument counting.
    *   `mandatory`: Number of mandatory arguments.
    *   `optional`: Number of optional arguments.

### Subcommands

*   `SHELL_STATIC_SUBCMD_SET_CREATE(name, ...)`: Define a set of static subcommands.
    *   `name`: The name of the subcommand set variable.
    *   `...`: List of `SHELL_CMD` or `SHELL_CMD_ARG` entries.
    *   Must end with `SHELL_SUBCMD_SET_END`.

*   `SHELL_CMD(syntax, subcmd, help, handler)`: Define a subcommand entry.

*   `SHELL_CMD_ARG(syntax, subcmd, help, handler, mandatory, optional)`: Define a subcommand entry with argument validation.

### Example

```c
static int cmd_demo_ping(const struct shell *sh, size_t argc, char **argv) {
    shell_print(sh, "pong");
    return 0;
}

SHELL_STATIC_SUBCMD_SET_CREATE(sub_demo,
    SHELL_CMD(ping, NULL, "Ping command", cmd_demo_ping),
    SHELL_SUBCMD_SET_END
);

SHELL_CMD_REGISTER(demo, &sub_demo, "Demo commands", NULL);
```
