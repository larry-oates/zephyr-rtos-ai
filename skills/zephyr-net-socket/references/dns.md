# DNS Resolution

## Table of Contents
- [Overview](#overview)
- [getaddrinfo (BSD Sockets API)](#getaddrinfo-bsd-sockets-api)
- [dns_resolve API (Async)](#dns_resolve-api-async)
- [mDNS Support](#mdns-support)
- [LLMNR Support](#llmnr-support)
- [Service Discovery (DNS-SD)](#service-discovery-dns-sd)
- [DNS Server Configuration](#dns-server-configuration)

## Overview

Zephyr provides two DNS resolution approaches:

| API | Style | Use Case |
|-----|-------|----------|
| `getaddrinfo()` | Synchronous (blocking) | Simple client apps, POSIX compatibility |
| `dns_resolve` | Asynchronous (callback) | Event-driven apps, multiple queries |

Both support:
- IPv4 (A records) and IPv6 (AAAA records)
- CNAME resolution (automatic chaining)
- mDNS (`.local` domains)
- LLMNR (link-local name resolution)

## getaddrinfo (BSD Sockets API)

Standard POSIX-compatible synchronous DNS lookup.

### Basic Usage

```c
#include <zephyr/net/socket.h>

int resolve_and_connect(const char *hostname, const char *port)
{
    struct addrinfo hints = {
        .ai_family = AF_UNSPEC,     /* IPv4 or IPv6 */
        .ai_socktype = SOCK_STREAM, /* TCP */
    };
    struct addrinfo *res;

    int ret = getaddrinfo(hostname, port, &hints, &res);
    if (ret != 0) {
        printk("DNS lookup failed: %d\n", ret);
        return -1;
    }

    /* Try each result until one works */
    struct addrinfo *rp;
    int sock = -1;
    for (rp = res; rp != NULL; rp = rp->ai_next) {
        sock = socket(rp->ai_family, rp->ai_socktype, rp->ai_protocol);
        if (sock < 0) {
            continue;
        }

        if (connect(sock, rp->ai_addr, rp->ai_addrlen) == 0) {
            break;  /* Success */
        }

        close(sock);
        sock = -1;
    }

    freeaddrinfo(res);  /* Always free when done */

    if (sock < 0) {
        printk("Could not connect\n");
        return -1;
    }

    return sock;
}
```

### Hints Structure

```c
struct addrinfo {
    int ai_flags;           /* AI_* flags */
    int ai_family;          /* AF_INET, AF_INET6, AF_UNSPEC */
    int ai_socktype;        /* SOCK_STREAM, SOCK_DGRAM */
    int ai_protocol;        /* IPPROTO_TCP, IPPROTO_UDP */
    socklen_t ai_addrlen;   /* Length of ai_addr */
    struct sockaddr *ai_addr;  /* Socket address */
    char *ai_canonname;     /* Canonical name */
    struct addrinfo *ai_next;  /* Next result */
};
```

### Hint Flags

| Flag | Description |
|------|-------------|
| `AI_PASSIVE` | For server binding (returns `INADDR_ANY`) |
| `AI_CANONNAME` | Request canonical name in result |
| `AI_NUMERICHOST` | Hostname is numeric (skip DNS) |
| `AI_NUMERICSERV` | Service is numeric port |
| `AI_V4MAPPED` | Return IPv4-mapped IPv6 if no IPv6 |
| `AI_ADDRCONFIG` | Only return if host has that address family |

### Return Values

| Value | Meaning |
|-------|---------|
| 0 | Success |
| EAI_AGAIN | Temporary failure |
| EAI_FAIL | Non-recoverable failure |
| EAI_MEMORY | Memory allocation failure |
| EAI_NONAME | Name not found |
| EAI_SERVICE | Service not found for socket type |

### IPv4-Only Lookup

```c
struct addrinfo hints = {
    .ai_family = AF_INET,       /* Only IPv4 */
    .ai_socktype = SOCK_STREAM,
};
getaddrinfo("example.com", "80", &hints, &res);
```

### IPv6-Only Lookup

```c
struct addrinfo hints = {
    .ai_family = AF_INET6,      /* Only IPv6 */
    .ai_socktype = SOCK_STREAM,
};
getaddrinfo("example.com", "80", &hints, &res);
```

## dns_resolve API (Async)

Asynchronous DNS resolution with callbacks. Better for event-driven applications.

### Basic Query

```c
#include <zephyr/net/dns_resolve.h>

#define DNS_TIMEOUT (5 * MSEC_PER_SEC)

static void dns_callback(enum dns_resolve_status status,
                         struct dns_addrinfo *info,
                         void *user_data)
{
    char addr_str[NET_IPV6_ADDR_LEN];

    switch (status) {
    case DNS_EAI_INPROGRESS:
        if (info->ai_family == AF_INET) {
            net_addr_ntop(AF_INET,
                         &net_sin(&info->ai_addr)->sin_addr,
                         addr_str, sizeof(addr_str));
        } else if (info->ai_family == AF_INET6) {
            net_addr_ntop(AF_INET6,
                         &net_sin6(&info->ai_addr)->sin6_addr,
                         addr_str, sizeof(addr_str));
        }
        printk("Resolved: %s\n", addr_str);
        break;

    case DNS_EAI_ALLDONE:
        printk("DNS resolution complete\n");
        break;

    case DNS_EAI_CANCELED:
        printk("DNS query canceled\n");
        break;

    case DNS_EAI_FAIL:
        printk("DNS resolution failed\n");
        break;

    case DNS_EAI_NODATA:
        printk("No data found\n");
        break;
    }
}

int start_dns_lookup(const char *hostname)
{
    uint16_t dns_id;

    int ret = dns_get_addr_info(hostname,
                                DNS_QUERY_TYPE_A,  /* IPv4 */
                                &dns_id,
                                dns_callback,
                                NULL,              /* user_data */
                                DNS_TIMEOUT);
    if (ret < 0) {
        printk("Failed to start DNS query: %d\n", ret);
        return ret;
    }

    printk("DNS query started, ID: %u\n", dns_id);
    return 0;
}
```

### Query Types

| Type | Record | Description |
|------|--------|-------------|
| `DNS_QUERY_TYPE_A` | A | IPv4 address |
| `DNS_QUERY_TYPE_AAAA` | AAAA | IPv6 address |

### Canceling Queries

```c
uint16_t dns_id;
dns_get_addr_info("example.com", DNS_QUERY_TYPE_A, &dns_id, callback, NULL, 5000);

/* Cancel before timeout */
dns_cancel_addr_info(dns_id);
```

### Using Custom DNS Context

```c
/* Get default context */
struct dns_resolve_context *ctx = dns_resolve_get_default();

/* Or create custom context with specific servers */
static struct dns_resolve_context my_ctx;

static const char *dns_servers[] = { "8.8.8.8", NULL };
dns_resolve_init(&my_ctx, dns_servers, NULL);

dns_resolve_name(&my_ctx, "example.com", DNS_QUERY_TYPE_A,
                 &dns_id, callback, NULL, DNS_TIMEOUT);
```

## mDNS Support

Multicast DNS for `.local` domains (RFC 6762).

### Enable mDNS

```
CONFIG_MDNS_RESOLVER=y
CONFIG_MDNS_RESPONDER=y  /* To advertise services */
```

### mDNS Queries

mDNS is automatic for `.local` hostnames:

```c
/* Uses mDNS automatically */
getaddrinfo("mydevice.local", "80", &hints, &res);

/* Or with async API */
dns_get_addr_info("mydevice.local", DNS_QUERY_TYPE_A,
                  &dns_id, callback, NULL, DNS_TIMEOUT);
```

### mDNS Responder

Register a hostname for your device:

```c
#include <zephyr/net/mdns_responder.h>

/* Device will respond to "zephyr.local" */
/* Configured via Kconfig */
```

Kconfig:
```
CONFIG_MDNS_RESPONDER=y
CONFIG_MDNS_RESPONDER_DNS_SD=y  /* For service discovery */
CONFIG_NET_HOSTNAME="zephyr"    /* Responds to zephyr.local */
```

## LLMNR Support

Link-Local Multicast Name Resolution (RFC 4795) for local network resolution without DNS server.

### Enable LLMNR

```
CONFIG_LLMNR_RESOLVER=y
CONFIG_LLMNR_RESPONDER=y
```

LLMNR is used automatically for unqualified hostnames that don't match mDNS patterns.

## Service Discovery (DNS-SD)

Query for services on the network (RFC 6763).

```c
#include <zephyr/net/dns_resolve.h>

static void service_callback(enum dns_resolve_status status,
                             struct dns_addrinfo *info,
                             void *user_data)
{
    if (status == DNS_EAI_INPROGRESS && info) {
        if (info->ai_family == AF_LOCAL) {
            /* Service discovery result */
            char service_name[128];
            memcpy(service_name, info->ai_canonname,
                   MIN(info->ai_addrlen, sizeof(service_name) - 1));
            printk("Found service: %s\n", service_name);
        }
    }
}

int discover_services(void)
{
    int ret = dns_resolve_service(dns_resolve_get_default(),
                                  "_http._tcp.local",
                                  NULL,
                                  service_callback,
                                  NULL,
                                  5000);
    return ret;
}
```

Kconfig for large service discovery responses:
```
CONFIG_DNS_RESOLVER_MAX_ANSWER_SIZE=1024
CONFIG_DNS_RESOLVER_MAX_NAME_LEN=128
```

## DNS Server Configuration

### Static Configuration (Kconfig)

```
CONFIG_DNS_RESOLVER=y
CONFIG_DNS_SERVER_IP_ADDRESSES=y
CONFIG_DNS_SERVER1="8.8.8.8"
CONFIG_DNS_SERVER2="8.8.4.4"
CONFIG_DNS_SERVER3="2001:4860:4860::8888"  /* IPv6 */
```

### Dynamic Configuration (DHCP)

DNS servers are automatically configured when using DHCP:

```
CONFIG_NET_DHCPV4=y
# DNS servers from DHCP are used automatically
```

### Runtime Configuration

```c
#include <zephyr/net/dns_resolve.h>

static struct dns_resolve_context dns_ctx;

int configure_dns_servers(void)
{
    static const char *servers[] = {
        "192.168.1.1",   /* Primary */
        "8.8.8.8",       /* Fallback */
        NULL
    };

    return dns_resolve_init(&dns_ctx, servers, NULL);
}
```

### DNS Resolver Kconfig Options

| Option | Default | Description |
|--------|---------|-------------|
| `CONFIG_DNS_RESOLVER` | n | Enable DNS resolver |
| `CONFIG_DNS_RESOLVER_MAX_QUERY_LEN` | 64 | Max query name length |
| `CONFIG_DNS_RESOLVER_MAX_ANSWER_SIZE` | 512 | Max DNS response size |
| `CONFIG_DNS_RESOLVER_MAX_NAME_LEN` | 64 | Max resolved name length |
| `CONFIG_DNS_RESOLVER_ADDITIONAL_QUERIES` | 1 | Max CNAME chain depth |
| `CONFIG_DNS_NUM_CONCUR_QUERIES` | 1 | Concurrent query limit |
