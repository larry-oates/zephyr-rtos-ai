# Kconfig Options

## Core Networking

| Option | Default | Description |
|--------|---------|-------------|
| `CONFIG_NETWORKING` | n | Enable networking subsystem |
| `CONFIG_NET_IPV4` | n | Enable IPv4 support |
| `CONFIG_NET_IPV6` | n | Enable IPv6 support |
| `CONFIG_NET_TCP` | n | Enable TCP protocol |
| `CONFIG_NET_UDP` | n | Enable UDP protocol |

## BSD Sockets

| Option | Default | Description |
|--------|---------|-------------|
| `CONFIG_NET_SOCKETS` | n | Enable BSD sockets API |
| `CONFIG_POSIX_API` | n | Use POSIX function names (no `zsock_` prefix) |
| `CONFIG_NET_SOCKETS_POSIX_NAMES` | n | Alternative to POSIX_API for socket names only |
| `CONFIG_NET_SOCKETS_POLL_MAX` | 3 | Max sockets in poll() |
| `CONFIG_NET_SOCKETS_PRIORITY_DEFAULT` | 50 | Socket implementation priority |

## TLS/DTLS

| Option | Default | Description |
|--------|---------|-------------|
| `CONFIG_NET_SOCKETS_SOCKOPT_TLS` | n | Enable TLS socket options |
| `CONFIG_NET_SOCKETS_ENABLE_DTLS` | n | Enable DTLS support |
| `CONFIG_NET_SOCKETS_TLS_MAX_CONTEXTS` | 1 | Max concurrent TLS connections |
| `CONFIG_NET_SOCKETS_TLS_PRIORITY` | 45 | TLS socket implementation priority |
| `CONFIG_NET_SOCKETS_DTLS_TIMEOUT` | 30000 | DTLS handshake timeout (ms) |

## mbedTLS

| Option | Default | Description |
|--------|---------|-------------|
| `CONFIG_MBEDTLS` | n | Enable mbedTLS library |
| `CONFIG_MBEDTLS_BUILTIN` | y | Use builtin mbedTLS (vs external) |
| `CONFIG_MBEDTLS_ENABLE_HEAP` | n | Enable mbedTLS heap (required for TLS) |
| `CONFIG_MBEDTLS_HEAP_SIZE` | 0 | mbedTLS heap size (40000-60000 typical) |
| `CONFIG_MBEDTLS_SSL_MAX_CONTENT_LEN` | 16384 | Max TLS record size |
| `CONFIG_MBEDTLS_PEM_CERTIFICATE_FORMAT` | n | Enable PEM cert parsing |
| `CONFIG_MBEDTLS_KEY_EXCHANGE_PSK_ENABLED` | n | Enable PSK ciphersuites |
| `CONFIG_MBEDTLS_DEBUG` | n | Enable mbedTLS debug output |
| `CONFIG_MBEDTLS_DEBUG_LEVEL` | 0 | Debug verbosity (0-4) |

## TLS Credential Storage

| Option | Default | Description |
|--------|---------|-------------|
| `CONFIG_TLS_CREDENTIALS` | y | Enable TLS credentials subsystem |
| `CONFIG_TLS_MAX_CREDENTIALS_NUMBER` | 4 | Max stored credentials |
| `CONFIG_TLS_CREDENTIAL_FILENAMES` | n | Reference creds by filename |

## DNS Resolver

| Option | Default | Description |
|--------|---------|-------------|
| `CONFIG_DNS_RESOLVER` | n | Enable DNS resolver |
| `CONFIG_DNS_SERVER_IP_ADDRESSES` | n | Enable static DNS server config |
| `CONFIG_DNS_SERVER1` | "" | Primary DNS server IP |
| `CONFIG_DNS_SERVER2` | "" | Secondary DNS server IP |
| `CONFIG_DNS_RESOLVER_MAX_QUERY_LEN` | 64 | Max query name length |
| `CONFIG_DNS_RESOLVER_MAX_ANSWER_SIZE` | 512 | Max DNS response size |
| `CONFIG_DNS_RESOLVER_ADDITIONAL_QUERIES` | 1 | Max CNAME chain depth |
| `CONFIG_DNS_NUM_CONCUR_QUERIES` | 1 | Concurrent queries |

## mDNS/LLMNR

| Option | Default | Description |
|--------|---------|-------------|
| `CONFIG_MDNS_RESOLVER` | n | Enable mDNS queries |
| `CONFIG_MDNS_RESPONDER` | n | Enable mDNS responder |
| `CONFIG_MDNS_RESPONDER_DNS_SD` | n | Enable DNS-SD in responder |
| `CONFIG_LLMNR_RESOLVER` | n | Enable LLMNR queries |
| `CONFIG_LLMNR_RESPONDER` | n | Enable LLMNR responder |
| `CONFIG_NET_HOSTNAME` | "zephyr" | Device hostname |

## Socket Offloading

| Option | Default | Description |
|--------|---------|-------------|
| `CONFIG_NET_SOCKETS_OFFLOAD` | n | Enable socket offloading |
| `CONFIG_NET_SOCKETS_OFFLOAD_DISPATCHER` | n | Socket dispatcher for multi-interface |

## Raw Sockets

| Option | Default | Description |
|--------|---------|-------------|
| `CONFIG_NET_SOCKETS_PACKET` | n | Raw L2 packets (AF_PACKET SOCK_RAW) |
| `CONFIG_NET_SOCKETS_PACKET_DGRAM` | n | L2 without header (AF_PACKET SOCK_DGRAM) |
| `CONFIG_NET_SOCKETS_INET_RAW` | n | Raw IP packets (AF_INET SOCK_RAW) |
| `CONFIG_NET_SOCKETS_CAN` | n | CAN bus sockets (AF_CAN) |

## Network Buffers

| Option | Default | Description |
|--------|---------|-------------|
| `CONFIG_NET_PKT_RX_COUNT` | 4 | Receive packet count |
| `CONFIG_NET_PKT_TX_COUNT` | 4 | Transmit packet count |
| `CONFIG_NET_BUF_RX_COUNT` | 16 | Receive buffer count |
| `CONFIG_NET_BUF_TX_COUNT` | 16 | Transmit buffer count |
| `CONFIG_NET_BUF_DATA_SIZE` | 128 | Buffer fragment size |

## File Descriptors

| Option | Default | Description |
|--------|---------|-------------|
| `CONFIG_ZVFS_OPEN_ADD_SIZE_NET_SAMPLE` | 0 | Additional FDs for networking |
| `CONFIG_NET_MAX_CONTEXTS` | 6 | Max network contexts (connections) |

## Example Configurations

### Minimal TCP Client
```
CONFIG_NETWORKING=y
CONFIG_NET_SOCKETS=y
CONFIG_NET_TCP=y
CONFIG_NET_IPV4=y
CONFIG_NET_PKT_RX_COUNT=8
CONFIG_NET_PKT_TX_COUNT=8
CONFIG_NET_BUF_RX_COUNT=16
CONFIG_NET_BUF_TX_COUNT=16
```

### TLS Client
```
CONFIG_NETWORKING=y
CONFIG_NET_SOCKETS=y
CONFIG_NET_TCP=y
CONFIG_NET_IPV4=y

CONFIG_NET_SOCKETS_SOCKOPT_TLS=y
CONFIG_MBEDTLS=y
CONFIG_MBEDTLS_BUILTIN=y
CONFIG_MBEDTLS_ENABLE_HEAP=y
CONFIG_MBEDTLS_HEAP_SIZE=60000
CONFIG_MBEDTLS_SSL_MAX_CONTENT_LEN=4096

CONFIG_MAIN_STACK_SIZE=4096
CONFIG_NET_PKT_RX_COUNT=16
CONFIG_NET_PKT_TX_COUNT=16
CONFIG_NET_BUF_RX_COUNT=32
CONFIG_NET_BUF_TX_COUNT=32
```

### TLS Server
```
CONFIG_NETWORKING=y
CONFIG_NET_SOCKETS=y
CONFIG_NET_TCP=y
CONFIG_NET_IPV4=y
CONFIG_NET_IPV6=y

CONFIG_NET_SOCKETS_SOCKOPT_TLS=y
CONFIG_NET_SOCKETS_TLS_MAX_CONTEXTS=4
CONFIG_MBEDTLS=y
CONFIG_MBEDTLS_BUILTIN=y
CONFIG_MBEDTLS_ENABLE_HEAP=y
CONFIG_MBEDTLS_HEAP_SIZE=80000

CONFIG_MAIN_STACK_SIZE=4096
CONFIG_NET_MAX_CONTEXTS=10
```

### DTLS Client
```
CONFIG_NETWORKING=y
CONFIG_NET_SOCKETS=y
CONFIG_NET_UDP=y
CONFIG_NET_IPV4=y

CONFIG_NET_SOCKETS_SOCKOPT_TLS=y
CONFIG_NET_SOCKETS_ENABLE_DTLS=y
CONFIG_NET_SOCKETS_DTLS_TIMEOUT=30000
CONFIG_MBEDTLS=y
CONFIG_MBEDTLS_BUILTIN=y
CONFIG_MBEDTLS_ENABLE_HEAP=y
CONFIG_MBEDTLS_HEAP_SIZE=60000
```

### DNS with mDNS
```
CONFIG_NETWORKING=y
CONFIG_NET_SOCKETS=y
CONFIG_NET_TCP=y
CONFIG_NET_UDP=y
CONFIG_NET_IPV4=y

CONFIG_DNS_RESOLVER=y
CONFIG_DNS_SERVER_IP_ADDRESSES=y
CONFIG_DNS_SERVER1="8.8.8.8"

CONFIG_MDNS_RESOLVER=y
CONFIG_MDNS_RESPONDER=y
CONFIG_NET_HOSTNAME="mydevice"
```

### Full Network Stack
```
CONFIG_NETWORKING=y
CONFIG_NET_SOCKETS=y
CONFIG_POSIX_API=y
CONFIG_NET_TCP=y
CONFIG_NET_UDP=y
CONFIG_NET_IPV4=y
CONFIG_NET_IPV6=y

CONFIG_NET_SOCKETS_SOCKOPT_TLS=y
CONFIG_NET_SOCKETS_ENABLE_DTLS=y
CONFIG_MBEDTLS=y
CONFIG_MBEDTLS_BUILTIN=y
CONFIG_MBEDTLS_ENABLE_HEAP=y
CONFIG_MBEDTLS_HEAP_SIZE=80000

CONFIG_DNS_RESOLVER=y
CONFIG_MDNS_RESOLVER=y
CONFIG_LLMNR_RESOLVER=y

CONFIG_NET_PKT_RX_COUNT=32
CONFIG_NET_PKT_TX_COUNT=32
CONFIG_NET_BUF_RX_COUNT=64
CONFIG_NET_BUF_TX_COUNT=64
CONFIG_NET_MAX_CONTEXTS=16
CONFIG_MAIN_STACK_SIZE=4096
```
