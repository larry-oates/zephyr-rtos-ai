# zcbor Source Locations

## Headers (in Zephyr workspace)

```
modules/zcbor/include/zcbor_encode.h    # Encoding API
modules/zcbor/include/zcbor_decode.h    # Decoding API
modules/zcbor/include/zcbor_common.h    # Shared types (zcbor_state_t, zcbor_string)
modules/zcbor/include/zcbor_tags.h      # Registered CBOR tag constants
```

## Implementation

```
modules/zcbor/src/zcbor_encode.c
modules/zcbor/src/zcbor_decode.c
modules/zcbor/src/zcbor_common.c
```

## CMake / Build Integration

```cmake
# zcbor is a Zephyr module — no manual CMakeLists changes needed.
# Just enable CONFIG_ZCBOR=y and include the headers.
```

## Zephyr Samples

```
samples/modules/zcbor/           # Basic encoding/decoding sample
```

## Upstream Repository

- GitHub: https://github.com/NordicSemiconductor/zcbor
- Upstream docs: https://nordicsemiconductor.github.io/zcbor/latest/

## Zephyr Documentation

- https://docs.zephyrproject.org/latest/services/serialization/cbor.html
