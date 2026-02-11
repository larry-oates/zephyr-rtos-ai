# Shell Command Examples

Complete working examples for common Zephyr shell command patterns.

## Table of Contents

1. [Simple Root Command](#simple-root-command)
2. [Command with Arguments](#command-with-arguments)
3. [Commands with Subcommands](#commands-with-subcommands)
4. [Device Control Commands](#device-control-commands)
5. [Dictionary Commands](#dictionary-commands)
6. [Dynamic Commands](#dynamic-commands)
7. [Conditional Commands](#conditional-commands)
8. [Commands with Getopt](#commands-with-getopt)
9. [Driver Shell Integration](#driver-shell-integration)

---

## Simple Root Command

Minimal command with no arguments.

```c
#include <zephyr/shell/shell.h>

static int cmd_version(const struct shell *sh, size_t argc, char **argv)
{
    ARG_UNUSED(argc);
    ARG_UNUSED(argv);

    shell_print(sh, "Firmware v1.0.0");
    shell_print(sh, "Build: %s %s", __DATE__, __TIME__);
    return 0;
}

SHELL_CMD_REGISTER(version, NULL, "Show firmware version", cmd_version);
```

**Usage:**
```
uart:~$ version
Firmware v1.0.0
Build: Feb 10 2026 10:30:00
```

---

## Command with Arguments

Command that validates and uses arguments.

```c
#include <zephyr/shell/shell.h>
#include <stdlib.h>

static int cmd_repeat(const struct shell *sh, size_t argc, char **argv)
{
    int count;
    int ret = 0;

    /* Parse count argument */
    count = shell_strtoul(argv[1], 10, &ret);
    if (ret != 0) {
        shell_error(sh, "Invalid count: %s", argv[1]);
        return -EINVAL;
    }

    /* Print message the specified number of times */
    for (int i = 0; i < count; i++) {
        shell_print(sh, "[%d] %s", i + 1, argv[2]);
    }

    return 0;
}

/* mandatory=3: command + count + message */
SHELL_CMD_ARG_REGISTER(repeat, NULL,
    "Repeat message N times\n"
    "Usage: repeat <count> <message>",
    cmd_repeat, 3, 0);
```

**Usage:**
```
uart:~$ repeat 3 hello
[1] hello
[2] hello
[3] hello
```

---

## Commands with Subcommands

Hierarchical command structure with subcommands.

```c
#include <zephyr/shell/shell.h>

/* Subcommand handlers */
static int cmd_led_on(const struct shell *sh, size_t argc, char **argv)
{
    shell_print(sh, "LED turned ON");
    /* gpio_pin_set_dt(&led, 1); */
    return 0;
}

static int cmd_led_off(const struct shell *sh, size_t argc, char **argv)
{
    shell_print(sh, "LED turned OFF");
    /* gpio_pin_set_dt(&led, 0); */
    return 0;
}

static int cmd_led_toggle(const struct shell *sh, size_t argc, char **argv)
{
    shell_print(sh, "LED toggled");
    /* gpio_pin_toggle_dt(&led); */
    return 0;
}

static int cmd_led_status(const struct shell *sh, size_t argc, char **argv)
{
    shell_print(sh, "LED status: ON");
    /* shell_print(sh, "LED status: %s", gpio_pin_get_dt(&led) ? "ON" : "OFF"); */
    return 0;
}

/* Create subcommand set */
SHELL_STATIC_SUBCMD_SET_CREATE(led_cmds,
    SHELL_CMD(on,     NULL, "Turn LED on",     cmd_led_on),
    SHELL_CMD(off,    NULL, "Turn LED off",    cmd_led_off),
    SHELL_CMD(toggle, NULL, "Toggle LED",      cmd_led_toggle),
    SHELL_CMD(status, NULL, "Show LED status", cmd_led_status),
    SHELL_SUBCMD_SET_END
);

/* Register root command with subcommands */
SHELL_CMD_REGISTER(led, &led_cmds, "LED control commands", NULL);
```

**Usage:**
```
uart:~$ led on
LED turned ON
uart:~$ led status
LED status: ON
uart:~$ led
led - LED control commands
Subcommands:
  on      : Turn LED on
  off     : Turn LED off
  toggle  : Toggle LED
  status  : Show LED status
```

---

## Device Control Commands

Pattern for device-specific commands.

```c
#include <zephyr/shell/shell.h>
#include <zephyr/drivers/sensor.h>

static int cmd_sensor_read(const struct shell *sh, size_t argc, char **argv)
{
    const struct device *dev;
    struct sensor_value temp;
    int ret;

    /* Get device by name from argument */
    dev = shell_device_get_binding(argv[1]);
    if (dev == NULL) {
        shell_error(sh, "Device not found: %s", argv[1]);
        return -ENODEV;
    }

    /* Sample the sensor */
    ret = sensor_sample_fetch(dev);
    if (ret < 0) {
        shell_error(sh, "Failed to fetch sample: %d", ret);
        return ret;
    }

    /* Get temperature value */
    ret = sensor_channel_get(dev, SENSOR_CHAN_AMBIENT_TEMP, &temp);
    if (ret < 0) {
        shell_error(sh, "Failed to get temperature: %d", ret);
        return ret;
    }

    shell_print(sh, "Temperature: %d.%06d C",
                temp.val1, temp.val2);
    return 0;
}

SHELL_CMD_ARG_REGISTER(sensor_read, NULL,
    "Read sensor value\n"
    "Usage: sensor_read <device_name>",
    cmd_sensor_read, 2, 0);
```

---

## Dictionary Commands

Map string values to data.

```c
#include <zephyr/shell/shell.h>

/* Handler receives data pointer with the mapped value */
static int log_level_handler(const struct shell *sh,
                             size_t argc, char **argv, void *data)
{
    int level = (int)(intptr_t)data;

    shell_print(sh, "Log level set to: %s (value: %d)", argv[0], level);
    /* log_filter_set(NULL, 0, level); */

    return 0;
}

/* Dictionary: (syntax, value, help) */
SHELL_SUBCMD_DICT_SET_CREATE(log_level_cmds, log_level_handler,
    (none,  0, "Disable logging"),
    (err,   1, "Error level only"),
    (wrn,   2, "Warning and above"),
    (inf,   3, "Info and above"),
    (dbg,   4, "Debug (all messages)")
);

SHELL_CMD_REGISTER(loglevel, &log_level_cmds, "Set log level", NULL);
```

**Usage:**
```
uart:~$ loglevel dbg
Log level set to: dbg (value: 4)
uart:~$ loglevel
loglevel - Set log level
Subcommands:
  none : Disable logging
  err  : Error level only
  wrn  : Warning and above
  inf  : Info and above
  dbg  : Debug (all messages)
```

---

## Dynamic Commands

Commands determined at runtime.

```c
#include <zephyr/shell/shell.h>
#include <string.h>

/* Storage for dynamic command names */
#define MAX_DYNAMIC_CMDS 10
#define MAX_CMD_LEN 32

static char dynamic_cmds[MAX_DYNAMIC_CMDS][MAX_CMD_LEN];
static uint8_t dynamic_cmd_count;

/* Dynamic command getter function */
static void dynamic_cmd_get(size_t idx, struct shell_static_entry *entry)
{
    if (idx < dynamic_cmd_count) {
        entry->syntax = dynamic_cmds[idx];
        entry->handler = NULL;
        entry->subcmd = NULL;
        entry->help = "Dynamic command";
    } else {
        entry->syntax = NULL;  /* No more commands */
    }
}

SHELL_DYNAMIC_CMD_CREATE(dynamic_subcmds, dynamic_cmd_get);

/* Add a new dynamic command */
static int cmd_dynamic_add(const struct shell *sh, size_t argc, char **argv)
{
    if (dynamic_cmd_count >= MAX_DYNAMIC_CMDS) {
        shell_error(sh, "Maximum commands reached");
        return -ENOMEM;
    }

    strncpy(dynamic_cmds[dynamic_cmd_count], argv[1], MAX_CMD_LEN - 1);
    dynamic_cmds[dynamic_cmd_count][MAX_CMD_LEN - 1] = '\0';
    dynamic_cmd_count++;

    shell_print(sh, "Added command: %s", argv[1]);
    return 0;
}

/* List dynamic commands */
static int cmd_dynamic_list(const struct shell *sh, size_t argc, char **argv)
{
    shell_print(sh, "Dynamic commands (%d):", dynamic_cmd_count);
    for (int i = 0; i < dynamic_cmd_count; i++) {
        shell_print(sh, "  %d: %s", i, dynamic_cmds[i]);
    }
    return 0;
}

/* Execute a dynamic command */
static int cmd_dynamic_exec(const struct shell *sh, size_t argc, char **argv)
{
    shell_print(sh, "Executing dynamic command: %s", argv[1]);
    return 0;
}

SHELL_STATIC_SUBCMD_SET_CREATE(dynamic_cmds_set,
    SHELL_CMD_ARG(add, NULL, "Add dynamic command", cmd_dynamic_add, 2, 0),
    SHELL_CMD(list, NULL, "List dynamic commands", cmd_dynamic_list),
    SHELL_CMD_ARG(exec, &dynamic_subcmds, "Execute dynamic command",
                  cmd_dynamic_exec, 2, 0),
    SHELL_SUBCMD_SET_END
);

SHELL_CMD_REGISTER(dynamic, &dynamic_cmds_set, "Dynamic command demo", NULL);
```

**Usage:**
```
uart:~$ dynamic add test1
Added command: test1
uart:~$ dynamic add test2
Added command: test2
uart:~$ dynamic list
Dynamic commands (2):
  0: test1
  1: test2
uart:~$ dynamic exec test<TAB>
test1  test2
```

---

## Conditional Commands

Commands enabled by Kconfig flags.

```c
#include <zephyr/shell/shell.h>

static int cmd_debug_dump(const struct shell *sh, size_t argc, char **argv)
{
    shell_print(sh, "Debug dump...");
    /* Dump debug information */
    return 0;
}

static int cmd_debug_reset(const struct shell *sh, size_t argc, char **argv)
{
    shell_print(sh, "Resetting system...");
    /* sys_reboot(SYS_REBOOT_COLD); */
    return 0;
}

SHELL_STATIC_SUBCMD_SET_CREATE(debug_cmds,
    /* Always available */
    SHELL_CMD(dump, NULL, "Dump debug info", cmd_debug_dump),

    /* Only when CONFIG_DEBUG_COMMANDS=y */
    SHELL_COND_CMD(CONFIG_DEBUG_COMMANDS, reset, NULL,
                   "Reset system", cmd_debug_reset),
    SHELL_SUBCMD_SET_END
);

/* Conditionally register entire command tree */
SHELL_COND_CMD_REGISTER(CONFIG_SHELL_DEBUG, debug, &debug_cmds,
                        "Debug commands", NULL);
```

---

## Commands with Getopt

Standard argument parsing with getopt.

**Kconfig:**
```kconfig
CONFIG_POSIX_C_LIB_EXT=y
CONFIG_GETOPT_LONG=y
CONFIG_SHELL_GETOPT=y
```

**Code:**
```c
#include <zephyr/shell/shell.h>
#include <getopt.h>

static int cmd_config(const struct shell *sh, size_t argc, char **argv)
{
    int opt;
    bool verbose = false;
    const char *name = NULL;
    int count = 1;

    /* Reset getopt */
    optreset = 1;
    optind = 1;

    while ((opt = getopt(argc, argv, "vn:c:h")) != -1) {
        switch (opt) {
        case 'v':
            verbose = true;
            break;
        case 'n':
            name = optarg;
            break;
        case 'c':
            count = atoi(optarg);
            break;
        case 'h':
            shell_print(sh, "Usage: config [-v] [-n name] [-c count]");
            shell_print(sh, "  -v        Verbose mode");
            shell_print(sh, "  -n name   Set name");
            shell_print(sh, "  -c count  Set count");
            return 0;
        default:
            shell_error(sh, "Unknown option: %c", opt);
            return -EINVAL;
        }
    }

    shell_print(sh, "Configuration:");
    shell_print(sh, "  Verbose: %s", verbose ? "yes" : "no");
    shell_print(sh, "  Name: %s", name ? name : "(not set)");
    shell_print(sh, "  Count: %d", count);

    return 0;
}

SHELL_CMD_ARG_REGISTER(config, NULL,
    "Configure settings\n"
    "Usage: config [-v] [-n name] [-c count] [-h]",
    cmd_config, 1, 6);
```

**Usage:**
```
uart:~$ config -v -n myapp -c 5
Configuration:
  Verbose: yes
  Name: myapp
  Count: 5
```

---

## Driver Shell Integration

Pattern for driver-specific shell commands (e.g., GPIO shell).

```c
#include <zephyr/shell/shell.h>
#include <zephyr/drivers/gpio.h>

/* Get device from argument */
static const struct device *get_gpio_device(const struct shell *sh,
                                            const char *name)
{
    const struct device *dev = shell_device_get_binding(name);

    if (dev == NULL) {
        shell_error(sh, "GPIO device not found: %s", name);
    }
    return dev;
}

static int cmd_gpio_set(const struct shell *sh, size_t argc, char **argv)
{
    const struct device *dev;
    gpio_pin_t pin;
    int value;
    int ret;

    dev = get_gpio_device(sh, argv[1]);
    if (dev == NULL) {
        return -ENODEV;
    }

    pin = shell_strtoul(argv[2], 10, &ret);
    if (ret != 0) {
        shell_error(sh, "Invalid pin: %s", argv[2]);
        return -EINVAL;
    }

    value = shell_strtoul(argv[3], 10, &ret);
    if (ret != 0 || value > 1) {
        shell_error(sh, "Invalid value (0 or 1): %s", argv[3]);
        return -EINVAL;
    }

    ret = gpio_pin_set(dev, pin, value);
    if (ret < 0) {
        shell_error(sh, "Failed to set pin: %d", ret);
        return ret;
    }

    shell_print(sh, "%s pin %d = %d", argv[1], pin, value);
    return 0;
}

SHELL_STATIC_SUBCMD_SET_CREATE(mygpio_cmds,
    SHELL_CMD_ARG(set, NULL,
        "Set GPIO pin\n"
        "Usage: mygpio set <device> <pin> <0|1>",
        cmd_gpio_set, 4, 0),
    SHELL_SUBCMD_SET_END
);

SHELL_CMD_REGISTER(mygpio, &mygpio_cmds, "Custom GPIO commands", NULL);
```
