# zcbor Kconfig Reference

## Required

```kconfig
CONFIG_ZCBOR=y
```

Enables the zcbor library. Pulls in the zcbor West module.

## Optional Options

```kconfig
# Enable canonical CBOR encoding (definite-length maps/arrays, sorted map keys)
# Uses memmove() to rewrite headers — increases code/RAM usage
CONFIG_ZCBOR_CANONICAL=y

# Stop encoding/decoding immediately on first error (slightly smaller code)
CONFIG_ZCBOR_STOP_ON_ERROR=y

# Enable smart search for unordered maps (per-element flags instead of rolling count)
# Allows re-searching the same key, safer for optional fields
CONFIG_ZCBOR_MAP_SMART_SEARCH=y

# Enable verbose error logging (prints to LOG_ERR)
CONFIG_ZCBOR_VERBOSE=y

# Validation level — 0=none (fastest), 1=assert, 2=full
CONFIG_ZCBOR_VALIDATE=0
```

## Example prj.conf

```kconfig
CONFIG_ZCBOR=y
CONFIG_ZCBOR_STOP_ON_ERROR=y
```

## Notes

- `CONFIG_ZCBOR_CANONICAL` is required when encoding CBOR that must conform to RFC 8949 canonical form (e.g., SUIT manifests).
- `CONFIG_ZCBOR_MAP_SMART_SEARCH` is only needed for `zcbor_unordered_map_search` when fields may appear multiple times.
- Default (non-canonical) mode encodes maps and lists with an indefinite-length terminator (`0xFF`).
