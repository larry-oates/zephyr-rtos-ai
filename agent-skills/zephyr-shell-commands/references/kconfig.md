# Shell Kconfig Options

Complete reference for Zephyr Shell subsystem Kconfig configuration options.

## Table of Contents

1. [Essential Options](#essential-options)
2. [Backend Options](#backend-options)
3. [Feature Options](#feature-options)
4. [Memory Optimization](#memory-optimization)
5. [Built-in Commands](#built-in-commands)

---

## Essential Options

### Core Shell

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `CONFIG_SHELL` | bool | n | Enable the shell subsystem |
| `CONFIG_SHELL_THREAD_PRIORITY_OVERRIDE` | bool | n | Override default shell thread priority |
| `CONFIG_SHELL_STACK_SIZE` | int | 2048 | Shell thread stack size |

### Prompt Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `CONFIG_SHELL_PROMPT_UART` | string | "uart:~$" | Default shell prompt |
| `CONFIG_SHELL_PROMPT_BUFF_SIZE` | int | 32 | Prompt buffer size |

---

## Backend Options

### UART Backend (Most Common)

```kconfig
CONFIG_SHELL=y
CONFIG_SHELL_BACKEND_SERIAL=y
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `CONFIG_SHELL_BACKEND_SERIAL` | bool | y | Enable UART/serial backend |
| `CONFIG_SHELL_BACKEND_SERIAL_INIT_PRIORITY` | int | 0 | Initialization priority |
| `CONFIG_SHELL_BACKEND_SERIAL_INTERRUPT_DRIVEN` | bool | y | Use interrupt-driven UART |

### RTT Backend (Segger J-Link)

```kconfig
CONFIG_USE_SEGGER_RTT=y
CONFIG_SHELL_BACKEND_RTT=y
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `CONFIG_SHELL_BACKEND_RTT` | bool | n | Enable RTT backend |
| `CONFIG_SHELL_BACKEND_RTT_BUFFER` | int | 0 | RTT buffer/channel index |

### USB CDC ACM Backend

Use snippet `cdc-acm-console`:
```bash
west build -S cdc-acm-console [...]
```

### Telnet Backend

```kconfig
CONFIG_SHELL_BACKEND_TELNET=y
CONFIG_NETWORKING=y
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `CONFIG_SHELL_BACKEND_TELNET` | bool | n | Enable Telnet backend |
| `CONFIG_SHELL_TELNET_PORT` | int | 23 | Telnet port number |
| `CONFIG_SHELL_TELNET_SUPPORT_COMMAND` | bool | n | Handle telnet commands |

### Bluetooth LE NUS Backend

Use snippet `nus-console`:
```bash
west build -S nus-console [...]
```

### Dummy Backend (Testing)

```kconfig
CONFIG_SHELL_BACKEND_DUMMY=y
```

Useful for executing shell commands programmatically without physical transport.

---

## Feature Options

### Tab Completion

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `CONFIG_SHELL_TAB` | bool | y | Enable Tab key functionality |
| `CONFIG_SHELL_TAB_AUTOCOMPLETION` | bool | y | Enable auto-completion |

### Command History

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `CONFIG_SHELL_HISTORY` | bool | y | Enable command history |
| `CONFIG_SHELL_HISTORY_BUFFER` | int | 128 | History buffer size (bytes) |

### Wildcards

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `CONFIG_SHELL_WILDCARD` | bool | y | Enable wildcard support (`*`, `?`) |

### Meta Keys

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `CONFIG_SHELL_METAKEYS` | bool | y | Enable Ctrl+key shortcuts |

### VT100 / Colors

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `CONFIG_SHELL_VT100_COLORS` | bool | y | Enable colored output |
| `CONFIG_SHELL_VT100_COMMANDS` | bool | y | Enable VT100 escape sequences |

### Getopt Support

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `CONFIG_SHELL_GETOPT` | bool | n | Thread-safe getopt for shell |

Requires:
```kconfig
CONFIG_POSIX_C_LIB_EXT=y
CONFIG_GETOPT_LONG=y
```

### Help System

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `CONFIG_SHELL_HELP` | bool | y | Enable help for commands (`-h`, `--help`) |
| `CONFIG_SHELL_HELP_ON_WRONG_ARGUMENT_COUNT` | bool | y | Print help when args wrong |

---

## Memory Optimization

### Minimal Shell Configuration

For resource-constrained devices, enable minimal mode:

```kconfig
CONFIG_SHELL_MINIMAL=y
```

This disables many features by default. Selectively re-enable what you need:

```kconfig
CONFIG_SHELL_MINIMAL=y
CONFIG_SHELL_HISTORY=n
CONFIG_SHELL_WILDCARD=n
CONFIG_SHELL_METAKEYS=n
CONFIG_SHELL_TAB_AUTOCOMPLETION=n
CONFIG_SHELL_VT100_COLORS=n
```

### Buffer Sizes

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `CONFIG_SHELL_CMD_BUFF_SIZE` | int | 128 | Command buffer size |
| `CONFIG_SHELL_PRINTF_BUFF_SIZE` | int | 30 | Printf buffer size |
| `CONFIG_SHELL_ARGC_MAX` | int | 12 | Maximum argument count |

---

## Built-in Commands

### Enable/Disable Built-in Commands

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `CONFIG_SHELL_CMDS` | bool | y | Enable built-in commands (clear, history, etc.) |
| `CONFIG_SHELL_CMDS_RESIZE` | bool | n | Enable `resize` command |
| `CONFIG_SHELL_CMDS_SELECT` | bool | n | Enable `select` command (set root) |

### Available Built-in Commands

When `CONFIG_SHELL_CMDS=y`:
- `clear` - Clear screen
- `history` - Show command history
- `shell` - Shell configuration subcommands
  - `echo` - Toggle echo
  - `colors` - Toggle colored output
  - `stats` - Show shell statistics

---

## Logging Integration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `CONFIG_SHELL_LOG_BACKEND` | bool | y | Shell as logging backend |
| `CONFIG_SHELL_LOG_LEVEL` | int | 3 (INFO) | Default log level for shell |

**Warning**: Shell is a complex logger backend. For early boot debugging, use simpler backends like `CONFIG_LOG_BACKEND_UART`.

---

## Example Configurations

### Full-Featured Development

```kconfig
CONFIG_SHELL=y
CONFIG_SHELL_BACKEND_SERIAL=y
CONFIG_SHELL_TAB=y
CONFIG_SHELL_TAB_AUTOCOMPLETION=y
CONFIG_SHELL_HISTORY=y
CONFIG_SHELL_HISTORY_BUFFER=512
CONFIG_SHELL_WILDCARD=y
CONFIG_SHELL_METAKEYS=y
CONFIG_SHELL_VT100_COLORS=y
CONFIG_SHELL_CMDS=y
CONFIG_SHELL_LOG_BACKEND=y
```

### Minimal Production

```kconfig
CONFIG_SHELL=y
CONFIG_SHELL_MINIMAL=y
CONFIG_SHELL_BACKEND_SERIAL=y
CONFIG_SHELL_HISTORY=n
CONFIG_SHELL_WILDCARD=n
CONFIG_SHELL_VT100_COLORS=n
CONFIG_SHELL_STACK_SIZE=1024
CONFIG_SHELL_CMD_BUFF_SIZE=64
```

### RTT for Debugging

```kconfig
CONFIG_USE_SEGGER_RTT=y
CONFIG_SHELL=y
CONFIG_SHELL_BACKEND_RTT=y
CONFIG_SHELL_BACKEND_SERIAL=n
CONFIG_RTT_CONSOLE=n
```
