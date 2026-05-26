# zcbor Common Patterns

## List of Integers

```c
// Encode
zcbor_list_start_encode(zse, 3);
zcbor_int32_put(zse, 10);
zcbor_int32_put(zse, 20);
zcbor_int32_put(zse, 30);
zcbor_list_end_encode(zse, 3);

// Decode
int32_t vals[3];
zcbor_list_start_decode(zsd);
for (int i = 0; i < 3; i++) {
    zcbor_int32_decode(zsd, &vals[i]);
}
zcbor_list_end_decode(zsd);
```

## Unordered Map (Keys in Any Order)

```c
// backups=1 required; n_flags = max elements in any unordered map
ZCBOR_STATE_D(zsd, 1, buf, len, 1, 2);

int32_t temp;
struct zcbor_string unit;

zcbor_unordered_map_start_decode(zsd);
zcbor_search_key_tstr_lit(zsd, "temp") && zcbor_int32_decode(zsd, &temp);
zcbor_search_key_tstr_lit(zsd, "unit") && zcbor_tstr_decode(zsd, &unit);
zcbor_unordered_map_end_decode(zsd);
```

Enable `CONFIG_ZCBOR_MAP_SMART_SEARCH=y` if keys may appear multiple times or for optional fields.

## Byte String (bstr)

```c
// Encode raw bytes
uint8_t data[] = {0x01, 0x02, 0x03};
zcbor_bstr_encode_ptr(zse, (char *)data, sizeof(data));

// Decode — zero-copy, result.value points into original buffer
struct zcbor_string result;
zcbor_bstr_decode(zsd, &result);
// result.value[0..result.len-1] valid while buf is alive
```

## Nested CBOR in a bstr

```c
// Encode: wrap inner CBOR inside a bstr
zcbor_bstr_start_encode(zse);
zcbor_int32_put(zse, 42);           // inner payload
zcbor_bstr_end_encode(zse, NULL);

// Decode
struct zcbor_string inner_bstr;
zcbor_bstr_start_decode(zsd, &inner_bstr);
int32_t val;
zcbor_int32_decode(zsd, &val);
zcbor_bstr_end_decode(zsd);
```

## Error Handling

```c
// All functions return bool — chain with &&
bool ok = zcbor_map_start_encode(zse, 2)
       && zcbor_tstr_put_lit(zse, "key")
       && zcbor_int32_put(zse, 42)
       && zcbor_map_end_encode(zse, 2);

if (!ok) {
    int err = zcbor_peek_error(zse);  // ZCBOR_ERR_*
    // e.g. ZCBOR_ERR_NO_PAYLOAD, ZCBOR_ERR_WRONG_TYPE
}
```

## Skipping Unknown Fields

```c
// Skip one element of any type during decode
zcbor_any_skip(zsd, NULL);
```

## Dynamic Array with Multi-decode

```c
uint32_t items[8];
size_t num_decoded;

zcbor_list_start_decode(zsd);
zcbor_multi_decode(1, ARRAY_SIZE(items), &num_decoded,
                   (zcbor_decoder_t)zcbor_uint32_decode,
                   zsd, items, sizeof(items[0]));
zcbor_list_end_decode(zsd);
```
