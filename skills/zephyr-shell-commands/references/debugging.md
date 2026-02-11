# Debugging and Troubleshooting Zephyr Shell

## Common Build Errors

### Undefined Reference to Shell Commands
**Error:** `undefined reference to __shell_root_cmds_start` or similar linker errors.
**Cause:** Shell subsystem is not properly initialized or no commands are registered.
**Solution:** Ensure `CONFIG_SHELL=y` is enabled in `prj.conf`.

### Missing Header File
**Error:** `fatal error: zephyr/shell/shell.h: No such file or directory`
**Cause:** The shell header is included but the shell subsystem is not enabled in Kconfig.
**Solution:** Add `CONFIG_SHELL=y` to your configuration.

### Duplicate Command Names
**Error:** No build error, but only one command appears or system behaves unexpectedly.
**Cause:** Multiple calls to `SHELL_CMD_REGISTER` or `SHELL_SUBCMD_SET_CREATE` using the same command name at the same level.
**Solution:** Ensure every command and sub-command name is unique within its parent context.

## Runtime Issues

### Command Not Appearing in Help
**Issue:** Command is registered in code but does not show up when typing `help`.
**Checklist:**
1. Verify `CONFIG_SHELL=y` is in the final `.config`.
2. Ensure the file containing `SHELL_CMD_REGISTER` is actually being compiled (check `CMakeLists.txt`).
3. Check if the command is conditional on a Kconfig that is disabled.

### Wrong Argument Count
**Issue:** Command returns "Invalid number of arguments" or similar.
**Cause:** The `min_args` and `max_args` parameters in `SHELL_CMD_ARG_REGISTER` do not match the input.
**Solution:**
- `min_args`: Minimum arguments including the command name itself.
- `max_args`: Maximum arguments including the command name itself.

### Output Not Visible
**Issue:** `shell_print()` or `shell_fprintf()` calls execute but nothing appears on the console.
**Cause:**
1. Incorrect shell backend configuration (e.g., `CONFIG_SHELL_BACKEND_UART` vs `CONFIG_SHELL_BACKEND_RTT`).
2. Logging level is suppressing output if the shell is integrated with the logger.
3. The shell thread has lower priority than a CPU-bound thread.
**Solution:** Verify backend settings and check if other shell output (like the prompt) is visible.

## Debugging Techniques

### Checking .config
Always verify the generated configuration in the build directory:
```bash
grep CONFIG_SHELL build/zephyr/.config
```

### Using Shell Statistics
If `CONFIG_SHELL_STATS=y` is enabled, use the built-in stats command to monitor shell behavior:
```bash
shell stats show
```

### Verifying Backend
Ensure the physical transport is working.
For UART:
```kconfig
CONFIG_SHELL_BACKEND_SERIAL=y
CONFIG_UART_CONSOLE=y
```
For RTT:
```kconfig
CONFIG_SHELL_BACKEND_RTT=y
CONFIG_USE_SEGGER_RTT=y
```

## Kconfig Verification

### Required Base Options
Ensure these are set for a functional shell:
- `CONFIG_SHELL=y`: Enables the shell subsystem.
- `CONFIG_SHELL_BACKENDS=y`: Enables shell backends.
- `CONFIG_SHELL_BACKEND_SERIAL=y`: Typical for physical console access.

### Troubleshooting Dependencies
The shell requires `CONFIG_MULTITHREADING=y`. If multithreading is disabled, the shell subsystem will not function as it relies on its own thread.

## Best Practices for Debugging

1. **Simplify Commands**: Test with a basic `SHELL_CMD_REGISTER` without subcommands or complex arguments first.
2. **Check Return Codes**: Command handlers should return `0` on success.
3. **Use Dummy Backend**: Use `CONFIG_SHELL_BACKEND_DUMMY=y` to verify shell logic without hardware dependencies.
4. **Stack Size**: If a command causes a crash or stack overflow, increase `CONFIG_SHELL_STACK_SIZE`.
