# Ztest Framework Reference

Complete API reference for the Zephyr Test Framework (Ztest).

## Table of Contents

1. [Suite Definition](#suite-definition)
2. [Test Macros](#test-macros)
3. [Assertion Macros](#assertion-macros)
4. [Expectation Macros](#expectation-macros)
5. [Assumption Macros](#assumption-macros)
6. [Fixtures](#fixtures)
7. [Test Rules](#test-rules)
8. [Test Result Expectations](#test-result-expectations)
9. [Skipping Tests](#skipping-tests)
10. [Parameterized Tests](#parameterized-tests)
11. [Userspace Tests](#userspace-tests)
12. [Custom test_main](#custom-test_main)
13. [Test Shuffling and Repeating](#test-shuffling-and-repeating)

---

## Suite Definition

### ZTEST_SUITE Macro

```c
ZTEST_SUITE(suite_name, predicate, setup, before, after, teardown);
```

| Parameter | Type | Purpose |
|-----------|------|---------|
| `suite_name` | identifier | Unique name within the binary |
| `predicate` | `bool (*)(const void *)` | Returns true if suite should run (NULL = always run) |
| `setup` | `void *(*)(void)` | Returns fixture pointer, runs once at suite start |
| `before` | `void (*)(void *)` | Runs before each test, receives fixture |
| `after` | `void (*)(void *)` | Runs after each test, receives fixture |
| `teardown` | `void (*)(void *)` | Runs once at suite end, receives fixture |

### Minimal Suite

```c
ZTEST_SUITE(my_suite, NULL, NULL, NULL, NULL, NULL);
```

### Suite with Predicate

```c
static bool only_when_ready(const void *state)
{
    return ((const struct test_state *)state)->ready;
}

ZTEST_SUITE(conditional_suite, only_when_ready, NULL, NULL, NULL, NULL);
```

---

## Test Macros

| Macro | Purpose | Fixture Access |
|-------|---------|----------------|
| `ZTEST(suite, test)` | Standard test | No |
| `ZTEST_F(suite, test)` | Test with fixture | Yes, via `fixture` variable |
| `ZTEST_USER(suite, test)` | Runs in userspace thread | No |
| `ZTEST_USER_F(suite, test)` | Userspace + fixture | Yes |
| `ZTEST_P(suite, test)` | Parameterized test | Via `data` pointer |

### Standard Test

```c
ZTEST(my_suite, test_addition)
{
    zassert_equal(2 + 2, 4, "math failed");
}
```

### Test with Fixture

```c
ZTEST_F(my_suite, test_with_state)
{
    zassert_equal(fixture->count, 0, "count not reset");
    fixture->count++;
}
```

---

## Assertion Macros

Assertions **fail immediately** and abort the current test.

### Boolean Assertions

| Macro | Checks |
|-------|--------|
| `zassert_true(cond, msg, ...)` | cond is true |
| `zassert_false(cond, msg, ...)` | cond is false |
| `zassert_ok(ret, msg, ...)` | ret == 0 |

### Equality Assertions

| Macro | Checks |
|-------|--------|
| `zassert_equal(a, b, msg, ...)` | a == b (integers/pointers) |
| `zassert_not_equal(a, b, msg, ...)` | a != b |
| `zassert_equal_ptr(a, b, msg, ...)` | pointer equality |

### Pointer Assertions

| Macro | Checks |
|-------|--------|
| `zassert_is_null(ptr, msg, ...)` | ptr == NULL |
| `zassert_not_null(ptr, msg, ...)` | ptr != NULL |

### Memory/String Assertions

| Macro | Checks |
|-------|--------|
| `zassert_mem_equal(a, b, size, msg, ...)` | memcmp(a, b, size) == 0 |
| `zassert_str_equal(a, b, msg, ...)` | strcmp(a, b) == 0 |

### Numeric Range Assertions

| Macro | Checks |
|-------|--------|
| `zassert_within(a, b, delta, msg, ...)` | \|a - b\| <= delta |
| `zassert_between_inclusive(a, lo, hi, msg, ...)` | lo <= a <= hi |

### Unreachable Code

```c
zassert_unreachable("should not reach here");
```

### Example Output

```
Assertion failed at main.c:42: test_example: expected 4 but got 5 (a not equal to b)
Aborted at unit test function
```

---

## Expectation Macros

Expectations **continue execution** but mark the test as failed at the end.

Replace `zassert_` prefix with `zexpect_`:

```c
ZTEST(my_suite, test_multiple_checks)
{
    zexpect_equal(result->a, 1, "a wrong");
    zexpect_equal(result->b, 2, "b wrong");  // continues even if above fails
    zexpect_equal(result->c, 3, "c wrong");
}
// Test fails at end if any expectation failed
```

All assertion variants have expectation equivalents:
- `zexpect_true`, `zexpect_false`, `zexpect_ok`
- `zexpect_equal`, `zexpect_not_equal`
- `zexpect_is_null`, `zexpect_not_null`
- `zexpect_mem_equal`, `zexpect_str_equal`
- `zexpect_within`

---

## Assumption Macros

Assumptions **skip the test** if the condition fails.

Replace `zassert_` prefix with `zassume_`:

```c
ZTEST(my_suite, test_requires_feature)
{
    zassume_true(feature_available(), "feature not available");
    // Test skipped (not failed) if feature unavailable

    run_feature_test();
}
```

All assertion variants have assumption equivalents:
- `zassume_true`, `zassume_false`, `zassume_ok`
- `zassume_equal`, `zassume_not_equal`
- `zassume_not_null`

---

## Fixtures

### Defining a Fixture

The fixture struct must be named `<suite_name>_fixture`:

```c
struct my_suite_fixture {
    int count;
    uint8_t buffer[256];
    void *resource;
};
```

### Fixture Lifecycle Functions

```c
// Called once at suite start, returns fixture pointer
static void *my_suite_setup(void)
{
    struct my_suite_fixture *f = malloc(sizeof(*f));
    zassume_not_null(f, "malloc failed");
    f->resource = acquire_resource();
    return f;
}

// Called before each test
static void my_suite_before(void *f)
{
    struct my_suite_fixture *fixture = f;
    fixture->count = 0;
    memset(fixture->buffer, 0, sizeof(fixture->buffer));
}

// Called after each test
static void my_suite_after(void *f)
{
    struct my_suite_fixture *fixture = f;
    // cleanup per-test state
}

// Called once at suite end
static void my_suite_teardown(void *f)
{
    struct my_suite_fixture *fixture = f;
    release_resource(fixture->resource);
    free(f);
}

ZTEST_SUITE(my_suite, NULL, my_suite_setup, my_suite_before,
            my_suite_after, my_suite_teardown);
```

### Using Fixtures in Tests

```c
ZTEST_F(my_suite, test_uses_fixture)
{
    // 'fixture' is automatically available, typed as struct my_suite_fixture *
    zassert_equal(fixture->count, 0, "before() should reset count");
    fixture->buffer[0] = 0xAB;
}
```

### Userspace Fixture Memory

For `ZTEST_USER_F`, fixture memory must be userspace-accessible:

```c
static ZTEST_DMEM struct shared_data userspace_data;
static ZTEST_BMEM uint8_t userspace_buffer[64];
```

---

## Test Rules

Rules run before/after **every test in the binary**, regardless of suite.

### Defining a Rule

```c
static void rule_before(const struct ztest_unit_test *test, void *fixture)
{
    ARG_UNUSED(test);
    ARG_UNUSED(fixture);
    // Reset global state, mocks, etc.
}

static void rule_after(const struct ztest_unit_test *test, void *fixture)
{
    ARG_UNUSED(test);
    ARG_UNUSED(fixture);
    // Verify invariants, cleanup
}

ZTEST_RULE(my_rule, rule_before, rule_after);
```

### Common Use: Reset FFF Mocks

```c
#include <zephyr/fff.h>

DEFINE_FFF_GLOBALS;
DEFINE_FAKE_VOID_FUNC(my_function, int);

static void fff_reset_before(const struct ztest_unit_test *test, void *fixture)
{
    ARG_UNUSED(test);
    ARG_UNUSED(fixture);
    RESET_FAKE(my_function);
}

ZTEST_RULE(fff_reset, fff_reset_before, NULL);
```

---

## Test Result Expectations

Mark tests that are **expected to fail or skip**:

```c
// This test is expected to fail - will be marked PASS if it fails
ZTEST_EXPECT_FAIL(my_suite, test_known_broken);
ZTEST(my_suite, test_known_broken)
{
    zassert_true(false, "this fails as expected");
}

// This test is expected to skip - will be marked PASS if it skips
ZTEST_EXPECT_SKIP(my_suite, test_expected_skip);
ZTEST(my_suite, test_expected_skip)
{
    zassume_true(false, "this skips as expected");
}
```

---

## Skipping Tests

### Runtime Skip

```c
ZTEST(my_suite, test_conditional)
{
    if (!hardware_present()) {
        ztest_test_skip();
        return;  // Must return after skip
    }
    // Test code...
}
```

### Compile-time Skip

```c
ZTEST(my_suite, test_feature)
{
    Z_TEST_SKIP_IFDEF(CONFIG_FEATURE_DISABLED);
    Z_TEST_SKIP_IFNDEF(CONFIG_REQUIRED_FEATURE);
    // Test runs only if conditions met
}
```

### Ifdef Pattern

```c
#ifdef CONFIG_MY_FEATURE
ZTEST(my_suite, test_feature)
{
    // Test implementation
}
#else
ZTEST(my_suite, test_feature)
{
    ztest_test_skip();
}
#endif
```

---

## Parameterized Tests

### Defining Parameters

```c
struct test_params {
    int input;
    int expected;
};

static struct test_params params[] = {
    {.input = 0, .expected = 0},
    {.input = 1, .expected = 1},
    {.input = 2, .expected = 4},
};

ZTEST_P(my_suite, test_parameterized, params);
```

### Using Parameters

```c
ZTEST_P(my_suite, test_parameterized)
{
    // 'data' points to current parameter
    int result = square(data->input);
    zassert_equal(result, data->expected,
                  "square(%d) = %d, expected %d",
                  data->input, result, data->expected);
}
```

---

## Userspace Tests

When `CONFIG_USERSPACE=y`, userspace tests run in unprivileged mode:

```c
// Runs in userspace thread
ZTEST_USER(my_suite, test_userspace)
{
    // Cannot access kernel memory
    // Tests user-facing API behavior
}

// Userspace with fixture
ZTEST_USER_F(my_suite, test_userspace_with_fixture)
{
    // fixture must use ZTEST_DMEM/ZTEST_BMEM for shared memory
}
```

---

## Custom test_main

Override the default test runner for complex scenarios:

```c
#include <zephyr/ztest.h>

void test_main(void)
{
    struct test_state state = {0};

    // Run suites that check for phase == 0
    state.phase = 0;
    ztest_run_all(&state, false, 1, 1);

    // Run suites that check for phase == 1
    state.phase = 1;
    ztest_run_all(&state, false, 1, 1);

    // Verify all suites ran
    ztest_verify_all_test_suites_ran();
}
```

**Note**: Requires `CONFIG_ZTEST_CUSTOM_TEST_MAIN=y`

---

## Test Shuffling and Repeating

### Kconfig Options

```
# Randomize test order
CONFIG_ZTEST_SHUFFLE=y

# Repeat tests
CONFIG_ZTEST_REPEAT=y
CONFIG_ZTEST_SUITE_REPEAT_COUNT=3
CONFIG_ZTEST_TEST_REPEAT_COUNT=3
```

### Native Simulator Selection

```bash
# List all tests
./zephyr.exe -list

# Run specific tests
./zephyr.exe -test="my_suite::test_one,other_suite::test_two"

# Run all tests in a suite
./zephyr.exe -test="my_suite::*"
```

---

## Best Practices

1. **Test naming**: Prefix with `test_`, be descriptive
2. **One assertion focus**: Each test should verify one behavior
3. **Use fixtures**: For shared setup/teardown logic
4. **Use rules**: For cross-suite concerns (mock reset, invariant checks)
5. **Use expectations**: When testing multiple related conditions
6. **Use assumptions**: For optional test prerequisites
7. **Document tests**: Use doxygen comments for test purposes
