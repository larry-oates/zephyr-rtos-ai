# Shell Backends Configuration

Complete guide for configuring Zephyr Shell transport backends.

## Table of Contents

1. [Overview](#overview)
2. [UART Backend](#uart-backend)
3. [USB CDC ACM Backend](#usb-cdc-acm-backend)
4. [RTT Backend](#rtt-backend)
5. [Telnet Backend](#telnet-backend)
6. [Bluetooth LE NUS Backend](#bluetooth-le-nus-backend)
7. [RPMSG Backend](#rpmsg-backend)
8. [Dummy Backend](#dummy-backend)
9. [Multiple Backends](#multiple-backends)

---

## Overview

The shell can be connected to different transport layers for command input and output. Each backend has specific configuration requirements and use cases.

| Backend | Use Case | Connection |
|---------|----------|------------|
| UART | Default, most common | Serial terminal |
| USB CDC ACM | USB serial | USB cable |
| RTT | Debugging | J-Link probe |
| Telnet | Network access | TCP/IP |
| BLE NUS | Wireless | Bluetooth LE |
| RPMSG | Multi-core | Inter-processor |
| Dummy | Testing | Programmatic |

---

## UART Backend

The most common backend, enabled by default when shell is enabled.

### Configuration

```kconfig
# prj.conf
CONFIG_SHELL=y
CONFIG_SHELL_BACKEND_SERIAL=y
```

### Additional Options

| Option | Default | Description |
|--------|---------|-------------|
| `CONFIG_SHELL_BACKEND_SERIAL_INTERRUPT_DRIVEN` | y | Use interrupt-driven UART |
| `CONFIG_SHELL_BACKEND_SERIAL_TX_RING_BUFFER_SIZE` | 8 | TX ring buffer size |
| `CONFIG_SHELL_BACKEND_SERIAL_RX_RING_BUFFER_SIZE` | 64 | RX ring buffer size |

### Devicetree

The shell uses the device designated by the `zephyr,shell-uart` chosen node:

```dts
/ {
    chosen {
        zephyr,shell-uart = &uart0;
    };
};
```

### Accessing Backend

```c
#include <zephyr/shell/shell_uart.h>

const struct shell *sh = shell_backend_uart_get_ptr();
shell_execute_cmd(sh, "help");
```

---

## USB CDC ACM Backend

Connect via USB as a virtual serial port.

### Configuration

**Recommended**: Use the `cdc-acm-console` snippet:

```bash
west build -S cdc-acm-console [...]
```

**Manual Configuration**:

```kconfig
# prj.conf
CONFIG_USB_DEVICE_STACK=y
CONFIG_USB_CDC_ACM=y
CONFIG_SHELL=y
CONFIG_SHELL_BACKEND_SERIAL=y
```

With devicetree overlay:

```dts
/ {
    chosen {
        zephyr,shell-uart = &cdc_acm_uart0;
    };
};

&zephyr_udc0 {
    cdc_acm_uart0: cdc_acm_uart0 {
        compatible = "zephyr,cdc-acm-uart";
    };
};
```

---

## RTT Backend

Use with Segger J-Link for debugging without UART.

### Configuration

```kconfig
# prj.conf
CONFIG_USE_SEGGER_RTT=y
CONFIG_SHELL=y
CONFIG_SHELL_BACKEND_RTT=y
CONFIG_SHELL_BACKEND_SERIAL=n  # Disable UART if not needed
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `CONFIG_SHELL_BACKEND_RTT_BUFFER` | 0 | RTT channel/buffer index |

### Connecting

**Using west**:
```bash
west rtt
```

**Using PuTTY**:
1. Start debug session: `west attach`
2. Open PuTTY with Telnet to localhost:19021
3. Set Terminal → Local echo: Force off
4. Set Terminal → Local line editing: Force off

**Using JLinkRTTClient** (macOS alternative):
```bash
# Terminal 1
JLinkRTTLogger -Device NRF52840_XXAA -RTTChannel 1 -if SWD -Speed 4000 ~/rtt.log

# Terminal 2
nc localhost 19021
```

### Using RTT with Logging

To use both shell and logging via RTT on separate channels:

```kconfig
CONFIG_SHELL_BACKEND_RTT_BUFFER=0        # Shell on channel 0
CONFIG_LOG_BACKEND_RTT=y
CONFIG_LOG_BACKEND_RTT_BUFFER=1          # Logging on channel 1
```

---

## Telnet Backend

Access shell over the network.

### Configuration

```kconfig
# prj.conf
CONFIG_NETWORKING=y
CONFIG_NET_TCP=y
CONFIG_SHELL=y
CONFIG_SHELL_BACKEND_TELNET=y
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `CONFIG_SHELL_TELNET_PORT` | 23 | Telnet port |
| `CONFIG_SHELL_TELNET_LINE_BUF_SIZE` | 80 | Line buffer size |
| `CONFIG_SHELL_TELNET_SEND_TIMEOUT` | 100 | Send timeout (ms) |
| `CONFIG_SHELL_TELNET_SUPPORT_COMMAND` | n | Handle telnet commands |

### Connecting

```bash
telnet <device_ip> <port>
# Example:
telnet 192.168.1.100 23
```

### Telnet Command Support

Enable `CONFIG_SHELL_TELNET_SUPPORT_COMMAND=y` for character-at-a-time mode, which enables:
- Line editing
- Tab completion
- Command history

**Trade-off**: Increased network traffic.

---

## Bluetooth LE NUS Backend

Wireless shell access via Bluetooth LE Nordic UART Service.

### Configuration

**Recommended**: Use the `nus-console` snippet:

```bash
west build -S nus-console [...]
```

**Manual Configuration**:

```kconfig
# prj.conf
CONFIG_BT=y
CONFIG_BT_PERIPHERAL=y
CONFIG_BT_NUS=y
CONFIG_SHELL=y
CONFIG_SHELL_BACKEND_NUS=y
```

### Connecting

Use a BLE terminal app that supports NUS (Nordic UART Service):
- nRF Connect (mobile)
- Serial Bluetooth Terminal (Android)
- BLE Serial (iOS)

---

## RPMSG Backend

For multi-core systems with inter-processor communication.

### Configuration

```kconfig
# prj.conf
CONFIG_SHELL=y
CONFIG_SHELL_BACKEND_RPMSG=y
CONFIG_IPC_SERVICE=y
CONFIG_MBOX=y
```

### Devicetree

```dts
/ {
    chosen {
        zephyr,shell-ipc = &ipc0;
    };
};
```

---

## Dummy Backend

For testing and programmatic command execution.

### Configuration

```kconfig
# prj.conf
CONFIG_SHELL=y
CONFIG_SHELL_BACKEND_DUMMY=y
```

### Usage

```c
#include <zephyr/shell/shell_dummy.h>

int main(void)
{
    const struct shell *sh = shell_backend_dummy_get_ptr();

    /* Execute command programmatically */
    shell_execute_cmd(sh, "help");

    /* Get output from dummy backend */
    const char *output = shell_backend_dummy_get_output(sh, &output_size);
}
```

---

## Multiple Backends

Multiple backends can be active simultaneously.

### Example: UART + RTT

```kconfig
CONFIG_SHELL=y
CONFIG_SHELL_BACKEND_SERIAL=y
CONFIG_USE_SEGGER_RTT=y
CONFIG_SHELL_BACKEND_RTT=y
```

### Backend Access

```c
#include <zephyr/shell/shell_uart.h>
#include <zephyr/shell/shell_rtt.h>

/* Execute on specific backend */
shell_execute_cmd(shell_backend_uart_get_ptr(), "version");
shell_execute_cmd(shell_backend_rtt_get_ptr(), "kernel threads");
```

### Considerations

- Each backend runs independently
- Commands registered once, available on all backends
- Log messages may appear on multiple backends if shell log backend enabled
- Memory usage increases with each backend
