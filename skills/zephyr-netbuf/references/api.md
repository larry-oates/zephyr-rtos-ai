# net_buf API Reference

## Header File

```c
#include <zephyr/net_buf.h>
```

## Pool Definition Macros

### NET_BUF_POOL_DEFINE (Fixed-Size)

Most common. Allocates fixed-size data chunks.

```c
NET_BUF_POOL_DEFINE(name, count, size, ud_size, destroy);
```

| Parameter | Description |
|-----------|-------------|
| `name` | Pool variable name |
| `count` | Number of buffers in pool |
| `size` | Max data bytes per buffer |
| `ud_size` | User data size per buffer (0 if unused) |
| `destroy` | Optional callback when buffer freed (NULL if unused) |

### NET_BUF_POOL_VAR_DEFINE (Variable-Size)

Uses a heap for variable-sized allocations.

```c
NET_BUF_POOL_VAR_DEFINE(name, count, total_data_size, ud_size, destroy);
```

- `total_data_size` — Total heap size for all buffer data.

### NET_BUF_POOL_HEAP_DEFINE (System Heap)

Uses `k_malloc` for data. Requires `CONFIG_HEAP_MEM_POOL_SIZE > 0`.

```c
NET_BUF_POOL_HEAP_DEFINE(name, count, ud_size, destroy);
```

**Note**: Does not support blocking on allocation — always treated as `K_NO_WAIT`.

### NET_BUF_SIMPLE_DEFINE (Stack)

Defines a `net_buf_simple` on the stack (no pool).

```c
NET_BUF_SIMPLE_DEFINE(name, size);
```

Or get a pointer directly:

```c
struct net_buf_simple *buf = NET_BUF_SIMPLE(size);
net_buf_simple_init(buf, reserve_headroom);
```

---

## Lifecycle Functions

### Allocation

```c
struct net_buf *net_buf_alloc(struct net_buf_pool *pool, k_timeout_t timeout);
struct net_buf *net_buf_alloc_len(struct net_buf_pool *pool, size_t size, k_timeout_t timeout);
struct net_buf *net_buf_alloc_with_data(struct net_buf_pool *pool, void *data, size_t size, k_timeout_t timeout);
```

| Function | Use Case |
|----------|----------|
| `net_buf_alloc` | Fixed-size pools |
| `net_buf_alloc_len` | Variable-size pools (specify needed size) |
| `net_buf_alloc_with_data` | Use external data pointer |

### Reference Counting

```c
struct net_buf *net_buf_ref(struct net_buf *buf);   /* Increment refcount */
void net_buf_unref(struct net_buf *buf);            /* Decrement; frees when 0 */
```

### Reset & Clone

```c
void net_buf_reset(struct net_buf *buf);                              /* Reset data/flags for reuse */
struct net_buf *net_buf_clone(struct net_buf *buf, k_timeout_t timeout); /* Deep copy */
```

### Headroom Reservation

```c
void net_buf_reserve(struct net_buf *buf, size_t reserve);
```

---

## Data Manipulation Functions

### Add (Append to End)

```c
void *net_buf_add(struct net_buf *buf, size_t len);
void *net_buf_add_mem(struct net_buf *buf, const void *mem, size_t len);
uint8_t *net_buf_add_u8(struct net_buf *buf, uint8_t val);
void net_buf_add_le16(struct net_buf *buf, uint16_t val);
void net_buf_add_be16(struct net_buf *buf, uint16_t val);
void net_buf_add_le32(struct net_buf *buf, uint32_t val);
void net_buf_add_be32(struct net_buf *buf, uint32_t val);
void net_buf_add_le64(struct net_buf *buf, uint64_t val);
void net_buf_add_be64(struct net_buf *buf, uint64_t val);
```

### Remove (Trim from End)

```c
void *net_buf_remove_mem(struct net_buf *buf, size_t len);
uint8_t net_buf_remove_u8(struct net_buf *buf);
uint16_t net_buf_remove_le16(struct net_buf *buf);
uint16_t net_buf_remove_be16(struct net_buf *buf);
uint32_t net_buf_remove_le32(struct net_buf *buf);
uint32_t net_buf_remove_be32(struct net_buf *buf);
```

### Push (Prepend to Start)

```c
void *net_buf_push(struct net_buf *buf, size_t len);
void *net_buf_push_mem(struct net_buf *buf, const void *mem, size_t len);
void net_buf_push_u8(struct net_buf *buf, uint8_t val);
void net_buf_push_le16(struct net_buf *buf, uint16_t val);
void net_buf_push_be16(struct net_buf *buf, uint16_t val);
void net_buf_push_le32(struct net_buf *buf, uint32_t val);
void net_buf_push_be32(struct net_buf *buf, uint32_t val);
```

### Pull (Consume from Start)

```c
void *net_buf_pull(struct net_buf *buf, size_t len);
void *net_buf_pull_mem(struct net_buf *buf, size_t len);
uint8_t net_buf_pull_u8(struct net_buf *buf);
uint16_t net_buf_pull_le16(struct net_buf *buf);
uint16_t net_buf_pull_be16(struct net_buf *buf);
uint32_t net_buf_pull_le32(struct net_buf *buf);
uint32_t net_buf_pull_be32(struct net_buf *buf);
uint64_t net_buf_pull_le64(struct net_buf *buf);
uint64_t net_buf_pull_be64(struct net_buf *buf);
```

---

## Buffer Info Functions

```c
size_t net_buf_tailroom(const struct net_buf *buf);  /* Free space at end */
size_t net_buf_headroom(const struct net_buf *buf);  /* Free space at start */
uint16_t net_buf_max_len(const struct net_buf *buf); /* Max usable length */
uint8_t *net_buf_tail(const struct net_buf *buf);    /* Pointer to end of data */
void *net_buf_user_data(const struct net_buf *buf);  /* Pointer to user_data */
int net_buf_id(const struct net_buf *buf);           /* Zero-based index in pool */
```

---

## Fragment Functions

```c
struct net_buf *net_buf_frag_last(struct net_buf *frags);
struct net_buf *net_buf_frag_add(struct net_buf *head, struct net_buf *frag);
void net_buf_frag_insert(struct net_buf *parent, struct net_buf *frag);
struct net_buf *net_buf_frag_del(struct net_buf *parent, struct net_buf *frag);
size_t net_buf_frags_len(const struct net_buf *buf);
size_t net_buf_linearize(void *dst, size_t dst_len, const struct net_buf *src, size_t offset, size_t len);
```

---

## List Operations

For passing buffers through `k_fifo`:

```c
/* Standard kernel FIFO works directly */
k_fifo_put(&my_fifo, buf);
buf = k_fifo_get(&my_fifo, K_FOREVER);
```

For `sys_slist_t`:

```c
void net_buf_slist_put(sys_slist_t *list, struct net_buf *buf);
struct net_buf *net_buf_slist_get(sys_slist_t *list);
```

---

## Kconfig Options

| Option | Description |
|--------|-------------|
| `CONFIG_NET_BUF_LOG` | Enable debug logging for net_buf operations |
| `CONFIG_NET_BUF_POOL_USAGE` | Track pool usage statistics (avail_count, max_used) |
| `CONFIG_NET_BUF_ALIGNMENT` | Data alignment (default: sizeof(void *)) |

---

## net_buf_simple API

Same operations as `net_buf` but with `_simple` suffix:

```c
void net_buf_simple_init(struct net_buf_simple *buf, size_t reserve_head);
void net_buf_simple_reset(struct net_buf_simple *buf);
void *net_buf_simple_add(struct net_buf_simple *buf, size_t len);
void *net_buf_simple_push(struct net_buf_simple *buf, size_t len);
void *net_buf_simple_pull(struct net_buf_simple *buf, size_t len);
size_t net_buf_simple_headroom(const struct net_buf_simple *buf);
size_t net_buf_simple_tailroom(const struct net_buf_simple *buf);
```

Use `net_buf_simple` when:
- Buffer is stack-allocated or has known lifetime
- No need for reference counting
- No need to pass through kernel objects
