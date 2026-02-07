---
name: zephyr-kconfig
description: Expert guidance on Zephyr OS Kconfig system. Use when creating/editing Kconfig files, setting configuration values in prj.conf, or fixing Kconfig dependency errors.
---

# Zephyr Kconfig Expert

## When to Use This Skill

Use this skill when:
1.  **Defining Options**: Creating new configuration symbols in `Kconfig` files for drivers, modules, or apps.
2.  **Configuring Apps**: Setting values in `prj.conf` or `boards/*.conf`.
3.  **Debugging**: Resolving "unsatisfied dependencies" or "symbol not found" errors during `west build`.
4.  **Structuring**: Organizing configuration menus and files in a Zephyr project.

## Core Concept: Define vs. Configure

**CRITICAL**: Distinguish between *defining* a symbol and *assigning* a value.

| Action | File | Syntax Example |
| :--- | :--- | :--- |
| **Define** (Create Option) | `Kconfig` | `config MY_FEAT`<br>&nbsp;&nbsp;`bool "Enable feature"` |
| **Configure** (Set Value) | `prj.conf` | `CONFIG_MY_FEAT=y` |

## Workflow

### 1. Creating/Editing `Kconfig` (Definitions)
*   For syntax rules (types, menus, logic), read [references/syntax.md](references/syntax.md).
*   For placement and naming conventions, read [references/best_practices.md](references/best_practices.md).

**Key Rules:**
*   Always add a `help` string for clarity.
*   Use `depends on` for hardware/subsystem requirements.
*   Avoid `select` unless necessary; it bypasses dependency checks.

### 2. Configuring Application (`prj.conf`)
*   Use `CONFIG_SYMBOL_NAME=value`.
*   **Booleans**: `y` or `n`. (e.g., `CONFIG_LOG=y`)
*   **Strings**: Double quotes. (e.g., `CONFIG_BT_DEVICE_NAME="MyDevice"`)
*   **Integers**: Direct numbers. (e.g., `CONFIG_MAIN_STACK_SIZE=2048`)

### 3. Debugging Dependency Errors
If `west build` reports a Kconfig error:
1.  **Check Visibility**: Is the symbol `depends on` condition met?
2.  **Check Typo**: specific `CONFIG_` prefix usage.
    *   In `Kconfig`: `config MY_NAME` (NO prefix).
    *   In `prj.conf`: `CONFIG_MY_NAME=y` (WITH prefix).

## References

*   [syntax.md](references/syntax.md) - Detailed syntax (bool, int, menu, choice, if/endif).
*   [best_practices.md](references/best_practices.md) - File organization, naming, and dependency safety.
