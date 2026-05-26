# zcbor API Reference

## Type Quick Reference

| C type | Encode (_put) | Decode |
|--------|--------------|--------|
| `int8/16/32/64_t` | `zcbor_int32_put(state, val)` | `zcbor_int32_decode(state, &result)` |
| `uint8/16/32/64_t` | `zcbor_uint32_put(state, val)` | `zcbor_uint32_decode(state, &result)` |
| `bool` | `zcbor_bool_put(state, val)` | `zcbor_bool_decode(state, &result)` |
| `float` (32-bit) | `zcbor_float32_put(state, val)` | `zcbor_float32_decode(state, &result)` |
| `double` | `zcbor_float64_put(state, val)` | `zcbor_float64_decode(state, &result)` |
| text string | `zcbor_tstr_put_lit(state, "str")` | `zcbor_tstr_decode(state, &zcbor_string)` |
| byte string | `zcbor_bstr_encode_ptr(state, ptr, len)` | `zcbor_bstr_decode(state, &zcbor_string)` |
| nil | `zcbor_nil_put(state, NULL)` | `zcbor_nil_expect(state, NULL)` |
| list/array | `zcbor_list_start/end_encode` | `zcbor_list_start/end_decode` |
| map | `zcbor_map_start/end_encode` | `zcbor_map_start/end_decode` |

`struct zcbor_string { const uint8_t *value; size_t len; }` — points into the original buffer (zero-copy).

## Headers

```c
#include <zcbor_encode.h>   // encoding
#include <zcbor_decode.h>   // decoding
#include <zcbor_common.h>   // shared types (zcbor_state_t, zcbor_string)
```

## State Types

```c
struct zcbor_string {
    const uint8_t *value;  // points into payload buffer (zero-copy)
    size_t len;
};

struct zcbor_string_fragment {
    struct zcbor_string fragment;
    size_t offset;       // offset in the full string
    size_t total_len;    // ZCBOR_STRING_FRAGMENT_UNKNOWN_LENGTH if unknown
};
```

## State Initialization

```c
// Encoder
ZCBOR_STATE_E(name, num_backups, payload, payload_size, elem_count);

// Decoder
ZCBOR_STATE_D(name, num_backups, payload, payload_size, elem_count, n_flags);

// Low-level init (not needed if using the macros above)
void zcbor_new_encode_state(zcbor_state_t *state_array, size_t n_states,
                             uint8_t *payload, size_t payload_len, size_t elem_count);
void zcbor_new_decode_state(zcbor_state_t *state_array, size_t n_states,
                             const uint8_t *payload, size_t payload_len, size_t elem_count,
                             uint8_t *elem_state, size_t elem_state_bytes);
```

## Encoding Functions

All return `bool` — `true` on success, `false` on failure.

### Primitives (_put = value, _encode = pointer)

```c
bool zcbor_int8_put(zcbor_state_t *state, int8_t input);
bool zcbor_int16_put(zcbor_state_t *state, int16_t input);
bool zcbor_int32_put(zcbor_state_t *state, int32_t input);
bool zcbor_int64_put(zcbor_state_t *state, int64_t input);
bool zcbor_uint8_put(zcbor_state_t *state, uint8_t input);
bool zcbor_uint16_put(zcbor_state_t *state, uint16_t input);
bool zcbor_uint32_put(zcbor_state_t *state, uint32_t input);
bool zcbor_uint64_put(zcbor_state_t *state, uint64_t input);
bool zcbor_size_put(zcbor_state_t *state, size_t input);
bool zcbor_bool_put(zcbor_state_t *state, bool input);
bool zcbor_nil_put(zcbor_state_t *state, const void *unused);
bool zcbor_undefined_put(zcbor_state_t *state, const void *unused);
bool zcbor_float16_put(zcbor_state_t *state, float input);
bool zcbor_float32_put(zcbor_state_t *state, float input);
bool zcbor_float64_put(zcbor_state_t *state, double input);
bool zcbor_tag_put(zcbor_state_t *state, uint32_t tag);

// _encode variants take a pointer (for use with zcbor_multi_encode)
bool zcbor_int32_encode(zcbor_state_t *state, const int32_t *input);
bool zcbor_uint32_encode(zcbor_state_t *state, const uint32_t *input);
bool zcbor_bool_encode(zcbor_state_t *state, const bool *input);
bool zcbor_float32_encode(zcbor_state_t *state, const float *input);
bool zcbor_float64_encode(zcbor_state_t *state, const double *input);
// ... (same pattern for all numeric types)
```

### Strings

```c
bool zcbor_bstr_encode(zcbor_state_t *state, const struct zcbor_string *input);
bool zcbor_tstr_encode(zcbor_state_t *state, const struct zcbor_string *input);
bool zcbor_bstr_encode_ptr(zcbor_state_t *state, const char *str, size_t len);
bool zcbor_tstr_encode_ptr(zcbor_state_t *state, const char *str, size_t len);
bool zcbor_bstr_put_term(zcbor_state_t *state, char const *str, size_t maxlen);
bool zcbor_tstr_put_term(zcbor_state_t *state, char const *str, size_t maxlen);

// Convenience macros for string literals and arrays
#define zcbor_bstr_put_lit(state, str)   // sizeof(str)-1
#define zcbor_tstr_put_lit(state, str)   // sizeof(str)-1
#define zcbor_bstr_put_arr(state, str)   // sizeof(str)
#define zcbor_tstr_put_arr(state, str)   // sizeof(str)
```

### Lists and Maps

```c
bool zcbor_list_start_encode(zcbor_state_t *state, size_t size_hint);
bool zcbor_list_end_encode(zcbor_state_t *state, size_t size_hint);
bool zcbor_map_start_encode(zcbor_state_t *state, size_t size_hint);
bool zcbor_map_end_encode(zcbor_state_t *state, size_t size_hint);
bool zcbor_list_map_end_force_encode(zcbor_state_t *state);
```

`size_hint`: Used only with `ZCBOR_CANONICAL`. Pass `0` if unused or unknown.

### Nested CBOR in bstr

```c
bool zcbor_bstr_start_encode(zcbor_state_t *state);
bool zcbor_bstr_end_encode(zcbor_state_t *state, struct zcbor_string *result);
```

### Multi-encode

```c
bool zcbor_multi_encode(size_t num_encode, zcbor_encoder_t encoder,
                         zcbor_state_t *state, const void *input, size_t result_len);
bool zcbor_multi_encode_minmax(size_t min_encode, size_t max_encode,
                                const size_t *num_encode, zcbor_encoder_t encoder,
                                zcbor_state_t *state, const void *input, size_t input_len);
```

Use `ZCBOR_CAST_FP(fn)` to cast function pointers for compatibility checks.

## Decoding Functions

All return `bool` — `true` if decoded successfully.

### Primitives (_decode = output to pointer)

```c
bool zcbor_int8_decode(zcbor_state_t *state, int8_t *result);
bool zcbor_int16_decode(zcbor_state_t *state, int16_t *result);
bool zcbor_int32_decode(zcbor_state_t *state, int32_t *result);
bool zcbor_int64_decode(zcbor_state_t *state, int64_t *result);
bool zcbor_uint8_decode(zcbor_state_t *state, uint8_t *result);
bool zcbor_uint16_decode(zcbor_state_t *state, uint16_t *result);
bool zcbor_uint32_decode(zcbor_state_t *state, uint32_t *result);
bool zcbor_uint64_decode(zcbor_state_t *state, uint64_t *result);
bool zcbor_size_decode(zcbor_state_t *state, size_t *result);
bool zcbor_bool_decode(zcbor_state_t *state, bool *result);
bool zcbor_float16_decode(zcbor_state_t *state, float *result);
bool zcbor_float32_decode(zcbor_state_t *state, float *result);
bool zcbor_float64_decode(zcbor_state_t *state, double *result);
bool zcbor_float_decode(zcbor_state_t *state, double *result);  // any float width
bool zcbor_tag_decode(zcbor_state_t *state, uint32_t *result);
bool zcbor_bstr_decode(zcbor_state_t *state, struct zcbor_string *result);
bool zcbor_tstr_decode(zcbor_state_t *state, struct zcbor_string *result);
```

### Expect (decode + validate value)

```c
bool zcbor_int32_expect(zcbor_state_t *state, int32_t expected);
bool zcbor_uint32_expect(zcbor_state_t *state, uint32_t expected);
bool zcbor_bool_expect(zcbor_state_t *state, bool expected);
bool zcbor_nil_expect(zcbor_state_t *state, void *unused);
bool zcbor_undefined_expect(zcbor_state_t *state, void *unused);
bool zcbor_tstr_expect(zcbor_state_t *state, struct zcbor_string *expected);
bool zcbor_bstr_expect(zcbor_state_t *state, struct zcbor_string *expected);
bool zcbor_tag_expect(zcbor_state_t *state, uint32_t expected);

// String literal convenience macros (same as encode side)
#define zcbor_tstr_expect_lit(state, str)
#define zcbor_bstr_expect_lit(state, str)
#define zcbor_tstr_expect_term(state, str, maxlen)
```

### Lists and Maps

```c
bool zcbor_list_start_decode(zcbor_state_t *state);
bool zcbor_list_end_decode(zcbor_state_t *state);
bool zcbor_map_start_decode(zcbor_state_t *state);
bool zcbor_map_end_decode(zcbor_state_t *state);
```

### Unordered Maps

```c
bool zcbor_unordered_map_start_decode(zcbor_state_t *state);
bool zcbor_unordered_map_end_decode(zcbor_state_t *state);

bool zcbor_unordered_map_search(zcbor_decoder_t key_decoder,
                                 zcbor_state_t *state, void *key_result);

// Convenience: search for a specific string key
bool zcbor_search_key_tstr_lit(zcbor_state_t *state, const char *str);
bool zcbor_search_key_bstr_lit(zcbor_state_t *state, const char *str);
bool zcbor_search_key_tstr_ptr(zcbor_state_t *state, char const *ptr, size_t len);
bool zcbor_search_key_tstr_term(zcbor_state_t *state, char const *str, size_t maxlen);
```

Requires `num_backups >= 1` in `ZCBOR_STATE_D`.
`n_flags` in `ZCBOR_STATE_D` must be >= max number of elements in any unordered map.

### Nested CBOR in bstr

```c
bool zcbor_bstr_start_decode(zcbor_state_t *state, struct zcbor_string *result);
bool zcbor_bstr_end_decode(zcbor_state_t *state);
```

### Skipping Elements

```c
bool zcbor_any_skip(zcbor_state_t *state, void *unused);  // skip one element
```

### Multi-decode

```c
bool zcbor_multi_decode(size_t min_decode, size_t max_decode,
                         size_t *num_decode, zcbor_decoder_t decoder,
                         zcbor_state_t *state, void *result, size_t result_len);
```

## Error Handling

```c
int zcbor_peek_error(const zcbor_state_t *state);  // returns ZCBOR_ERR_* code

// Common error codes
ZCBOR_ERR_NO_PAYLOAD           // buffer exhausted
ZCBOR_ERR_WRONG_TYPE           // type mismatch
ZCBOR_ERR_HIGH_ELEM_COUNT      // too many elements in list/map
ZCBOR_ERR_NOT_AT_END           // list/map didn't consume all elements
ZCBOR_ERR_VALUE_NOT_FOUND      // _expect() value mismatch
ZCBOR_ERR_PAYLOAD_NOT_CONSUMED // trailing bytes after decoding
```

## Encoded Size

```c
// After encoding, bytes written = payload_ptr - start_of_buffer
size_t len = zse->payload - buf;

// For canonical mode: zcbor provides no pre-computation helper;
// encode into a sufficiently large scratch buffer and check the length.
```
