# JSON API Reference

## Header

```c
#include <zephyr/data/json.h>
```

## Core Functions

### Parsing

```c
int64_t json_obj_parse(char *json, size_t len,
                       const struct json_obj_descr *descr, size_t descr_len,
                       void *val);
```

Parse JSON object into a C struct.

- **json**: Input buffer (MODIFIED in place - strings null-terminated)
- **len**: Length of JSON string
- **descr**: Descriptor array
- **descr_len**: Number of descriptors (max 63)
- **val**: Output struct pointer
- **Returns**: Bitmap of decoded fields (bit N set = field N decoded), negative on error

```c
int json_arr_parse(char *json, size_t len,
                   const struct json_obj_descr *descr, void *val);
```

Parse JSON array into a C struct containing an array field.

- **Returns**: 0 on success, negative errno on error

### Encoding

```c
int json_obj_encode_buf(const struct json_obj_descr *descr, size_t descr_len,
                        const void *val, char *buffer, size_t buf_size);
```

Encode struct to JSON in a buffer.

- **buffer**: Output buffer
- **buf_size**: Buffer size (includes space for null terminator)
- **Returns**: 0 on success, negative errno on error

```c
int json_arr_encode_buf(const struct json_obj_descr *descr, const void *val,
                        char *buffer, size_t buf_size);
```

Encode array to JSON in a buffer.

```c
int json_obj_encode(const struct json_obj_descr *descr, size_t descr_len,
                    const void *val, json_append_bytes_t append_bytes,
                    void *data);
```

Encode using callback function (for streaming).

- **append_bytes**: `int (*)(const char *bytes, size_t len, void *data)`
- **Returns**: 0 on success, callback's error on failure

### Length Calculation

```c
ssize_t json_calc_encoded_len(const struct json_obj_descr *descr,
                              size_t descr_len, const void *val);
```

Calculate buffer size needed for encoding (excludes null terminator).

```c
ssize_t json_calc_encoded_arr_len(const struct json_obj_descr *descr,
                                  const void *val);
```

Calculate buffer size for array encoding.

### String Escaping

```c
ssize_t json_escape(char *str, size_t *len, size_t buf_size);
```

Escape string in-place for JSON encoding.

- **str**: String to escape (modified in place)
- **len**: Input/output length
- **buf_size**: Total buffer capacity
- **Returns**: 0 on success, -ENOMEM if insufficient space

```c
size_t json_calc_escaped_len(const char *str, size_t len);
```

Calculate escaped length without modifying string.

## Descriptor Macros

### Primitives

```c
JSON_OBJ_DESCR_PRIM(struct_, field_name_, type_)
```

Describe a primitive field.

```c
JSON_OBJ_DESCR_PRIM_NAMED(struct_, "json-key", field_name_, type_)
```

Describe a primitive field with different JSON key name.

### Objects

```c
JSON_OBJ_DESCR_OBJECT(struct_, field_name_, sub_descr_)
```

Describe a nested object field.

```c
JSON_OBJ_DESCR_OBJECT_NAMED(struct_, "json-key", field_name_, sub_descr_)
```

Describe nested object with different JSON key name.

### Arrays

```c
JSON_OBJ_DESCR_ARRAY(struct_, field_name_, max_len_, len_field_, elem_type_)
```

Describe array of primitives.

- **max_len_**: Maximum array capacity
- **len_field_**: Field tracking actual element count

```c
JSON_OBJ_DESCR_ARRAY_NAMED(struct_, "json-key", field_name_, max_len_, len_field_, elem_type_)
```

Array with different JSON key name.

```c
JSON_OBJ_DESCR_OBJ_ARRAY(struct_, field_name_, max_len_, len_field_, elem_descr_, elem_descr_len_)
```

Describe array of objects.

```c
JSON_OBJ_DESCR_OBJ_ARRAY_NAMED(struct_, "json-key", field_name_, max_len_, len_field_, elem_descr_, elem_descr_len_)
```

Array of objects with different JSON key name.

```c
JSON_OBJ_DESCR_ARRAY_ARRAY(struct_, field_name_, max_len_, len_field_, elem_descr_, elem_descr_len_)
```

Describe 2D array (array of arrays).

### Mixed Arrays

For arrays with heterogeneous element types:

```c
JSON_MIXED_ARR_DESCR_PRIM(struct_, field_name_, type_, count_field_)
JSON_MIXED_ARR_DESCR_OBJECT(struct_, field_name_, sub_descr_, count_field_)
JSON_MIXED_ARR_DESCR_ARRAY(struct_, field_name_, max_len_, elem_descr_, count_field_)
JSON_MIXED_ARR_DESCR_MIXED_ARRAY(struct_, field_name_, sub_descr_, count_field_)
```

```c
int json_mixed_arr_parse(char *json, size_t len,
                         const struct json_mixed_arr_descr *descr,
                         size_t descr_len, void *val);

int json_mixed_arr_encode_buf(const struct json_mixed_arr_descr *descr,
                              size_t descr_len, void *val,
                              char *buffer, size_t buf_size);
```

## Streaming Array Parsing

For parsing large arrays one object at a time:

```c
int json_arr_separate_object_parse_init(struct json_obj *json, char *payload, size_t len);
```

Initialize streaming array parser.

```c
int json_arr_separate_parse_object(struct json_obj *json,
                                   const struct json_obj_descr *descr,
                                   size_t descr_len, void *val);
```

Parse next object from array.

- **Returns**: Bitmap of decoded fields, 0 for end of array, negative on error

## Error Codes

| Return Value | Meaning |
|--------------|---------|
| `-EINVAL` | Invalid JSON syntax |
| `-ENOMEM` | Buffer too small |
| `-ENOENT` | Required field not found |
| `0` (encode) | Success |
| `bitmap` (parse) | Fields decoded (check bits) |
