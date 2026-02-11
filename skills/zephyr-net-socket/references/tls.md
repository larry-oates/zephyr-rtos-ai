# TLS/DTLS Secure Sockets

## Table of Contents
- [Overview](#overview)
- [TLS Credentials](#tls-credentials)
- [TLS Client](#tls-client)
- [TLS Server](#tls-server)
- [DTLS (UDP)](#dtls-udp)
- [TLS Socket Options](#tls-socket-options)
- [Certificate Formats](#certificate-formats)
- [PSK Authentication](#psk-authentication)
- [Session Caching](#session-caching)
- [Troubleshooting](#troubleshooting)

## Overview

Zephyr secure sockets use mbedTLS to provide TLS 1.2 (TCP) and DTLS 1.2 (UDP) support. The API extends standard BSD sockets with:

1. Secure protocol types (`IPPROTO_TLS_1_2`, `IPPROTO_DTLS_1_2`)
2. TLS-specific socket options (`SOL_TLS`)
3. Credential management via `sec_tag_t` tags

## TLS Credentials

### Credential Types

| Type | Description | Paired With |
|------|-------------|-------------|
| `TLS_CREDENTIAL_CA_CERTIFICATE` | Trusted CA cert (verify server) | - |
| `TLS_CREDENTIAL_PUBLIC_CERTIFICATE` | Client/server cert | `TLS_CREDENTIAL_PRIVATE_KEY` |
| `TLS_CREDENTIAL_PRIVATE_KEY` | Private key | `TLS_CREDENTIAL_PUBLIC_CERTIFICATE` |
| `TLS_CREDENTIAL_PSK` | Pre-shared key | `TLS_CREDENTIAL_PSK_ID` |
| `TLS_CREDENTIAL_PSK_ID` | PSK identity | `TLS_CREDENTIAL_PSK` |

### Registering Credentials

```c
#include <zephyr/net/tls_credentials.h>

#define CA_TAG 1
#define CLIENT_TAG 2
#define PSK_TAG 3

/* CA certificate for server verification */
static const unsigned char ca_cert[] = { /* DER data */ };

/* Client certificate and key for mutual TLS */
static const unsigned char client_cert[] = { /* DER data */ };
static const unsigned char client_key[] = { /* DER data */ };

int setup_credentials(void)
{
    int ret;

    /* Register CA certificate */
    ret = tls_credential_add(CA_TAG, TLS_CREDENTIAL_CA_CERTIFICATE,
                             ca_cert, sizeof(ca_cert));
    if (ret < 0) {
        return ret;
    }

    /* Register client cert and key (same tag for paired credentials) */
    ret = tls_credential_add(CLIENT_TAG, TLS_CREDENTIAL_PUBLIC_CERTIFICATE,
                             client_cert, sizeof(client_cert));
    if (ret < 0) {
        return ret;
    }

    ret = tls_credential_add(CLIENT_TAG, TLS_CREDENTIAL_PRIVATE_KEY,
                             client_key, sizeof(client_key));
    if (ret < 0) {
        return ret;
    }

    return 0;
}
```

### Credential Management API

```c
/* Add credential */
int tls_credential_add(sec_tag_t tag, enum tls_credential_type type,
                       const void *cred, size_t credlen);

/* Get credential (for inspection) */
int tls_credential_get(sec_tag_t tag, enum tls_credential_type type,
                       void *cred, size_t *credlen);

/* Delete credential */
int tls_credential_delete(sec_tag_t tag, enum tls_credential_type type);
```

## TLS Client

### Basic TLS Client

```c
#include <zephyr/net/socket.h>
#include <zephyr/net/tls_credentials.h>

#define CA_TAG 1

int tls_client(const char *host, uint16_t port)
{
    int sock, ret;

    /* 1. Create TLS socket */
    sock = socket(AF_INET, SOCK_STREAM, IPPROTO_TLS_1_2);
    if (sock < 0) {
        return -errno;
    }

    /* 2. Set credentials */
    sec_tag_t sec_tags[] = { CA_TAG };
    ret = setsockopt(sock, SOL_TLS, TLS_SEC_TAG_LIST,
                     sec_tags, sizeof(sec_tags));
    if (ret < 0) {
        close(sock);
        return -errno;
    }

    /* 3. Set hostname for SNI and certificate verification */
    ret = setsockopt(sock, SOL_TLS, TLS_HOSTNAME, host, strlen(host) + 1);
    if (ret < 0) {
        close(sock);
        return -errno;
    }

    /* 4. Connect (TLS handshake happens automatically) */
    struct sockaddr_in addr = {
        .sin_family = AF_INET,
        .sin_port = htons(port),
    };
    inet_pton(AF_INET, "1.2.3.4", &addr.sin_addr);  /* Use resolved IP */

    ret = connect(sock, (struct sockaddr *)&addr, sizeof(addr));
    if (ret < 0) {
        close(sock);
        return -errno;
    }

    /* 5. Use socket normally */
    send(sock, "GET / HTTP/1.1\r\nHost: example.com\r\n\r\n", 38, 0);

    char buf[512];
    int len = recv(sock, buf, sizeof(buf) - 1, 0);
    if (len > 0) {
        buf[len] = '\0';
        printk("%s\n", buf);
    }

    close(sock);
    return 0;
}
```

### Mutual TLS (Client Certificate)

```c
#define CA_TAG 1
#define CLIENT_TAG 2  /* Has both cert and key */

sec_tag_t sec_tags[] = { CA_TAG, CLIENT_TAG };
setsockopt(sock, SOL_TLS, TLS_SEC_TAG_LIST, sec_tags, sizeof(sec_tags));
```

## TLS Server

```c
#include <zephyr/net/socket.h>
#include <zephyr/net/tls_credentials.h>

#define SERVER_TAG 1  /* Has server cert + private key */

int tls_server(uint16_t port)
{
    int sock, client, ret;

    /* Create TLS server socket */
    sock = socket(AF_INET, SOCK_STREAM, IPPROTO_TLS_1_2);
    if (sock < 0) {
        return -errno;
    }

    /* Set server credentials */
    sec_tag_t sec_tags[] = { SERVER_TAG };
    setsockopt(sock, SOL_TLS, TLS_SEC_TAG_LIST, sec_tags, sizeof(sec_tags));

    /* Optional: Require client certificate */
    int verify = TLS_PEER_VERIFY_REQUIRED;
    setsockopt(sock, SOL_TLS, TLS_PEER_VERIFY, &verify, sizeof(verify));

    /* Bind and listen */
    struct sockaddr_in addr = {
        .sin_family = AF_INET,
        .sin_port = htons(port),
        .sin_addr.s_addr = INADDR_ANY,
    };
    bind(sock, (struct sockaddr *)&addr, sizeof(addr));
    listen(sock, 5);

    /* Accept connections (TLS handshake on accept) */
    while (1) {
        client = accept(sock, NULL, NULL);
        if (client < 0) {
            continue;
        }

        char buf[256];
        int len = recv(client, buf, sizeof(buf), 0);
        if (len > 0) {
            send(client, buf, len, 0);
        }

        close(client);
    }

    close(sock);
    return 0;
}
```

## DTLS (UDP)

DTLS provides security for UDP datagrams.

### DTLS Client

```c
int dtls_client(void)
{
    int sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_DTLS_1_2);

    sec_tag_t tags[] = { CA_TAG };
    setsockopt(sock, SOL_TLS, TLS_SEC_TAG_LIST, tags, sizeof(tags));

    /* For DTLS client role is implicit from connect() */
    struct sockaddr_in addr = { /* ... */ };
    connect(sock, (struct sockaddr *)&addr, sizeof(addr));

    /* Handshake happens on first send or explicitly */
    send(sock, "Hello", 5, 0);

    char buf[256];
    recv(sock, buf, sizeof(buf), 0);

    close(sock);
    return 0;
}
```

### DTLS Server

```c
int dtls_server(void)
{
    int sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_DTLS_1_2);

    sec_tag_t tags[] = { SERVER_TAG };
    setsockopt(sock, SOL_TLS, TLS_SEC_TAG_LIST, tags, sizeof(tags));

    /* Set DTLS role to server (required for DTLS) */
    int role = TLS_DTLS_ROLE_SERVER;
    setsockopt(sock, SOL_TLS, TLS_DTLS_ROLE, &role, sizeof(role));

    struct sockaddr_in addr = {
        .sin_family = AF_INET,
        .sin_port = htons(5684),
        .sin_addr.s_addr = INADDR_ANY,
    };
    bind(sock, (struct sockaddr *)&addr, sizeof(addr));

    char buf[256];
    struct sockaddr_in client;
    socklen_t client_len = sizeof(client);

    /* recvfrom triggers handshake */
    int len = recvfrom(sock, buf, sizeof(buf), 0,
                       (struct sockaddr *)&client, &client_len);

    sendto(sock, buf, len, 0, (struct sockaddr *)&client, client_len);

    close(sock);
    return 0;
}
```

## TLS Socket Options

All options use level `SOL_TLS` (282).

### TLS_SEC_TAG_LIST

Array of `sec_tag_t` referencing credentials:

```c
sec_tag_t tags[] = { CA_TAG, CLIENT_TAG };
setsockopt(sock, SOL_TLS, TLS_SEC_TAG_LIST, tags, sizeof(tags));
```

### TLS_HOSTNAME

Server hostname for SNI and certificate CN/SAN verification:

```c
char hostname[] = "api.example.com";
setsockopt(sock, SOL_TLS, TLS_HOSTNAME, hostname, sizeof(hostname));

/* Disable hostname verification */
setsockopt(sock, SOL_TLS, TLS_HOSTNAME, NULL, 0);
```

### TLS_PEER_VERIFY

Peer certificate verification level:

```c
int verify = TLS_PEER_VERIFY_REQUIRED;  /* 2 = required (default for clients) */
/* TLS_PEER_VERIFY_NONE = 0, TLS_PEER_VERIFY_OPTIONAL = 1 */
setsockopt(sock, SOL_TLS, TLS_PEER_VERIFY, &verify, sizeof(verify));
```

### TLS_CIPHERSUITE_LIST

Restrict allowed ciphersuites (IANA IDs):

```c
int suites[] = {
    0x009F,  /* TLS_DHE_RSA_WITH_AES_256_GCM_SHA384 */
    0x00A3,  /* TLS_DHE_DSS_WITH_AES_256_GCM_SHA384 */
};
setsockopt(sock, SOL_TLS, TLS_CIPHERSUITE_LIST, suites, sizeof(suites));
```

### TLS_CIPHERSUITE_USED (read-only)

Get negotiated ciphersuite after handshake:

```c
int suite;
socklen_t len = sizeof(suite);
getsockopt(sock, SOL_TLS, TLS_CIPHERSUITE_USED, &suite, &len);
```

### TLS_ALPN_LIST

Application Layer Protocol Negotiation:

```c
const char *alpn[] = { "h2", "http/1.1", NULL };
setsockopt(sock, SOL_TLS, TLS_ALPN_LIST, alpn, sizeof(alpn));
```

### TLS_DTLS_ROLE

For DTLS, explicitly set client/server role:

```c
int role = TLS_DTLS_ROLE_SERVER;  /* 1 = server, 0 = client (default) */
setsockopt(sock, SOL_TLS, TLS_DTLS_ROLE, &role, sizeof(role));
```

### TLS_DTLS_HANDSHAKE_TIMEOUT_MIN/MAX

DTLS handshake retransmission timeouts (milliseconds):

```c
int min_timeout = 1000;  /* 1 second */
int max_timeout = 60000; /* 60 seconds */
setsockopt(sock, SOL_TLS, TLS_DTLS_HANDSHAKE_TIMEOUT_MIN, &min_timeout, sizeof(min_timeout));
setsockopt(sock, SOL_TLS, TLS_DTLS_HANDSHAKE_TIMEOUT_MAX, &max_timeout, sizeof(max_timeout));
```

### TLS_NATIVE

Force native TLS implementation when offloading is available:

```c
int native = 1;
setsockopt(sock, SOL_TLS, TLS_NATIVE, &native, sizeof(native));
```

## Certificate Formats

### DER (Binary) - Default

Certificates must be DER-encoded by default:

```c
/* In ca_certificate.h */
static const unsigned char ca_cert[] = {
    0x30, 0x82, 0x03, 0x77, /* ... DER bytes ... */
};
```

### PEM Support

Enable PEM with `CONFIG_MBEDTLS_PEM_CERTIFICATE_FORMAT=y`:

```c
static const char ca_cert_pem[] =
    "-----BEGIN CERTIFICATE-----\n"
    "MIIDxTCCAq2gAwIBAgIQAqxcJmoLQJuPC3nyrkYldzANBgkqhkiG9w0BAQsFADBs\n"
    /* ... */
    "-----END CERTIFICATE-----\n";
```

### Converting Certificates

```bash
# PEM to DER
openssl x509 -in cert.pem -outform DER -out cert.der

# DER to C array
xxd -i cert.der > cert.h
```

## PSK Authentication

Pre-shared key authentication (no certificates):

```c
#define PSK_TAG 1

static const unsigned char psk[] = { 0x01, 0x02, 0x03, 0x04 };
static const char psk_id[] = "Client_identity";

int setup_psk(void)
{
    tls_credential_add(PSK_TAG, TLS_CREDENTIAL_PSK, psk, sizeof(psk));
    tls_credential_add(PSK_TAG, TLS_CREDENTIAL_PSK_ID, psk_id, strlen(psk_id));

    int sock = socket(AF_INET, SOCK_STREAM, IPPROTO_TLS_1_2);

    sec_tag_t tags[] = { PSK_TAG };
    setsockopt(sock, SOL_TLS, TLS_SEC_TAG_LIST, tags, sizeof(tags));

    /* Connect as usual */
    return 0;
}
```

Enable PSK in Kconfig:
```
CONFIG_MBEDTLS_KEY_EXCHANGE_PSK_ENABLED=y
```

## Session Caching

TLS session caching reduces handshake overhead for reconnections:

```c
/* Enable session caching */
int cache = TLS_SESSION_CACHE_ENABLED;
setsockopt(sock, SOL_TLS, TLS_SESSION_CACHE, &cache, sizeof(cache));

/* Purge session cache */
setsockopt(sock, SOL_TLS, TLS_SESSION_CACHE_PURGE, NULL, 0);
```

Kconfig:
```
CONFIG_NET_SOCKETS_TLS_MAX_CONTEXTS=4
CONFIG_MBEDTLS_SSL_SESSION_TICKETS=y
```

## Troubleshooting

### Handshake Failures

1. **Certificate errors**: Verify CA certificate matches server's issuer
2. **Hostname mismatch**: Check `TLS_HOSTNAME` matches cert CN/SAN
3. **Time sync**: mbedTLS validates cert dates; ensure RTC is set
4. **Memory**: Increase `CONFIG_MBEDTLS_HEAP_SIZE` (typically 60000+)

### Debug Logging

```
CONFIG_MBEDTLS_DEBUG=y
CONFIG_MBEDTLS_DEBUG_LEVEL=4
CONFIG_NET_SOCKETS_LOG_LEVEL_DBG=y
```

### Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| ENOENT | Credential not found | Verify `tls_credential_add()` called before socket |
| ENOMEM | mbedTLS heap exhausted | Increase `CONFIG_MBEDTLS_HEAP_SIZE` |
| ECONNRESET | Handshake failed | Check certs, hostname, server compatibility |
| EAGAIN (non-blocking TLS) | Same data must be resent | Retry `send()` with identical buffer |

### mbedTLS Heap Sizing

Minimum heap sizes:
- Basic TLS client: ~40KB
- TLS client with session caching: ~50KB
- TLS server: ~60KB
- Multiple concurrent connections: Add ~20KB per connection
