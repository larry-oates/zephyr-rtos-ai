# net_buf Data Operations

## Overview

The `net_buf` API provides four fundamental operations for manipulating buffer data. Understanding when to use each is key to efficient protocol encoding/decoding.

## Operation Summary

```
           ┌─────────────────────────────────────────────┐
           │              Buffer Storage                 │
           └─────────────────────────────────────────────┘
           ^                                             ^
           │                                             │
        __buf                                       __buf + size

           ┌───────────┬─────────────────┬───────────────┐
           │ headroom  │      data       │   tailroom    │
           └───────────┴─────────────────┴───────────────┘
                       ^                 ^
                       │                 │
                     data            data + len

           ◄── PUSH    ─── ADD ──►
           ◄── PULL    ─── REMOVE ──►
```

| Operation | Affects | Data Ptr | Length | Requirement |
|-----------|---------|----------|--------|-------------|
| **Add** | Tail | Unchanged | Increases | Tailroom available |
| **Remove** | Tail | Unchanged | Decreases | Data exists |
| **Push** | Head | Moves left | Increases | Headroom available |
| **Pull** | Head | Moves right | Decreases | Data exists |

---

## Encoding Data (Building Packets)

Use **Add** to append payload, **Push** to prepend headers.

### Example: Building a Protocol Packet

```c
/* Reserve headroom for headers */
struct net_buf *buf = net_buf_alloc(&pool, K_FOREVER);
net_buf_reserve(buf, HEADER_SIZE);

/* 1. Add payload to tail */
net_buf_add_mem(buf, payload_data, payload_len);

/* 2. Push header to head (after payload is ready) */
net_buf_push_u8(buf, PACKET_TYPE);
net_buf_push_le16(buf, total_length);
net_buf_push_be32(buf, sequence_number);
```

### Why Push After Add?

Headers often contain fields (like length) that depend on payload size. Build payload first, then prepend the header with the calculated length.

---

## Decoding Data (Parsing Packets)

Use **Pull** to consume headers, **Remove** to strip trailers.

### Example: Parsing a Protocol Packet

```c
/* Incoming buffer contains: [header][payload][crc] */

/* 1. Pull header fields from front */
uint8_t type = net_buf_pull_u8(buf);
uint16_t length = net_buf_pull_le16(buf);
uint32_t seq = net_buf_pull_be32(buf);

/* 2. Remove CRC from tail (if present) */
uint16_t crc = net_buf_remove_le16(buf);

/* 3. Remaining buf->data points to payload, buf->len is payload size */
process_payload(buf->data, buf->len);
```

---

## Endian-Aware Helpers

For multi-byte values, choose the correct endianness:

| Suffix | Meaning | Use Case |
|--------|---------|----------|
| `_le16`, `_le32`, `_le64` | Little-endian | Bluetooth, USB |
| `_be16`, `_be32`, `_be64` | Big-endian | Network protocols (IP, TCP) |

```c
/* Bluetooth (little-endian) */
net_buf_add_le16(buf, handle);
uint16_t handle = net_buf_pull_le16(buf);

/* Network (big-endian) */
net_buf_add_be32(buf, ip_addr);
uint32_t ip = net_buf_pull_be32(buf);
```

---

## Byte-by-Byte Protocol Parsing

For serial protocols (SLIP, HDLC), process one byte at a time:

```c
static int slip_process_byte(struct net_buf *buf, uint8_t c)
{
    switch (c) {
    case SLIP_END:
        return 1; /* Packet complete */
    case SLIP_ESC:
        /* Next byte is escaped */
        return -EAGAIN;
    default:
        if (net_buf_tailroom(buf) > 0) {
            net_buf_add_u8(buf, c);
            return 0;
        }
        return -ENOMEM;
    }
}
```

---

## Memory Copy Operations

### Add with Memory Copy

```c
/* Copy data to tail */
void *net_buf_add_mem(struct net_buf *buf, const void *mem, size_t len);

/* Example: Add raw bytes */
uint8_t data[] = {0x01, 0x02, 0x03};
net_buf_add_mem(buf, data, sizeof(data));
```

### Push with Memory Copy

```c
/* Copy data to head (prepend) */
void *net_buf_push_mem(struct net_buf *buf, const void *mem, size_t len);

/* Example: Prepend MAC header */
net_buf_push_mem(buf, mac_header, MAC_HEADER_LEN);
```

### Pull with Memory Copy

```c
/* Consume and get pointer to data */
void *net_buf_pull_mem(struct net_buf *buf, size_t len);

/* Example: Extract and copy header */
struct my_header *hdr = net_buf_pull_mem(buf, sizeof(*hdr));
```

---

## Checking Available Space

Before operations, verify space is available:

```c
/* Before Add: check tailroom */
if (net_buf_tailroom(buf) >= len) {
    net_buf_add_mem(buf, data, len);
}

/* Before Push: check headroom */
if (net_buf_headroom(buf) >= HEADER_SIZE) {
    net_buf_push_le16(buf, value);
}

/* Before Pull/Remove: check data exists */
if (buf->len >= sizeof(uint32_t)) {
    uint32_t val = net_buf_pull_le32(buf);
}
```

---

## Common Patterns

### Pattern 1: UART TX with snprintk

```c
struct net_buf *buf = net_buf_alloc(&tx_pool, K_FOREVER);

int len = snprintk(buf->data, net_buf_tailroom(buf),
                   "Message: %d\r\n", value);
net_buf_add(buf, len);  /* Update length after snprintk */

uart_tx(dev, buf->data, buf->len, SYS_FOREVER_US);
```

### Pattern 2: Protocol Frame Builder

```c
struct net_buf *build_frame(uint8_t cmd, const uint8_t *payload, size_t len)
{
    struct net_buf *buf = net_buf_alloc(&pool, K_FOREVER);

    /* Reserve space for frame header */
    net_buf_reserve(buf, FRAME_HEADER_SIZE);

    /* Add payload */
    net_buf_add_mem(buf, payload, len);

    /* Add CRC at tail */
    uint16_t crc = calc_crc(buf->data, buf->len);
    net_buf_add_le16(buf, crc);

    /* Push header at front */
    net_buf_push_u8(buf, cmd);
    net_buf_push_le16(buf, buf->len);  /* Length includes CRC */
    net_buf_push_u8(buf, FRAME_START);

    return buf;
}
```

### Pattern 3: Streaming Parser State Machine

```c
enum parse_state { WAIT_START, READ_LEN, READ_DATA, VERIFY_CRC };

struct parser {
    enum parse_state state;
    uint16_t expected_len;
    struct net_buf *buf;
};

void parse_byte(struct parser *p, uint8_t c)
{
    switch (p->state) {
    case WAIT_START:
        if (c == FRAME_START) {
            p->buf = net_buf_alloc(&pool, K_NO_WAIT);
            p->state = READ_LEN;
        }
        break;
    case READ_LEN:
        net_buf_add_u8(p->buf, c);
        if (p->buf->len == 2) {
            p->expected_len = net_buf_pull_le16(p->buf);
            p->state = READ_DATA;
        }
        break;
    case READ_DATA:
        net_buf_add_u8(p->buf, c);
        if (p->buf->len == p->expected_len) {
            p->state = VERIFY_CRC;
        }
        break;
    /* ... */
    }
}
```
