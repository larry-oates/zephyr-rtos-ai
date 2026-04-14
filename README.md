# Zephyr RTOS AI

An Agent Hardness for AI assisted embedded firmware development

## Install

```bash
npx skills add ksachdeva/zephyr-rtos-ai
```

## Agent Skills

| Skill | Description |
|-------|-------------|
| `zephyr-bluetooth-le` | BLE development covering GAP roles, GATT services, advertising, scanning, connections, pairing/bonding, and built-in services. |
| `zephyr-device-drivers` | Device driver model, initialization levels, power management, bus-specific patterns, and sensor drivers. |
| `zephyr-devicetree` | Devicetree overlays, bindings, `DT_*` C macros, pin control, clocks, interrupts, DMA, and address translation. |
| `zephyr-fs` | File system support including VFS API, LittleFS, FAT, ext2, and FCB for persistent file-based storage. |
| `zephyr-gpio` | GPIO pin configuration, reading/writing, interrupts, and devicetree bindings for digital I/O. |
| `zephyr-i2c` | I2C bus communication covering synchronous/asynchronous transfers, register access helpers, target mode, and SMBus. |
| `zephyr-isr` | Interrupt Service Routines — static/dynamic ISRs, direct ISRs, IRQ management, and ISR-to-thread offloading. |
| `zephyr-json` | Descriptor-based JSON serialization/deserialization for C structs without dynamic memory allocation. |
| `zephyr-kconfig` | Build-time configuration — defining symbols, `prj.conf`, dependency debugging, and menuconfig/guiconfig. |
| `zephyr-kernel-datapassing` | Data passing between threads and ISRs using FIFO, LIFO, Stack, Message Queue, Mailbox, Pipe, ZBus, and Ring Buffer. |
| `zephyr-kernel-synchronization` | Kernel synchronization primitives — Semaphores, Mutexes, Events, and Condition Variables. |
| `zephyr-memory` | Memory management including heaps, memory slabs, memory blocks, memory domains, and virtual memory. |
| `zephyr-net-socket` | BSD sockets, TLS/DTLS secure sockets, DNS resolution, and mDNS/LLMNR support. |
| `zephyr-netbuf` | Network Buffer (`net_buf`) subsystem for buffer pools, reference counting, fragmentation, and protocol encoding. |
| `zephyr-settings` | Persistent configuration storage with settings handlers and NVS, ZMS, FCB, or File backends. |
| `zephyr-shell-commands` | Shell subsystem for creating CLI commands, subcommands, argument parsing, and configuring shell backends. |
| `zephyr-smf` | State Machine Framework for flat and hierarchical (HSM) state machines with entry/run/exit actions. |
| `zephyr-spi` | SPI communication covering synchronous/asynchronous transfers, modes (CPOL/CPHA), chip select, and scatter-gather buffers. |
| `zephyr-storage` | Direct key-value flash storage using NVS and ZMS subsystems with numeric IDs. |
| `zephyr-testing` | Unit and integration testing with Ztest framework, Twister test runner, and FFF mocking. |
| `zephyr-threading` | Thread management, scheduling (cooperative vs preemptive), lifecycle, workqueues, and deferred processing. |
| `zephyr-uart` | UART serial communication covering polling, interrupt-driven, and async DMA-based APIs. |
| `zephyr-wifi` | WiFi Station and Access Point modes, scanning, connection management, security types, and power save. |


## TODO

- [ ] Add more skills covering the entire Zephyr subsystem
- [ ] Custom Prompts and Agents
- [ ] Support for spec driven development