# Devicetree C API Macros

Zephyr provides a comprehensive set of C macros in `<zephyr/devicetree.h>` to access devicetree data at build-time.

## Node Identifiers
Node identifiers are internal representations of nodes. They are NOT variables and cannot be stored.

- `DT_PATH(soc, uart_40002000)`: Get ID by full path (slashes replaced by underscores).
- `DT_NODELABEL(uart0)`: Get ID by node label. **(Preferred)**
- `DT_ALIAS(my_uart)`: Get ID via `/aliases` node.
- `DT_CHOSEN(zephyr_console)`: Get ID via `/chosen` node.
- `DT_INST(inst, compat)`: Get ID by instance number of a compatible. Used in drivers.
- `DT_PARENT(node_id)` / `DT_CHILD(node_id, child_name)`: Navigate hierarchy.

## Property Access
- `DT_PROP(node_id, prop)`: Get property value (int, string, bool).
- `DT_PROP_LEN(node_id, prop)`: Get length of an array property.
- `DT_ENUM_IDX(node_id, prop)`: Get index of an enum value.

## Register and Interrupt Access
- `DT_REG_ADDR(node_id)`: Base address of `reg`.
- `DT_REG_SIZE(node_id)`: Size of `reg`.
- `DT_REG_ADDR_BY_IDX(node_id, idx)`: Address of Nth register block.
- `DT_NUM_REGS(node_id)`: Total number of register blocks.
- `DT_IRQN(node_id)`: Get the interrupt number.
- `DT_IRQ_BY_IDX(node_id, idx, cell)`: Get a specific cell of the Nth interrupt.

## Phandle and Hardware APIs
- `DT_PHANDLE(node_id, prop)`: Get node ID from a phandle property.
- `DT_PHA(node_id, prop, cell)`: Get a cell value from a phandle array.
- `DT_GPIO_PIN(node_id, prop)`: Specific helper for GPIO pins.
- `DT_GPIO_FLAGS(node_id, prop)`: Specific helper for GPIO flags.

## Existence and Status Checks
- `DT_NODE_EXISTS(node_id)`: Check if node exists.
- `DT_NODE_HAS_STATUS(node_id, okay)`: Check if node is enabled.
- `DT_NODE_HAS_PROP(node_id, prop)`: Check if property exists.
- `DT_HAS_COMPAT_STATUS_OKAY(compat)`: Check if any node with compat is enabled.

## Driver Conveniences
When writing drivers, define `DT_DRV_COMPAT`:
```c
#define DT_DRV_COMPAT vendor_device
DT_INST_PROP(0, clock_frequency) // Access prop of instance 0
```
