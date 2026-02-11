# FFF Mocking Reference

Complete reference for using FFF (Fake Function Framework) for mocking in Zephyr tests.

## Table of Contents

1. [Setup](#setup)
2. [Basic Fakes](#basic-fakes)
3. [Checking Calls](#checking-calls)
4. [Return Values](#return-values)
5. [Custom Fake Implementations](#custom-fake-implementations)
6. [Resetting Fakes](#resetting-fakes)
7. [FFF Fakes List Pattern](#fff-fakes-list-pattern)
8. [Test Rules for Mocks](#test-rules-for-mocks)
9. [Common Patterns](#common-patterns)

---

## Setup

### Include Header

```c
#include <zephyr/fff.h>
```

### Define FFF Globals

**Required once per test binary** (typically in main test file):

```c
DEFINE_FFF_GLOBALS;
```

---

## Basic Fakes

### Void Functions

```c
// For: void my_func(int arg1, char *arg2);
DEFINE_FAKE_VOID_FUNC(my_func, int, char *);
```

### Value-Returning Functions

```c
// For: int my_func(int arg1, char *arg2);
DEFINE_FAKE_VALUE_FUNC(int, my_func, int, char *);
```

### Variadic Functions

```c
// For: int printf_like(const char *fmt, ...);
DEFINE_FAKE_VALUE_FUNC_VARARG(int, printf_like, const char *, ...);
```

### No-Argument Functions

```c
// For: void init(void);
DEFINE_FAKE_VOID_FUNC(init);

// For: int get_value(void);
DEFINE_FAKE_VALUE_FUNC(int, get_value);
```

---

## Checking Calls

### Call Count

```c
ZTEST(my_suite, test_call_count)
{
    my_func(1, "hello");
    my_func(2, "world");

    zassert_equal(my_func_fake.call_count, 2, "expected 2 calls");
}
```

### Argument History

```c
ZTEST(my_suite, test_arguments)
{
    my_func(42, "test");

    zassert_equal(my_func_fake.arg0_val, 42, "wrong first arg");
    zassert_str_equal(my_func_fake.arg1_val, "test", "wrong second arg");
}
```

### Argument History (Multiple Calls)

```c
ZTEST(my_suite, test_arg_history)
{
    my_func(1, "a");
    my_func(2, "b");
    my_func(3, "c");

    // Access history (default keeps last 50 calls)
    zassert_equal(my_func_fake.arg0_history[0], 1, "first call arg0");
    zassert_equal(my_func_fake.arg0_history[1], 2, "second call arg0");
    zassert_equal(my_func_fake.arg0_history[2], 3, "third call arg0");
}
```

---

## Return Values

### Static Return Value

```c
ZTEST(my_suite, test_return_value)
{
    get_value_fake.return_val = 42;

    int result = get_value();
    zassert_equal(result, 42, "wrong return");
}
```

### Sequence of Return Values

```c
ZTEST(my_suite, test_return_sequence)
{
    int returns[] = {1, 2, 3, -1};
    SET_RETURN_SEQ(my_func, returns, 4);

    zassert_equal(my_func(0, NULL), 1, "first call");
    zassert_equal(my_func(0, NULL), 2, "second call");
    zassert_equal(my_func(0, NULL), 3, "third call");
    zassert_equal(my_func(0, NULL), -1, "fourth call");
    // Subsequent calls return last value
    zassert_equal(my_func(0, NULL), -1, "fifth call");
}
```

---

## Custom Fake Implementations

### Simple Custom Fake

```c
// Custom implementation
int my_func_custom(int arg1, char *arg2)
{
    if (arg1 < 0) {
        return -EINVAL;
    }
    return strlen(arg2);
}

ZTEST(my_suite, test_custom_fake)
{
    my_func_fake.custom_fake = my_func_custom;

    zassert_equal(my_func(-1, "test"), -EINVAL, "should fail");
    zassert_equal(my_func(1, "hello"), 5, "should return length");
}
```

### Custom Fake with State

```c
static int call_counter = 0;
static int stored_values[10];

int my_func_with_state(int value, char *unused)
{
    stored_values[call_counter++] = value;
    return 0;
}

ZTEST(my_suite, test_stateful_fake)
{
    call_counter = 0;
    my_func_fake.custom_fake = my_func_with_state;

    my_func(10, NULL);
    my_func(20, NULL);

    zassert_equal(stored_values[0], 10, "first value");
    zassert_equal(stored_values[1], 20, "second value");
}
```

### Custom Fake Sequence

```c
int fake_first_call(int arg) { return 1; }
int fake_second_call(int arg) { return 2; }
int fake_remaining(int arg) { return 99; }

ZTEST(my_suite, test_custom_sequence)
{
    int (*fakes[])(int) = {fake_first_call, fake_second_call, fake_remaining};
    SET_CUSTOM_FAKE_SEQ(my_func, fakes, 3);

    zassert_equal(my_func(0), 1, "first");
    zassert_equal(my_func(0), 2, "second");
    zassert_equal(my_func(0), 99, "third");
    zassert_equal(my_func(0), 99, "fourth (stays on last)");
}
```

---

## Resetting Fakes

### Reset Single Fake

```c
RESET_FAKE(my_func);
```

This resets:
- `call_count` to 0
- All argument history
- `return_val` to 0
- `custom_fake` to NULL

### Reset in Before Function

```c
static void my_suite_before(void *f)
{
    RESET_FAKE(func1);
    RESET_FAKE(func2);
    RESET_FAKE(func3);
}
```

---

## FFF Fakes List Pattern

For many fakes, use the list macro pattern:

### Define List

```c
// In header or top of file
#define FFF_FAKES_LIST(FAKE) \
    FAKE(func1)              \
    FAKE(func2)              \
    FAKE(func3)              \
    FAKE(func4)
```

### Reset All with List

```c
static void reset_all_fakes(void)
{
    FFF_FAKES_LIST(RESET_FAKE);
}
```

### Use in Test Rule

```c
#define FFF_FAKES_LIST(FAKE) \
    FAKE(sensor_read)        \
    FAKE(sensor_write)       \
    FAKE(sensor_init)

static void fff_reset_before(const struct ztest_unit_test *test, void *f)
{
    ARG_UNUSED(test);
    ARG_UNUSED(f);
    FFF_FAKES_LIST(RESET_FAKE);
}

ZTEST_RULE(fff_reset, fff_reset_before, NULL);
```

### Multiple Lists for Organization

```c
// Networking fakes
#define NET_FAKES_LIST(FAKE) \
    FAKE(net_send)           \
    FAKE(net_recv)

// Storage fakes
#define STORAGE_FAKES_LIST(FAKE) \
    FAKE(flash_read)             \
    FAKE(flash_write)

// Reset all
#define DO_FOREACH_FAKE(FAKE) \
    NET_FAKES_LIST(FAKE)      \
    STORAGE_FAKES_LIST(FAKE)

static void reset_all(void)
{
    DO_FOREACH_FAKE(RESET_FAKE);
}
```

---

## Test Rules for Mocks

### Global Mock Reset Rule

```c
#include <zephyr/fff.h>
#include <zephyr/ztest.h>

DEFINE_FFF_GLOBALS;

// Define fakes
DEFINE_FAKE_VALUE_FUNC(int, hw_init);
DEFINE_FAKE_VOID_FUNC(hw_deinit);
DEFINE_FAKE_VALUE_FUNC(int, hw_read, uint8_t *, size_t);

#define FFF_FAKES_LIST(FAKE) \
    FAKE(hw_init)            \
    FAKE(hw_deinit)          \
    FAKE(hw_read)

static void fff_reset_rule_before(const struct ztest_unit_test *test, void *fixture)
{
    ARG_UNUSED(test);
    ARG_UNUSED(fixture);
    FFF_FAKES_LIST(RESET_FAKE);
}

ZTEST_RULE(fff_reset_rule, fff_reset_rule_before, NULL);
```

---

## Common Patterns

### Mocking a Driver API

```c
// Mock sensor driver
DEFINE_FAKE_VALUE_FUNC(int, sensor_sample_fetch, const struct device *);
DEFINE_FAKE_VALUE_FUNC(int, sensor_channel_get, const struct device *,
                       enum sensor_channel, struct sensor_value *);

ZTEST(my_suite, test_sensor_read)
{
    struct sensor_value expected = {.val1 = 25, .val2 = 500000};

    sensor_sample_fetch_fake.return_val = 0;

    // Custom fake to set output parameter
    sensor_channel_get_fake.custom_fake =
        [](const struct device *dev, enum sensor_channel chan,
           struct sensor_value *val) {
            val->val1 = 25;
            val->val2 = 500000;
            return 0;
        };

    // Call code under test
    int result = my_sensor_read_function(dev);

    zassert_equal(result, 0, "read failed");
    zassert_equal(sensor_sample_fetch_fake.call_count, 1, "fetch not called");
}
```

### Mocking with Error Injection

```c
ZTEST(my_suite, test_error_handling)
{
    // First call succeeds, second fails
    int returns[] = {0, -EIO};
    SET_RETURN_SEQ(device_read, returns, 2);

    // First read should succeed
    zassert_ok(do_operation(), "first op should pass");

    // Second read should fail and be handled
    zassert_equal(do_operation(), -EIO, "should propagate error");
}
```

### Verifying Call Order

```c
DEFINE_FAKE_VOID_FUNC(step1);
DEFINE_FAKE_VOID_FUNC(step2);
DEFINE_FAKE_VOID_FUNC(step3);

ZTEST(my_suite, test_initialization_order)
{
    initialize_system();

    // Verify call order using global call counter
    zassert_true(step1_fake.call_count > 0, "step1 not called");
    zassert_true(step2_fake.call_count > 0, "step2 not called");
    zassert_true(step3_fake.call_count > 0, "step3 not called");

    // Use FFF's call order tracking
    // Each fake has .caller_history if FFF_CALL_HISTORY_LEN > 0
}
```

### Mocking Callbacks

```c
typedef void (*callback_t)(int result, void *user_data);

// The function that accepts a callback
DEFINE_FAKE_VOID_FUNC(async_operation, callback_t, void *);

ZTEST(my_suite, test_callback_invoked)
{
    static int callback_result = -1;
    static void *callback_data = NULL;

    // Custom fake that captures and invokes callback
    async_operation_fake.custom_fake =
        [](callback_t cb, void *data) {
            // Simulate async completion
            cb(42, data);
        };

    void *my_data = (void *)0x1234;

    // Callback implementation for test
    callback_t my_callback = [](int result, void *data) {
        callback_result = result;
        callback_data = data;
    };

    async_operation(my_callback, my_data);

    zassert_equal(callback_result, 42, "callback not invoked correctly");
    zassert_equal(callback_data, my_data, "wrong user data");
}
```

---

## Zephyr Fake Drivers

Zephyr provides pre-built fake drivers:

| Fake | Devicetree Compatible |
|------|----------------------|
| Fake CAN | `zephyr,fake-can` |
| Fake EEPROM | `zephyr,fake-eeprom` |

Enable via devicetree overlay:
```dts
/ {
    fake_eeprom: eeprom@0 {
        compatible = "zephyr,fake-eeprom";
        size = <1024>;
    };
};
```

---

## FFF Extensions (Zephyr)

Zephyr provides simplified macro wrappers. See `<zephyr/fff.h>` for:

- `ZTEST_FFF_FAKE` - Simplified fake declaration
- Additional helper macros for common patterns

---

## Best Practices

1. **Always reset fakes** in before function or test rule
2. **Use FFF_FAKES_LIST** macro for maintainability
3. **Prefer custom_fake** for complex behavior over return sequences
4. **Check call_count** to verify function was called
5. **Verify arguments** using arg_val or arg_history
6. **Organize fakes** by subsystem with separate lists
7. **Document fake behavior** in test comments
