# Zephyr Socket File Locations

Quick reference for finding socket, TLS, and DNS related files in the Zephyr tree.

## Headers (include/zephyr/net/)

| File | Purpose |
|------|---------|
| `socket.h` | Main BSD sockets API |
| `socket_types.h` | Socket type definitions |
| `socket_poll.h` | poll() implementation |
| `socket_select.h` | select() implementation |
| `socket_offload.h` | Offloaded socket API |
| `socket_service.h` | Socket service API |
| `socket_net_mgmt.h` | Network management sockets |
| `socketutils.h` | Socket utility functions |
| `socketcan.h` | CAN bus sockets |
| `socketcan_utils.h` | CAN socket utilities |
| `tls_credentials.h` | TLS credential management |
| `dns_resolve.h` | DNS resolver API |
| `dns_sd.h` | DNS Service Discovery |

## Implementation (subsys/net/lib/)

### Sockets (subsys/net/lib/sockets/)

| File | Purpose |
|------|---------|
| `sockets.c` | Core socket implementation |
| `sockets_inet.c` | IPv4/IPv6 socket support |
| `sockets_tls.c` | TLS/DTLS socket support |
| `sockets_packet.c` | Raw packet sockets (AF_PACKET) |
| `sockets_can.c` | CAN bus sockets |
| `sockets_misc.c` | Miscellaneous socket functions |
| `sockets_net_mgmt.c` | Network management sockets |
| `sockets_service.c` | Socket service implementation |
| `socket_dispatcher.c` | Socket dispatcher |
| `socket_offload.c` | Socket offloading support |
| `socket_obj_core.c` | Socket object core |
| `socketpair.c` | socketpair() implementation |
| `getaddrinfo.c` | getaddrinfo() implementation |
| `getnameinfo.c` | getnameinfo() implementation |

### DNS (subsys/net/lib/dns/)

| File | Purpose |
|------|---------|
| `resolve.c` | DNS resolver core |
| `dns_pack.c` | DNS packet packing/unpacking |
| `dns_cache.c` | DNS cache implementation |
| `dns_sd.c` | DNS Service Discovery |
| `mdns_responder.c` | mDNS responder |
| `llmnr_responder.c` | LLMNR responder |
| `dispatcher.c` | DNS dispatcher |

## Kconfig Files

| Path | Purpose |
|------|---------|
| `subsys/net/lib/sockets/Kconfig` | Socket configuration options |
| `subsys/net/lib/dns/Kconfig` | DNS configuration options |
| `modules/mbedtls/Kconfig` | mbedTLS configuration |
| `modules/mbedtls/Kconfig.tls-generic` | Generic TLS options |

## Samples (samples/net/)

### Socket Samples (samples/net/sockets/)

| Sample | Description |
|--------|-------------|
| `echo_server/` | TCP/UDP echo server |
| `echo_client/` | TCP/UDP echo client |
| `echo/` | Simple echo example |
| `echo_async/` | Async echo with poll() |
| `echo_async_select/` | Async echo with select() |
| `echo_service/` | Socket service example |
| `tcp/` | Basic TCP example |
| `http_get/` | HTTPS GET with TLS |
| `http_client/` | HTTP client |
| `http_server/` | HTTP server |
| `dumb_http_server/` | Simple HTTP server |
| `dumb_http_server_mt/` | Multi-threaded HTTP server |
| `big_http_download/` | Large file download |
| `websocket_client/` | WebSocket client |
| `coap_client/` | CoAP client |
| `coap_server/` | CoAP server |
| `coap_download/` | CoAP download |
| `coap_upload/` | CoAP upload |
| `sntp_client/` | SNTP client |
| `can/` | CAN socket example |
| `packet/` | Raw packet sockets |
| `net_mgmt/` | Network management sockets |
| `socketpair/` | socketpair() example |
| `txtime/` | TX time scheduling |

### DNS Sample

| Sample | Description |
|--------|-------------|
| `dns_resolve/` | DNS resolution example |

## Documentation (doc/connectivity/networking/)

| Path | Purpose |
|------|---------|
| `api/sockets.rst` | BSD sockets documentation |
| `api/dns_resolve.rst` | DNS resolver documentation |

## Tests (tests/net/)

| Path | Purpose |
|------|---------|
| `socket/` | Socket unit tests |
| `socket/tls/` | TLS socket tests |
| `socket/udp/` | UDP socket tests |
| `socket/tcp/` | TCP socket tests |
| `dns/` | DNS tests |

## Key Paths Summary

```
# Headers
include/zephyr/net/socket.h           # Main sockets API
include/zephyr/net/tls_credentials.h  # TLS credentials
include/zephyr/net/dns_resolve.h      # DNS resolver

# Implementation
subsys/net/lib/sockets/               # Socket implementation
subsys/net/lib/dns/                   # DNS implementation

# Samples
samples/net/sockets/echo_server/      # TCP/UDP server example
samples/net/sockets/http_get/         # TLS client example
samples/net/dns_resolve/              # DNS example

# Configuration
subsys/net/lib/sockets/Kconfig        # Socket Kconfig
subsys/net/lib/dns/Kconfig            # DNS Kconfig
```
