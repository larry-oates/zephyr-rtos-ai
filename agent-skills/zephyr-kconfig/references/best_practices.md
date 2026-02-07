# Zephyr Kconfig Best Practices

## 1. Defining vs. Configuring

Understand the difference to avoid errors:

*   **Defining (`Kconfig`)**: Creates *new* symbols (options). Used in drivers, modules, and subsystems.
    *   *Action*: "Add a new option to enable feature X."
    *   *File*: `Kconfig`, `drivers/Kconfig`, `modules/Kconfig`.
*   **Configuring (`prj.conf`)**: Sets values for *existing* symbols. Used in applications.
    *   *Action*: "Turn on Bluetooth."
    *   *File*: `prj.conf`, `boards/my_board.conf`.

## 2. Naming Conventions

*   **Prefix**: All Kconfig symbols are automatically prefixed with `CONFIG_` in C code and `prj.conf`.
    *   In `Kconfig`: define as `MY_SYMBOL`.
    *   In `C`: use `CONFIG_MY_SYMBOL`.
    *   In `prj.conf`: use `CONFIG_MY_SYMBOL=y`.
*   **Namespacing**: Use prefixes to avoid collisions.
    *   Driver: `config LIS2DH_TRIGGER` (for lis2dh driver).
    *   Subsystem: `config BT_L2CAP`.
    *   App: `config APP_MAX_USERS`.

## 3. File Locations

### Applications

*   **`prj.conf`**: Main configuration file.
*   **`Kconfig`**: Application-specific symbol definitions.
    *   Usually in the root of the app directory.
    *   Must be sourced explicitly if not default, but standard app structures pick it up.

### Modules / Drivers

*   **Root `Kconfig`**: Defines the module/driver toggle.
*   **`zephyr/module.yml`**: Defines the path to the Kconfig file so Zephyr's build system (`west`) finds it.
    ```yaml
    build:
      kconfig: Kconfig
    ```

## 4. Dependencies (`depends on` vs `select`)

*   Use **`depends on`** for hardware requirements or upstream subsystems (e.g., `depends on SPI`).
*   Use **`select`** only when you *must* force a strictly hidden implementation detail (e.g., `select HAS_HW_CRYPTO`).
    *   *Risk*: `select` does not check dependencies of the selected symbol.
*   Use **`imply`** for "nice to have" defaults that the user can override.

## 5. Description Guidelines

*   **Prompt**: Short summary (visible in menuconfig). `bool "Enable Foo"`
*   **Help**: Indented (2 spaces) text explaining *what* it does and *why* you'd change it.

```kconfig
config FOO_ENABLE
    bool "Enable Foo Feature"
    help
      Enables the Foo feature which allows...
```
