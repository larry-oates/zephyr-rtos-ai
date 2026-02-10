# DMA in Devicetree

DMA (Direct Memory Access) configuration describes DMA controllers and how peripherals connect to DMA channels.

## Overview

The DMA model has two parts:
1. **DMA controllers** — Hardware that performs memory transfers
2. **DMA consumers** — Peripherals that use DMA channels

## DMA Controller

Controllers are marked with `dma-controller` and define cell format with `#dma-cells`:

```devicetree
dma1: dma@40026000 {
    compatible = "st,stm32-dma-v2";
    reg = <0x40026000 0x400>;
    interrupts = <11 0>, <12 0>, <13 0>, <14 0>,
                 <15 0>, <16 0>, <17 0>, <18 0>;
    dma-controller;
    #dma-cells = <4>;  /* channel, slot, config, features */
    status = "okay";
};
```

## DMA Consumer

Devices reference DMA channels using `dmas` and `dma-names`:

```devicetree
&spi1 {
    status = "okay";
    dmas = <&dma1 3 3 0x28440 0x03>,
           <&dma1 0 3 0x28480 0x03>;
    dma-names = "tx", "rx";
};
```

## Properties

### Controller Properties

| Property | Type | Description |
|----------|------|-------------|
| `dma-controller` | boolean | Marks node as DMA controller |
| `#dma-cells` | int | Number of cells per DMA specifier |
| `dma-channels` | int | Number of DMA channels available |
| `dma-requests` | int | Number of DMA request lines |

### Consumer Properties

| Property | Type | Description |
|----------|------|-------------|
| `dmas` | phandle-array | Reference to DMA channel(s) with specifier |
| `dma-names` | string-array | Names for each DMA reference (typically "tx", "rx") |

## Vendor Cell Formats

### STM32 DMA - 4 cells
```
<&dma channel slot config features>
```
- `channel`: DMA stream/channel number
- `slot`: Request slot (mux selection)
- `config`: Configuration bits (direction, width, etc.)
- `features`: Feature flags

```devicetree
/* STM32 UART with DMA */
&usart1 {
    dmas = <&dma2 7 4 0x28440 0x03>,   /* TX: stream 7, slot 4 */
           <&dma2 2 4 0x28480 0x03>;   /* RX: stream 2, slot 4 */
    dma-names = "tx", "rx";
};
```

### Nordic nRF - Variable cells
```
<&dma channel>
```

### NXP EDMA - 2 cells
```
<&edma channel mux>
```

## DMAMUX (DMA Multiplexer)

Some SoCs have a DMA request multiplexer:

```devicetree
dmamux1: dmamux@40020800 {
    compatible = "st,stm32-dmamux";
    reg = <0x40020800 0x400>;
    #dma-cells = <3>;
    dma-channels = <16>;
    dma-generators = <4>;
    dma-requests = <107>;
};

&uart4 {
    dmas = <&dmamux1 0 52 (STM32_DMA_PERIPH_TX | STM32_DMA_MEM_INC)>,
           <&dmamux1 1 53 (STM32_DMA_PERIPH_RX | STM32_DMA_MEM_INC)>;
    dma-names = "tx", "rx";
};
```

## Complete Example

```devicetree
/* Enable DMA for SPI */
&dma1 {
    status = "okay";
};

&spi2 {
    status = "okay";
    pinctrl-0 = <&spi2_default>;
    pinctrl-names = "default";
    cs-gpios = <&gpio0 25 GPIO_ACTIVE_LOW>;

    dmas = <&dma1 4 3 (STM32_DMA_PERIPH_TX | STM32_DMA_MEM_INC | STM32_DMA_MEM_8BITS)>,
           <&dma1 3 3 (STM32_DMA_PERIPH_RX | STM32_DMA_MEM_INC | STM32_DMA_MEM_8BITS)>;
    dma-names = "tx", "rx";
};
```

## C API

DMA is typically configured automatically by drivers using devicetree. Manual access:

```c
#include <zephyr/drivers/dma.h>

#define MY_NODE DT_NODELABEL(spi2)

/* Check if DMA is configured */
#if DT_NODE_HAS_PROP(MY_NODE, dmas)
    /* Get DMA controller device */
    const struct device *dma_dev = DEVICE_DT_GET(DT_DMAS_CTLR(MY_NODE));

    /* Get channel from devicetree */
    uint32_t channel = DT_DMAS_CELL_BY_NAME(MY_NODE, tx, channel);
#endif

/* DMA macros */
DT_DMAS_CTLR(node_id)                    /* DMA controller phandle */
DT_DMAS_CTLR_BY_IDX(node_id, idx)        /* Nth DMA controller */
DT_DMAS_CTLR_BY_NAME(node_id, name)      /* DMA by name */
DT_DMAS_CELL_BY_NAME(node_id, name, cell) /* Specific cell value */
DT_DMAS_CELL_BY_IDX(node_id, idx, cell)
DT_HAS_DMA_CHANNEL(node_id, name)        /* Check if channel exists */
```

## Binding Example

```yaml
# dts/bindings/dma/vendor,my-dma.yaml
compatible: "vendor,my-dma"
include: [dma-controller.yaml]

properties:
  reg:
    required: true
  interrupts:
    required: true
  "#dma-cells":
    const: 2

dma-cells:
  - channel
  - config
```

## Tips

1. **Check SoC reference** — DMA slot/channel assignments are SoC-specific
2. **Enable controller** — DMA controller must have `status = "okay"`
3. **Interrupt per channel** — Each DMA channel typically needs an interrupt
4. **Driver support** — Not all drivers support DMA; check driver Kconfig
5. **Power consumption** — DMA can reduce CPU load but may affect power states
