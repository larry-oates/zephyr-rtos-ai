# Source Code and Documentation Locations

## Zephyr Repository Paths

All paths relative to Zephyr root (`zephyr/`).

### Core Library

| Resource | Path |
|----------|------|
| Header | `include/zephyr/data/json.h` |
| Implementation | `lib/utils/json.c` |
| Kconfig | `lib/utils/Kconfig` |

### Documentation

| Resource | Path |
|----------|------|
| API docs | `doc/services/misc.rst` (JSON section) |

### Tests

| Resource | Path |
|----------|------|
| Test source | `tests/lib/json/src/main.c` |
| Test config | `tests/lib/json/prj.conf` |
| Test spec | `tests/lib/json/testcase.yaml` |

The test file (`main.c`) contains comprehensive examples including:
- Nested objects and arrays
- Named fields with special characters
- Float/double encoding and decoding
- Mixed arrays
- 2D arrays
- Edge cases (limits, escaping)

## Sample Applications Using JSON

| Sample | Path | Description |
|--------|------|-------------|
| UpdateHub | `samples/subsys/mgmt/updatehub/` | OTA updates with JSON |
| AWS IoT | `samples/net/cloud/aws_iot_mqtt/` | Cloud telemetry |
| HTTP Server | `samples/net/sockets/http_server/` | REST API |
| HawkBit | `samples/subsys/mgmt/hawkbit/` | Device management |

## Running Tests

```bash
# Run JSON library tests
west twister -T tests/lib/json/

# Build for specific board
west build -b native_sim tests/lib/json
west build -t run
```

## Key Files to Reference

When implementing JSON:

1. **API usage patterns**: `tests/lib/json/src/main.c`
2. **Kconfig options**: `lib/utils/Kconfig`
3. **Error handling**: Check return values in `include/zephyr/data/json.h`

When debugging:

1. **Library source**: `lib/utils/json.c`
2. **Enable logging**: Add `CONFIG_LOG=y` and trace in application code
