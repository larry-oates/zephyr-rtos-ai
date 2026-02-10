---
name: zephyr-settings
description: Comprehensive skill for using and creating settings in Zephyr OS. It covers the settings subsystem, handlers, backends, and storage locations. Use it when you need to store persistent configuration, runtime state, or implement custom settings handlers.
---

# Zephyr Settings Skill

This skill enhances the AI agent's ability to work with the Zephyr Settings subsystem.

## Quick Start

1.  **Initialize**: Call `settings_subsys_init()`.
2.  **Define Handlers**: Use `SETTINGS_STATIC_HANDLER_DEFINE` for static registration or `settings_handler` struct for dynamic.
3.  **Load**: Call `settings_load()` to populate values from persistent storage.
4.  **Save**: Use `settings_save_one()` or `settings_save()`.

## Core Concepts

-   **Keys**: Represented as strings, often hierarchical (e.g., `id/serial`).
-   **Backends**: Persistent storage implementations like NVS (Non-Volatile Storage), ZMS (Zephyr Memory Storage), FCB (Flash Circular Buffer), or File system.
-   **Handlers**: Logic to handle specific subtrees of settings.
    -   `h_set`: Called when loading or setting a value.
    -   `h_get`: Called when getting a value.
    -   `h_export`: Called when saving all settings.
    -   `h_commit`: Called after all settings in a load operation are processed.

## Common Workflows

### Implementing a Setting

1.  Define a variable to hold the setting.
2.  Implement `h_set` to update the variable from storage.
3.  Implement `h_export` to allow the subsystem to save the variable.
4.  Register the handler.

### Loading and Saving

-   `settings_load()` is typically called once at startup.
-   `settings_save_one()` is used to persist a single value immediately.
-   `settings_save()` iterates through all handlers and calls their `h_export`.

## Reference Material

-   **API Reference**: See [references/api_reference.md](references/api_reference.md) for detailed function signatures and structures.
-   **Examples**: See [references/examples.md](references/examples.md) for common implementation patterns.
-   **Locations**: See [references/locations.md](references/locations.md) for source code and documentation paths in the Zephyr workspace.

## Kconfig Requirements

Ensure the following are enabled in `prj.conf`:
- `CONFIG_SETTINGS=y`
- One or more backends: `CONFIG_SETTINGS_NVS=y`, `CONFIG_SETTINGS_ZMS=y`, `CONFIG_SETTINGS_FILE=y`, or `CONFIG_SETTINGS_FCB=y`.
- `CONFIG_SETTINGS_RUNTIME=y` if using runtime API.
