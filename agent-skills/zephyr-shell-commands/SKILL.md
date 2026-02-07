---
name: zephyr-shell-commands
description: Expert guidance on using and creating shell commands in Zephyr OS. Use this skill when the user wants to implement new CLI commands, debug existing shell commands, or understand the Zephyr Shell API.
---

# Zephyr Shell Commands

This skill provides expert knowledge on the Zephyr Shell subsystem, allowing you to create custom commands, manage subcommands, and interact with the user via the console.

## Usage

When creating shell commands, always follow these steps:

1.  **Define the Handler**: Create a function matching `shell_cmd_handler`.
2.  **Define Subcommands (Optional)**: Use `SHELL_STATIC_SUBCMD_SET_CREATE` for nested commands.
3.  **Register the Command**: Use `SHELL_CMD_REGISTER` or `SHELL_CMD_ARG_REGISTER`.

## References

*   **[Macros](references/macros.md)**: Syntax for registering commands and subcommands.
*   **[API](references/api.md)**: Functions for printing and interacting with the shell.
*   **[Advanced](references/advanced.md)**: Dictionary commands, dynamic commands, and argument validation.

## Best Practices

*   **Use `shell_print`**: Never use `printk` in shell handlers.
*   **Argument Validation**: Use `SHELL_CMD_ARG_REGISTER` to enforce argument counts automatically.
*   **Help Strings**: Provide clear, concise help strings for all commands.
*   **Return Codes**: Return `0` on success, or a negative error code (like `-EINVAL`) on failure.
