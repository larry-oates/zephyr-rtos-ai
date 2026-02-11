# BSD Sockets API

## Table of Contents
- [Socket Functions](#socket-functions)
- [UDP Datagram Sockets](#udp-datagram-sockets)
- [Receiving Data](#receiving-data)
- [Socket Options](#socket-options)
- [Non-Blocking I/O](#non-blocking-io)
- [poll() and select()](#poll-and-select)
- [Short Read/Write Behavior](#short-readwrite-behavior)
- [IPv6 Considerations](#ipv6-considerations)

## Socket Functions

### socket()

```c
int socket(int family, int type, int protocol);
```

| Parameter | Values |
|-----------|--------|
| family | `AF_INET` (IPv4), `AF_INET6` (IPv6), `AF_PACKET` (raw L2), `AF_CAN` |
| type | `SOCK_STREAM` (TCP), `SOCK_DGRAM` (UDP), `SOCK_RAW` |
| protocol | `IPPROTO_TCP`, `IPPROTO_UDP`, `IPPROTO_TLS_1_2`, `IPPROTO_DTLS_1_2` |

Returns: socket file descriptor on success, -1 on error (check `errno`)

### connect()

```c
int connect(int sock, const struct sockaddr *addr, socklen_t addrlen);
```

For TCP: Initiates 3-way handshake (blocking by default)
For UDP: Sets default peer address for `send()`

### bind()

```c
int bind(int sock, const struct sockaddr *addr, socklen_t addrlen);
```

Associates socket with local address. For servers, use `INADDR_ANY` (0.0.0.0) or `in6addr_any`.

### listen()

```c
int listen(int sock, int backlog);
```

Marks socket as passive (server). `backlog` specifies max pending connections.

### accept()

```c
int accept(int sock, struct sockaddr *addr, socklen_t *addrlen);
```

Blocks until a client connects. Returns new socket for the connection.

### send() / sendto()

```c
ssize_t send(int sock, const void *buf, size_t len, int flags);
ssize_t sendto(int sock, const void *buf, size_t len, int flags,
               const struct sockaddr *dest_addr, socklen_t addrlen);
```

| Flag | Description |
|------|-------------|
| MSG_DONTWAIT | Non-blocking for this call only |
| MSG_MORE | More data coming (cork) |

### recv() / recvfrom()

```c
ssize_t recv(int sock, void *buf, size_t len, int flags);
ssize_t recvfrom(int sock, void *buf, size_t len, int flags,
                 struct sockaddr *src_addr, socklen_t *addrlen);
```

| Flag | Description |
|------|-------------|
| MSG_PEEK | Read without removing from queue |
| MSG_DONTWAIT | Non-blocking for this call only |
| MSG_WAITALL | Block until full amount received |
| MSG_TRUNC | Return real datagram length even if truncated |

### close()

```c
int close(int sock);
```

Terminates connection and releases socket resources.

### shutdown()

```c
int shutdown(int sock, int how);
```

| how | Effect |
|-----|--------|
| SHUT_RD (0) | No more receives |
| SHUT_WR (1) | No more sends (sends FIN) |
| SHUT_RDWR (2) | Both |

## UDP Datagram Sockets

```c
#include <zephyr/net/socket.h>

int udp_client(void)
{
    int sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);

    struct sockaddr_in dest = {
        .sin_family = AF_INET,
        .sin_port = htons(5000),
    };
    inet_pton(AF_INET, "192.168.1.100", &dest.sin_addr);

    /* Option 1: sendto() each time */
    sendto(sock, "Hello", 5, 0, (struct sockaddr *)&dest, sizeof(dest));

    /* Option 2: connect() then send() */
    connect(sock, (struct sockaddr *)&dest, sizeof(dest));
    send(sock, "Hello", 5, 0);

    close(sock);
    return 0;
}

int udp_server(void)
{
    int sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);

    struct sockaddr_in addr = {
        .sin_family = AF_INET,
        .sin_port = htons(5000),
        .sin_addr.s_addr = INADDR_ANY,
    };
    bind(sock, (struct sockaddr *)&addr, sizeof(addr));

    char buf[256];
    struct sockaddr_in client;
    socklen_t client_len = sizeof(client);

    int len = recvfrom(sock, buf, sizeof(buf), 0,
                       (struct sockaddr *)&client, &client_len);

    /* Echo back */
    sendto(sock, buf, len, 0, (struct sockaddr *)&client, client_len);

    close(sock);
    return 0;
}
```

## Receiving Data

### Complete receive helper (TCP)

TCP is a stream protocol; data may arrive in fragments:

```c
int recv_all(int sock, void *buf, size_t len)
{
    size_t received = 0;
    char *ptr = buf;

    while (received < len) {
        int ret = recv(sock, ptr + received, len - received, 0);
        if (ret < 0) {
            return -errno;
        }
        if (ret == 0) {
            return received;  /* Connection closed */
        }
        received += ret;
    }
    return received;
}
```

### Complete send helper (TCP)

```c
int send_all(int sock, const void *buf, size_t len)
{
    size_t sent = 0;
    const char *ptr = buf;

    while (sent < len) {
        int ret = send(sock, ptr + sent, len - sent, 0);
        if (ret < 0) {
            return -errno;
        }
        sent += ret;
    }
    return sent;
}
```

## Socket Options

### setsockopt() / getsockopt()

```c
int setsockopt(int sock, int level, int optname, const void *optval, socklen_t optlen);
int getsockopt(int sock, int level, int optname, void *optval, socklen_t *optlen);
```

### Common SOL_SOCKET Options

```c
/* Reuse address (for server restart) */
int optval = 1;
setsockopt(sock, SOL_SOCKET, SO_REUSEADDR, &optval, sizeof(optval));

/* Receive timeout (5 seconds) */
struct timeval tv = { .tv_sec = 5, .tv_usec = 0 };
setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));

/* Send timeout */
setsockopt(sock, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof(tv));

/* Bind to specific network interface */
struct ifreq ifr = { .ifr_name = "eth0" };
setsockopt(sock, SOL_SOCKET, SO_BINDTODEVICE, &ifr, sizeof(ifr));
```

### TCP Options (IPPROTO_TCP)

```c
/* Disable Nagle algorithm (send immediately) */
int optval = 1;
setsockopt(sock, IPPROTO_TCP, TCP_NODELAY, &optval, sizeof(optval));
```

### IPv6 Options (IPPROTO_IPV6)

```c
/* IPv6 only (don't accept IPv4-mapped addresses) */
int optval = 1;
setsockopt(sock, IPPROTO_IPV6, IPV6_V6ONLY, &optval, sizeof(optval));
```

## Non-Blocking I/O

### fcntl method (persistent)

```c
#include <fcntl.h>

int flags = fcntl(sock, F_GETFL, 0);
fcntl(sock, F_SETFL, flags | O_NONBLOCK);

/* Now recv/send return -1 with errno=EAGAIN if would block */
int ret = recv(sock, buf, len, 0);
if (ret < 0 && (errno == EAGAIN || errno == EWOULDBLOCK)) {
    /* No data available, try again later */
}
```

### MSG_DONTWAIT (per-call)

```c
int ret = recv(sock, buf, len, MSG_DONTWAIT);
```

## poll() and select()

### poll() - Preferred

```c
#include <zephyr/net/socket.h>

struct zsock_pollfd fds[3];

/* TCP server socket */
fds[0].fd = server_sock;
fds[0].events = ZSOCK_POLLIN;

/* Connected client 1 */
fds[1].fd = client1_sock;
fds[1].events = ZSOCK_POLLIN;

/* Connected client 2 */
fds[2].fd = client2_sock;
fds[2].events = ZSOCK_POLLIN | ZSOCK_POLLOUT;

int ret = zsock_poll(fds, 3, 5000);  /* 5 sec timeout, -1 = infinite */
if (ret < 0) {
    /* Error */
} else if (ret == 0) {
    /* Timeout */
} else {
    if (fds[0].revents & ZSOCK_POLLIN) {
        /* New connection waiting */
        int new_client = accept(server_sock, ...);
    }
    if (fds[1].revents & ZSOCK_POLLIN) {
        /* Client 1 has data */
        recv(client1_sock, ...);
    }
    if (fds[1].revents & ZSOCK_POLLHUP) {
        /* Client 1 disconnected */
        close(client1_sock);
    }
}
```

### Poll Events

| Event | Direction | Description |
|-------|-----------|-------------|
| ZSOCK_POLLIN | Input | Data available to read |
| ZSOCK_POLLOUT | Input | Socket ready to write |
| ZSOCK_POLLERR | Output | Error occurred |
| ZSOCK_POLLHUP | Output | Peer closed connection |
| ZSOCK_POLLNVAL | Output | Invalid file descriptor |

### select() - POSIX compatible

```c
#include <sys/select.h>

fd_set readfds;
FD_ZERO(&readfds);
FD_SET(sock1, &readfds);
FD_SET(sock2, &readfds);

struct timeval tv = { .tv_sec = 5, .tv_usec = 0 };
int max_fd = (sock1 > sock2) ? sock1 : sock2;

int ret = select(max_fd + 1, &readfds, NULL, NULL, &tv);
if (ret > 0) {
    if (FD_ISSET(sock1, &readfds)) {
        /* sock1 has data */
    }
}
```

## Short Read/Write Behavior

Zephyr's socket implementation aggressively uses POSIX short-read/short-write semantics:

- `recv()` may return fewer bytes than requested
- `send()` may send fewer bytes than requested
- Always check return values and loop if needed

```c
/* WRONG: Assumes all data received at once */
recv(sock, buf, 1024, 0);

/* CORRECT: Handle partial receives */
int total = 0;
while (total < expected_len) {
    int ret = recv(sock, buf + total, expected_len - total, 0);
    if (ret <= 0) break;
    total += ret;
}
```

## IPv6 Considerations

### Dual-Stack Socket (IPv4 + IPv6)

```c
/* Create IPv6 socket that also accepts IPv4 */
int sock = socket(AF_INET6, SOCK_STREAM, IPPROTO_TCP);

/* Disable IPv6-only mode (allow IPv4-mapped addresses) */
int optval = 0;
setsockopt(sock, IPPROTO_IPV6, IPV6_V6ONLY, &optval, sizeof(optval));

struct sockaddr_in6 addr = {
    .sin6_family = AF_INET6,
    .sin6_port = htons(8080),
    .sin6_addr = in6addr_any,  /* Accepts both IPv4 and IPv6 */
};
bind(sock, (struct sockaddr *)&addr, sizeof(addr));
```

### IPv6-Only Socket

```c
int optval = 1;
setsockopt(sock, IPPROTO_IPV6, IPV6_V6ONLY, &optval, sizeof(optval));
```

### Address Structures

```c
/* IPv4 */
struct sockaddr_in addr4 = {
    .sin_family = AF_INET,
    .sin_port = htons(8080),
};
inet_pton(AF_INET, "192.168.1.1", &addr4.sin_addr);

/* IPv6 */
struct sockaddr_in6 addr6 = {
    .sin6_family = AF_INET6,
    .sin6_port = htons(8080),
};
inet_pton(AF_INET6, "2001:db8::1", &addr6.sin6_addr);
```
