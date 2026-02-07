---
name: zephyr-devicetree
description: "Enhances the AI agent's capability to work with Zephyr Devicetree, including creating overlays, defining bindings, and using the Devicetree C API macros. Use this skill when you need to: (1) Understand existing .dts/.dtsi files in Zephyr, (2) Create or modify devicetree overlays (.overlay), (3) Write or debug devicetree bindings (.yaml), (4) Use DT_* macros in C/C++ code to access hardware information, (5) Resolve devicetree-related build errors."
---

# Zephyr Devicetree Skill

This skill provides expert guidance on using and creating Devicetrees in Zephyr OS. Zephyr's devicetree system is used to describe hardware and is tightly integrated with the driver model and build system.

## Core Workflows

### 1. Understanding Devicetree Structure
Devicetree is a tree of nodes and properties. Unlike Linux, Zephyr heavily relies on **bindings** to validate nodes and generate C macros.

- For basic syntax, nodes, and properties, see [syntax.md](references/syntax.md).
- To understand how nodes match with bindings via the `compatible` property, see [bindings.md](references/bindings.md).

### 2. Modifying Hardware via Overlays
Overlays are the primary way to customize hardware for an application or a specific board variant without modifying the base Zephyr tree.

- To learn how to override properties, add nodes, or enable/disable devices, see [overlays.md](references/overlays.md).
- **Pro-tip**: Check `build/zephyr/zephyr.dts` after a build to see the final, merged devicetree.

### 3. Writing Bindings
Bindings define the "schema" for a node. They are written in YAML.

- For details on binding syntax, property types, and bus-specific matching, see [bindings.md](references/bindings.md).
- Always include `base.yaml` for standard properties like `reg` and `status`.

### 4. Accessing Devicetree from C Code
Zephyr provides a macro-based API to access devicetree data at compile-time. This is more efficient than runtime parsing.

- For a guide on `DT_*` macros (node identifiers, property access, registers, interrupts), see [macros.md](references/macros.md).
- **Important**: Node labels (e.g., `DT_NODELABEL(i2c1)`) are the preferred way to get node identifiers.

## Practical Examples
See [examples.md](references/examples.md) for common scenarios:
- Configuring a GPIO LED.
- Adding an I2C sensor.
- Defining SPI flash partitions.
- Setting up a PWM buzzer.

## Troubleshooting
- **Missing Binding**: If you get a "choice of binding for ... not found" error, ensure your `compatible` property matches a binding file and that the binding is in a location Zephyr knows about.
- **Node Disabled**: If `DEVICE_DT_GET()` fails, check if the node has `status = "okay"`.
- **Undefined Reference**: If you get linker errors like `__device_dts_ord_N`, the driver for that device is likely not enabled in Kconfig.
- **Final DTS**: Always check `build/zephyr/zephyr.dts` to verify your overlays were applied correctly.
