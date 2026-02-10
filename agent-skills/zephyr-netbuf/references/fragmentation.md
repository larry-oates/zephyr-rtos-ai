# net_buf Fragmentation

## Overview

When a single buffer cannot hold all data (e.g., large packets, MTU limits), `net_buf` supports **fragment chains** — linked lists of buffers that together represent one logical packet.

```
┌─────────┐    ┌─────────┐    ┌─────────┐
│  head   │───►│  frag1  │───►│  frag2  │───► NULL
│ (buf)   │    │ (buf)   │    │ (buf)   │
│ frags ──┼────┘ frags ──┼────┘ frags   │
└─────────┘    └─────────┘    └─────────┘
```

Each `net_buf` has a `frags` pointer to the next fragment.

---

## Creating Fragment Chains

### Method 1: net_buf_frag_add (Append)

Adds fragment to end of chain. Returns head.

```c
struct net_buf *head = net_buf_alloc(&pool, K_FOREVER);
net_buf_add_mem(head, data1, len1);

struct net_buf *frag = net_buf_alloc(&pool, K_FOREVER);
net_buf_add_mem(frag, data2, len2);

/* Add to chain — frag's ref is consumed */
head = net_buf_frag_add(head, frag);
```

**Important**: `net_buf_frag_add` takes ownership of the fragment reference. Do not `unref` it separately.

### Method 2: net_buf_frag_insert (Insert After)

Inserts fragment after a specific parent buffer.

```c
struct net_buf *parent = /* ... */;
struct net_buf *new_frag = net_buf_alloc(&pool, K_FOREVER);

/* Insert new_frag immediately after parent */
net_buf_frag_insert(parent, new_frag);
/* Chain: parent → new_frag → (old parent->frags) */
```

---

## Traversing Fragment Chains

### Simple Iteration

```c
for (struct net_buf *f = head; f != NULL; f = f->frags) {
    /* Process f->data (length f->len) */
    process_fragment(f->data, f->len);
}
```

### Get Total Length

```c
size_t total = net_buf_frags_len(head);
```

### Find Last Fragment

```c
struct net_buf *last = net_buf_frag_last(head);
/* last->frags == NULL */
```

---

## Linearizing Fragment Data

Copy fragmented data into a contiguous buffer:

```c
uint8_t linear_buf[1024];

/* Copy from offset 0, up to sizeof(linear_buf) bytes */
size_t copied = net_buf_linearize(linear_buf, sizeof(linear_buf),
                                   head, 0, net_buf_frags_len(head));
```

### Parameters

| Param | Description |
|-------|-------------|
| `dst` | Destination buffer |
| `dst_len` | Max bytes to copy |
| `src` | Head of fragment chain |
| `offset` | Starting offset in chain |
| `len` | Max bytes to copy from chain |

Returns actual bytes copied.

---

## Removing Fragments

### Delete Fragment from Chain

```c
/* parent is the buffer before frag, or NULL if frag is head */
struct net_buf *next = net_buf_frag_del(parent, frag);
/* frag is unreferenced; next is the fragment that followed it */
```

### Delete First Fragment (Head)

```c
struct net_buf *old_head = head;
head = net_buf_frag_del(NULL, head);
/* old_head is unreferenced; head now points to former second fragment */
```

---

## Freeing Fragment Chains

`net_buf_unref` on head automatically frees the entire chain:

```c
net_buf_unref(head);
/* All fragments in chain are unreferenced */
```

**Caution**: If you hold references to individual fragments, they may become invalid after freeing head.

---

## Skip / Consume Across Fragments

The `net_buf_skip` helper advances through data, auto-deleting consumed fragments:

```c
/* Skip len bytes across fragment chain */
buf = net_buf_skip(buf, bytes_to_skip);
/* Returns updated head (or NULL if all data consumed) */
```

Internally:
1. Calls `net_buf_pull_u8` repeatedly
2. When a fragment is emptied (`len == 0`), deletes it
3. Moves to next fragment

---

## Appending Data Across Fragments

Use `net_buf_append_bytes` for large data that may span fragments:

```c
size_t added = net_buf_append_bytes(head, total_len, data,
                                     K_FOREVER,
                                     allocator_cb,  /* or NULL for same pool */
                                     user_data);
```

The function:
1. Fills remaining tailroom in current fragment
2. Allocates new fragments as needed
3. Returns bytes actually added

---

## Common Patterns

### Pattern 1: Scatter-Gather TX

```c
struct net_buf *pkt = net_buf_alloc(&pool, K_FOREVER);
net_buf_reserve(pkt, HEADER_RESERVE);

/* Add header */
net_buf_push_mem(pkt, header, header_len);

/* Add payload fragments */
for (int i = 0; i < payload_count; i++) {
    struct net_buf *frag = net_buf_alloc(&pool, K_FOREVER);
    net_buf_add_mem(frag, payloads[i].data, payloads[i].len);
    net_buf_frag_add(pkt, frag);
}

/* Send entire chain */
send_packet(pkt);
```

### Pattern 2: RX Reassembly

```c
static struct net_buf *rx_chain = NULL;

void on_rx_fragment(const uint8_t *data, size_t len)
{
    struct net_buf *frag = net_buf_alloc(&pool, K_NO_WAIT);
    if (!frag) return;

    net_buf_add_mem(frag, data, len);

    if (rx_chain == NULL) {
        rx_chain = frag;
    } else {
        net_buf_frag_add(rx_chain, frag);
    }
}

void on_rx_complete(void)
{
    /* Process complete packet */
    size_t total = net_buf_frags_len(rx_chain);
    process_packet(rx_chain, total);

    net_buf_unref(rx_chain);
    rx_chain = NULL;
}
```

### Pattern 3: Protocol Layer Stripping

```c
/* Strip L2 header, return L3 payload */
struct net_buf *strip_l2_header(struct net_buf *pkt)
{
    /* Pull L2 header from first fragment */
    struct l2_header *l2 = net_buf_pull_mem(pkt, sizeof(*l2));

    /* If first fragment is now empty, remove it */
    if (pkt->len == 0 && pkt->frags) {
        pkt = net_buf_frag_del(NULL, pkt);
    }

    return pkt;
}
```

---

## Memory Considerations

- Each fragment consumes one `net_buf` from the pool
- Fragment chains share the reference count model — `unref` on head releases all
- Pool sizing: account for worst-case fragmentation (e.g., MTU-sized fragments for max packet)

```c
/* Example: Support 1500-byte packets with 256-byte fragments */
#define FRAG_SIZE 256
#define MAX_FRAGS ((1500 + FRAG_SIZE - 1) / FRAG_SIZE)  /* 6 */
#define POOL_COUNT (MAX_FRAGS * MAX_CONCURRENT_PACKETS)

NET_BUF_POOL_DEFINE(pkt_pool, POOL_COUNT, FRAG_SIZE, 0, NULL);
```
