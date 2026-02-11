# Twister Reference

Complete reference for Twister test runner configuration and usage.

## Table of Contents

1. [Running Tests](#running-tests)
2. [testcase.yaml Configuration](#testcaseyaml-configuration)
3. [Harnesses](#harnesses)
4. [Hardware Testing](#hardware-testing)
5. [Filter Expressions](#filter-expressions)
6. [Output Files](#output-files)

---

## Running Tests

### Basic Commands

```bash
# Run all tests in a directory
./scripts/twister -T tests/kernel/

# Run on specific platform
./scripts/twister -p native_sim -T tests/kernel/threads/

# Run specific test scenario
./scripts/twister --scenario tests/kernel/semaphore/kernel.semaphore

# List available tests
./scripts/twister --list-tests -T tests/kernel/

# Build only (no execution)
./scripts/twister --build-only -T tests/subsys/

# Run all tests on all platforms
./scripts/twister --all --enable-slow

# Integration mode (uses integration_platforms)
./scripts/twister --integration -T tests/
```

### Verbose Output

```bash
# Verbose output (shows test method: qemu, native_sim, etc.)
./scripts/twister -v -T tests/kernel/

# Very verbose
./scripts/twister -vv -T tests/kernel/
```

### Filtering Options

```bash
# By tag
./scripts/twister -t kernel -T tests/

# Exclude tag
./scripts/twister -e slow -T tests/

# By architecture
./scripts/twister -a arm -T tests/

# Multiple platforms
./scripts/twister -p native_sim -p qemu_x86 -T tests/
```

---

## testcase.yaml Configuration

### Complete Key Reference

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `tags` | list | required | Categorization tags |
| `platform_allow` | list | all | Only run on these platforms |
| `platform_exclude` | list | none | Never run on these platforms |
| `arch_allow` | list | all | Only run on these architectures |
| `arch_exclude` | list | none | Never run on these architectures |
| `depends_on` | list | none | Required board features |
| `build_only` | bool | false | Build but don't run |
| `build_on_all` | bool | false | Build on all platforms (CI) |
| `timeout` | int | 60 | Seconds before kill |
| `slow` | bool | false | Only with --enable-slow |
| `skip` | bool | false | Skip unconditionally |
| `min_ram` | int | 128 | Minimum RAM in KB |
| `min_flash` | int | 512 | Minimum flash in KB |
| `extra_args` | list | none | Extra build arguments |
| `extra_configs` | list | none | Kconfig overlays |
| `filter` | string | none | Expression filter |
| `harness` | string | ztest | Test harness type |
| `harness_config` | dict | none | Harness-specific options |
| `type` | string | integration | "unit" for unit tests |
| `integration_platforms` | list | none | Platforms for --integration |
| `sysbuild` | bool | false | Use sysbuild |
| `required_snippets` | list | none | Required snippets |
| `levels` | list | none | Test levels |

### Common Patterns

**Basic Integration Test:**
```yaml
tests:
  mysubsys.feature:
    tags: feature subsys
    platform_allow:
      - native_sim
    integration_platforms:
      - native_sim
```

**Unit Test:**
```yaml
tests:
  mymodule.unit.basic:
    tags: unit
    type: unit
```

**Platform-specific Config:**
```yaml
tests:
  driver.test:
    depends_on: gpio spi
    extra_configs:
      - arch:arm:CONFIG_ARM_MPU=y
      - platform:nrf52840dk/nrf52840:CONFIG_DEBUG=y
```

**Build-only Test:**
```yaml
tests:
  driver.build_check:
    build_only: true
    platform_allow:
      - native_sim
      - qemu_x86
```

**Slow/Stress Test:**
```yaml
tests:
  kernel.stress:
    slow: true
    timeout: 300
```

### Using common Section

```yaml
common:
  tags: kernel
  platform_allow:
    - native_sim
    - qemu_x86

tests:
  kernel.semaphore.basic:
    # inherits common settings

  kernel.semaphore.stress:
    slow: true
    timeout: 120
```

---

## Harnesses

### Available Harnesses

| Harness | Purpose |
|---------|---------|
| `ztest` | Ztest framework output parsing (default) |
| `console` | Regex matching on console output |
| `pytest` | Python pytest integration |
| `gtest` | Google Test framework |
| `robot` | Robot Framework (Renode) |
| `shell` | Shell command execution |
| `power` | Power consumption measurement |
| `display_capture` | Display verification via camera |

### Ztest Harness

Default for Ztest-based tests. No special configuration needed.

```yaml
tests:
  my.test:
    harness: ztest
    harness_config:
      ztest_suite_repeat: 3
      ztest_test_repeat: 2
      ztest_test_shuffle: true
```

### Console Harness

Match regex patterns in output:

```yaml
tests:
  sample.output_check:
    harness: console
    harness_config:
      type: multi_line
      ordered: false
      regex:
        - "Initialization complete"
        - "Result: [0-9]+"
```

| Option | Type | Description |
|--------|------|-------------|
| `type` | `one_line`/`multi_line` | Matching mode |
| `regex` | list | Regular expressions to match |
| `ordered` | bool | Must match in order |
| `fixture` | string | Hardware fixture required |

### Pytest Harness

Run pytest tests against DUT:

```yaml
tests:
  integration.pytest:
    harness: pytest
    harness_config:
      pytest_root:
        - pytest/test_shell.py
        - pytest/test_api.py::test_specific
      pytest_args:
        - "-v"
        - "--log-level=DEBUG"
      pytest_dut_scope: session
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `pytest_root` | list | `pytest/` | Test files/directories |
| `pytest_args` | list | none | Extra pytest arguments |
| `pytest_dut_scope` | string | function | DUT fixture scope |

**pytest_dut_scope options:**
- `function` - DUT launched for each test
- `class` - DUT shared within test class
- `module` - DUT shared within module
- `session` - DUT launched once

### Shell Harness

Execute shell commands and verify output:

```yaml
tests:
  shell.test:
    harness: shell
    harness_config:
      shell_commands:
        - "help"
        - "version"
      regex:
        - "Available commands"
```

---

## Hardware Testing

### Single Device

```bash
./scripts/twister --device-testing \
    --device-serial /dev/ttyACM0 \
    -p nrf52840dk/nrf52840 \
    -T tests/kernel/
```

### Hardware Map

Generate and use hardware map for multiple devices:

```bash
# Generate hardware map
./scripts/twister --generate-hardware-map map.yml

# Edit map.yml to set correct platform names
# Then run:
./scripts/twister --device-testing \
    --hardware-map map.yml \
    -T tests/
```

**Example map.yml:**
```yaml
- id: 0
  serial: /dev/ttyACM0
  platform: nrf52840dk/nrf52840
  product: SEGGER J-Link
  runner: jlink
  available: true

- id: 1
  serial: /dev/ttyACM1
  platform: frdm_k64f
  product: DAPLink CMSIS-DAP
  runner: pyocd
  available: true
```

### Fixtures

For tests requiring external hardware:

```yaml
tests:
  sensor.i2c_test:
    harness: ztest
    harness_config:
      fixture: i2c_bme280
```

Mark devices with fixtures in hardware map:
```yaml
- id: 0
  serial: /dev/ttyACM0
  platform: nrf52840dk/nrf52840
  fixtures:
    - i2c_bme280
    - gpio_loopback
```

---

## Filter Expressions

### Syntax

```yaml
filter: <expression>
```

**Operators:** `and`, `or`, `not`, `==`, `!=`, `<`, `>`, `<=`, `>=`, `in`, `:`

### Kconfig Filters

```yaml
# Check if config is enabled
filter: CONFIG_BT

# Check config value
filter: CONFIG_LOG_DEFAULT_LEVEL >= 3

# Check config string
filter: CONFIG_SOC : "stm32.*"
```

### Architecture/Platform Filters

```yaml
# Same as arch_exclude
filter: not ARCH in ["x86", "arc"]

# Same as platform_allow
filter: PLATFORM in ["native_sim", "qemu_x86"]
```

### Devicetree Filters

```yaml
# Check compatible
filter: dt_compat_enabled("zephyr,gpio-keys")

# Check alias exists
filter: dt_alias_exists("led0")

# Check chosen node
filter: dt_chosen_enabled("zephyr,console")

# Check node label
filter: dt_nodelabel_enabled("i2c0")
```

**Available DT functions:**
- `dt_compat_enabled(compat)` - Enabled node with compatible
- `dt_alias_exists(alias)` - Alias exists and enabled
- `dt_chosen_enabled(chosen)` - Chosen node enabled
- `dt_nodelabel_enabled(label)` - Node label exists
- `dt_nodelabel_prop_enabled(label, prop)` - Node has property
- `dt_node_has_prop(node_id, prop)` - Node has property

### Environment Variables

```yaml
filter: *MY_ENV_VAR == "enabled"
```

---

## Output Files

### Location

Default: `twister-out/` directory

### Key Files

| File | Content |
|------|---------|
| `twister.json` | Complete results in JSON |
| `twister.log` | Build and execution logs |
| `twister_discard.csv` | Skipped tests with reasons |
| `twister_report.xml` | JUnit-style report |
| `testplan.json` | Planned test execution |

### twister.json Structure

```json
{
  "environment": {
    "zephyr_version": "3.5.0",
    "toolchain": "zephyr"
  },
  "testsuites": [
    {
      "name": "tests/kernel/semaphore/kernel.semaphore",
      "platform": "native_sim",
      "status": "passed",
      "execution_time": 1.23,
      "testcases": [
        {
          "name": "semaphore_tests.test_sem_give_take",
          "status": "passed",
          "execution_time": 0.05
        }
      ]
    }
  ]
}
```

### Cleanup Options

```bash
# Keep build directories for failed tests only
./scripts/twister --runtime-artifact-cleanup

# Force clean builds
./scripts/twister --clean

# Specify output directory
./scripts/twister -O my_output_dir -T tests/
```

---

## Quarantine

Skip flaky tests using quarantine:

```bash
./scripts/twister --quarantine-list quarantine.yaml -T tests/
```

**quarantine.yaml:**
```yaml
- scenarios:
    - kernel.semaphore.stress
  platforms:
    - qemu_x86
  comment: "Flaky under QEMU - issue #12345"
```

---

## Test Levels

Define and filter by test levels:

```yaml
tests:
  kernel.basic:
    levels:
      - smoke
      - daily

  kernel.stress:
    levels:
      - weekly
      - full
```

```bash
# Run only smoke tests
./scripts/twister --level smoke -T tests/

# Run daily tests
./scripts/twister --level daily -T tests/
```
