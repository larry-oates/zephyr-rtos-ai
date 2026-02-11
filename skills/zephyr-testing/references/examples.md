# Zephyr Testing Examples

Complete working test examples for common scenarios.

## Table of Contents

1. [Minimal Integration Test](#minimal-integration-test)
2. [Minimal Unit Test](#minimal-unit-test)
3. [Test with Fixtures](#test-with-fixtures)
4. [Test with FFF Mocking](#test-with-fff-mocking)
5. [Test with Multiple Suites](#test-with-multiple-suites)
6. [Parameterized Tests](#parameterized-tests)
7. [Stress Test with Ztress](#stress-test-with-ztress)
8. [Pytest Integration Test](#pytest-integration-test)

---

## Minimal Integration Test

### File Structure

```
tests/mysubsys/feature/
├── CMakeLists.txt
├── prj.conf
├── testcase.yaml
└── src/
    └── main.c
```

### CMakeLists.txt

```cmake
cmake_minimum_required(VERSION 3.20.0)
find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(my_test)

target_sources(app PRIVATE src/main.c)
```

### prj.conf

```
CONFIG_ZTEST=y
```

### testcase.yaml

```yaml
tests:
  mysubsys.feature.basic:
    tags: feature
    platform_allow:
      - native_sim
    integration_platforms:
      - native_sim
```

### src/main.c

```c
#include <zephyr/ztest.h>

ZTEST_SUITE(feature_tests, NULL, NULL, NULL, NULL, NULL);

ZTEST(feature_tests, test_basic_assertion)
{
    zassert_true(1, "true should be true");
    zassert_false(0, "false should be false");
}

ZTEST(feature_tests, test_equality)
{
    int a = 42;
    int b = 42;
    zassert_equal(a, b, "a and b should be equal");
}

ZTEST(feature_tests, test_string)
{
    const char *expected = "hello";
    const char *actual = "hello";
    zassert_str_equal(actual, expected, "strings should match");
}
```

### Run

```bash
./scripts/twister -T tests/mysubsys/feature/ -p native_sim
```

---

## Minimal Unit Test

Unit tests compile only the module under test without full Zephyr.

### File Structure

```
tests/unit/mymodule/
├── CMakeLists.txt
├── prj.conf
├── testcase.yaml
└── src/
    ├── main.c
    └── mymodule.c  # Module under test
```

### CMakeLists.txt

```cmake
cmake_minimum_required(VERSION 3.20.0)
project(mymodule_unit_test)

find_package(Zephyr COMPONENTS unittest REQUIRED HINTS $ENV{ZEPHYR_BASE})

target_sources(testbinary PRIVATE
    src/main.c
    src/mymodule.c
)

target_include_directories(testbinary PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)
```

### prj.conf

```
CONFIG_ZTEST=y
```

### testcase.yaml

```yaml
tests:
  mymodule.unit.basic:
    tags: unit
    type: unit
```

### src/mymodule.c

```c
/* Module under test */
#include "mymodule.h"

int mymodule_add(int a, int b)
{
    return a + b;
}

int mymodule_multiply(int a, int b)
{
    return a * b;
}
```

### src/main.c

```c
#include <zephyr/ztest.h>
#include "mymodule.h"

ZTEST_SUITE(mymodule_tests, NULL, NULL, NULL, NULL, NULL);

ZTEST(mymodule_tests, test_add)
{
    zassert_equal(mymodule_add(2, 3), 5, "2 + 3 should be 5");
    zassert_equal(mymodule_add(-1, 1), 0, "-1 + 1 should be 0");
}

ZTEST(mymodule_tests, test_multiply)
{
    zassert_equal(mymodule_multiply(3, 4), 12, "3 * 4 should be 12");
    zassert_equal(mymodule_multiply(0, 100), 0, "0 * 100 should be 0");
}
```

---

## Test with Fixtures

### src/main.c

```c
#include <zephyr/ztest.h>
#include <stdlib.h>
#include <string.h>

/* Fixture struct - must be named <suite_name>_fixture */
struct buffer_tests_fixture {
    uint8_t *buffer;
    size_t size;
    size_t used;
};

/* Setup - runs once at suite start */
static void *buffer_tests_setup(void)
{
    struct buffer_tests_fixture *f = malloc(sizeof(*f));

    zassume_not_null(f, "malloc failed");

    f->size = 256;
    f->buffer = malloc(f->size);
    zassume_not_null(f->buffer, "buffer malloc failed");

    return f;
}

/* Before - runs before each test */
static void buffer_tests_before(void *f)
{
    struct buffer_tests_fixture *fixture = f;

    memset(fixture->buffer, 0, fixture->size);
    fixture->used = 0;
}

/* Teardown - runs once at suite end */
static void buffer_tests_teardown(void *f)
{
    struct buffer_tests_fixture *fixture = f;

    free(fixture->buffer);
    free(fixture);
}

ZTEST_SUITE(buffer_tests, NULL, buffer_tests_setup,
            buffer_tests_before, NULL, buffer_tests_teardown);

ZTEST_F(buffer_tests, test_buffer_empty)
{
    zassert_equal(fixture->used, 0, "buffer should be empty");
    zassert_equal(fixture->buffer[0], 0, "buffer should be zeroed");
}

ZTEST_F(buffer_tests, test_buffer_write)
{
    fixture->buffer[0] = 0xAB;
    fixture->used = 1;

    zassert_equal(fixture->used, 1, "used should be 1");
    zassert_equal(fixture->buffer[0], 0xAB, "data should be written");
}

ZTEST_F(buffer_tests, test_buffer_size)
{
    zassert_equal(fixture->size, 256, "size should be 256");
}
```

---

## Test with FFF Mocking

### src/main.c

```c
#include <zephyr/ztest.h>
#include <zephyr/fff.h>

DEFINE_FFF_GLOBALS;

/* Mock external dependencies */
DEFINE_FAKE_VALUE_FUNC(int, external_init);
DEFINE_FAKE_VALUE_FUNC(int, external_read, uint8_t *, size_t);
DEFINE_FAKE_VOID_FUNC(external_cleanup);

/* FFF fakes list for easy reset */
#define FFF_FAKES_LIST(FAKE) \
    FAKE(external_init)      \
    FAKE(external_read)      \
    FAKE(external_cleanup)

/* Code under test */
static int my_init(void)
{
    return external_init();
}

static int my_read(uint8_t *buf, size_t len)
{
    if (external_init() != 0) {
        return -1;
    }
    int result = external_read(buf, len);
    external_cleanup();
    return result;
}

/* Test rule to reset all fakes before each test */
static void fff_reset_before(const struct ztest_unit_test *test, void *fixture)
{
    ARG_UNUSED(test);
    ARG_UNUSED(fixture);
    FFF_FAKES_LIST(RESET_FAKE);
}

ZTEST_RULE(fff_reset, fff_reset_before, NULL);

ZTEST_SUITE(mock_tests, NULL, NULL, NULL, NULL, NULL);

ZTEST(mock_tests, test_init_success)
{
    external_init_fake.return_val = 0;

    int result = my_init();

    zassert_equal(result, 0, "init should succeed");
    zassert_equal(external_init_fake.call_count, 1, "init should be called once");
}

ZTEST(mock_tests, test_init_failure)
{
    external_init_fake.return_val = -1;

    int result = my_init();

    zassert_equal(result, -1, "init should fail");
}

ZTEST(mock_tests, test_read_success)
{
    external_init_fake.return_val = 0;
    external_read_fake.return_val = 10;

    uint8_t buf[32];
    int result = my_read(buf, sizeof(buf));

    zassert_equal(result, 10, "read should return 10");
    zassert_equal(external_init_fake.call_count, 1, "init called");
    zassert_equal(external_read_fake.call_count, 1, "read called");
    zassert_equal(external_cleanup_fake.call_count, 1, "cleanup called");

    /* Verify read was called with correct arguments */
    zassert_equal(external_read_fake.arg0_val, buf, "buffer passed");
    zassert_equal(external_read_fake.arg1_val, sizeof(buf), "size passed");
}

ZTEST(mock_tests, test_read_fails_if_init_fails)
{
    external_init_fake.return_val = -1;

    uint8_t buf[32];
    int result = my_read(buf, sizeof(buf));

    zassert_equal(result, -1, "should fail");
    zassert_equal(external_read_fake.call_count, 0, "read not called");
}

/* Custom fake example */
static int custom_read_impl(uint8_t *buf, size_t len)
{
    memset(buf, 0xAB, len);
    return len;
}

ZTEST(mock_tests, test_read_with_custom_fake)
{
    external_init_fake.return_val = 0;
    external_read_fake.custom_fake = custom_read_impl;

    uint8_t buf[8];
    int result = my_read(buf, sizeof(buf));

    zassert_equal(result, 8, "should read 8 bytes");
    zassert_equal(buf[0], 0xAB, "buffer should be filled");
}
```

---

## Test with Multiple Suites

### src/main.c

```c
#include <zephyr/ztest.h>

/* First suite - basic tests */
ZTEST_SUITE(basic_tests, NULL, NULL, NULL, NULL, NULL);

ZTEST(basic_tests, test_one)
{
    zassert_true(1, "test one");
}

ZTEST(basic_tests, test_two)
{
    zassert_true(1, "test two");
}

/* Second suite - with predicate */
struct test_state {
    bool advanced_enabled;
};

static bool advanced_predicate(const void *state)
{
    const struct test_state *s = state;
    return s != NULL && s->advanced_enabled;
}

ZTEST_SUITE(advanced_tests, advanced_predicate, NULL, NULL, NULL, NULL);

ZTEST(advanced_tests, test_advanced_one)
{
    zassert_true(1, "advanced test");
}

/* Third suite - with fixture */
struct fixture_tests_fixture {
    int value;
};

static void *fixture_tests_setup(void)
{
    struct fixture_tests_fixture *f = malloc(sizeof(*f));
    f->value = 42;
    return f;
}

static void fixture_tests_teardown(void *f)
{
    free(f);
}

ZTEST_SUITE(fixture_tests, NULL, fixture_tests_setup,
            NULL, NULL, fixture_tests_teardown);

ZTEST_F(fixture_tests, test_with_fixture)
{
    zassert_equal(fixture->value, 42, "fixture value");
}
```

---

## Parameterized Tests

### src/main.c

```c
#include <zephyr/ztest.h>

/* Test parameters */
struct math_params {
    int a;
    int b;
    int expected_sum;
    int expected_product;
};

/* Parameter sets */
static struct math_params math_test_params[] = {
    {.a = 1, .b = 2, .expected_sum = 3, .expected_product = 2},
    {.a = 0, .b = 0, .expected_sum = 0, .expected_product = 0},
    {.a = -1, .b = 1, .expected_sum = 0, .expected_product = -1},
    {.a = 100, .b = 200, .expected_sum = 300, .expected_product = 20000},
};

ZTEST_SUITE(param_tests, NULL, NULL, NULL, NULL, NULL);

/* Parameterized test - runs once for each parameter set */
ZTEST_P(param_tests, test_addition, math_test_params)
{
    int result = data->a + data->b;
    zassert_equal(result, data->expected_sum,
                  "%d + %d = %d, expected %d",
                  data->a, data->b, result, data->expected_sum);
}

ZTEST_P(param_tests, test_multiplication, math_test_params)
{
    int result = data->a * data->b;
    zassert_equal(result, data->expected_product,
                  "%d * %d = %d, expected %d",
                  data->a, data->b, result, data->expected_product);
}
```

---

## Stress Test with Ztress

### prj.conf

```
CONFIG_ZTEST=y
CONFIG_ZTRESS=y
CONFIG_ZTRESS_MAX_THREADS=3
CONFIG_SYS_CLOCK_TICKS_PER_SEC=100000
```

### src/main.c

```c
#include <zephyr/ztest.h>
#include <zephyr/kernel.h>

/* Shared state for stress test */
static atomic_t counter = ATOMIC_INIT(0);
static K_SEM_DEFINE(sem, 1, 1);

/* Handler for timer context (highest priority) */
static bool timer_handler(void *user_data, uint32_t cnt, bool last_iter)
{
    ARG_UNUSED(user_data);
    ARG_UNUSED(cnt);
    ARG_UNUSED(last_iter);

    atomic_inc(&counter);
    return true;
}

/* Handler for high priority thread */
static bool thread_high_handler(void *user_data, uint32_t cnt, bool last_iter)
{
    ARG_UNUSED(user_data);
    ARG_UNUSED(cnt);
    ARG_UNUSED(last_iter);

    k_sem_take(&sem, K_FOREVER);
    atomic_inc(&counter);
    k_sem_give(&sem);
    return true;
}

/* Handler for low priority thread */
static bool thread_low_handler(void *user_data, uint32_t cnt, bool last_iter)
{
    ARG_UNUSED(user_data);
    ARG_UNUSED(cnt);
    ARG_UNUSED(last_iter);

    k_sem_take(&sem, K_FOREVER);
    atomic_inc(&counter);
    k_sem_give(&sem);
    return true;
}

ZTEST_SUITE(stress_tests, NULL, NULL, NULL, NULL, NULL);

ZTEST(stress_tests, test_concurrent_access)
{
    atomic_set(&counter, 0);

    /* Set 10 second timeout */
    ztress_set_timeout(K_MSEC(10000));

    /* Run stress test with:
     * - Timer context: 10000 iterations, 20 tick initial delay
     * - High priority thread: 10000 iterations, no preemption requirement
     * - Low priority thread: 10000 iterations, expect 100 preemptions
     */
    ZTRESS_EXECUTE(
        ZTRESS_TIMER(timer_handler, NULL, 10000, Z_TIMEOUT_TICKS(20)),
        ZTRESS_THREAD(thread_high_handler, NULL, 10000, 0, Z_TIMEOUT_TICKS(20)),
        ZTRESS_THREAD(thread_low_handler, NULL, 10000, 100, Z_TIMEOUT_TICKS(20))
    );

    /* Verify all iterations completed */
    zassert_true(atomic_get(&counter) >= 30000,
                 "expected at least 30000 iterations");
}
```

---

## Pytest Integration Test

### File Structure

```
tests/integration/shell_test/
├── CMakeLists.txt
├── prj.conf
├── testcase.yaml
├── src/
│   └── main.c
└── pytest/
    └── test_shell.py
```

### testcase.yaml

```yaml
tests:
  integration.shell.pytest:
    harness: pytest
    harness_config:
      pytest_root:
        - pytest/test_shell.py
      pytest_dut_scope: session
    platform_allow:
      - native_sim
```

### prj.conf

```
CONFIG_ZTEST=y
CONFIG_SHELL=y
CONFIG_SHELL_BACKEND_SERIAL=y
```

### src/main.c

```c
#include <zephyr/kernel.h>
#include <zephyr/shell/shell.h>

static int cmd_hello(const struct shell *sh, size_t argc, char **argv)
{
    shell_print(sh, "Hello from Zephyr!");
    return 0;
}

static int cmd_add(const struct shell *sh, size_t argc, char **argv)
{
    if (argc != 3) {
        shell_error(sh, "Usage: add <a> <b>");
        return -EINVAL;
    }

    int a = atoi(argv[1]);
    int b = atoi(argv[2]);

    shell_print(sh, "Result: %d", a + b);
    return 0;
}

SHELL_CMD_REGISTER(hello, NULL, "Say hello", cmd_hello);
SHELL_CMD_REGISTER(add, NULL, "Add two numbers", cmd_add);

int main(void)
{
    return 0;
}
```

### pytest/test_shell.py

```python
import pytest
import re

def test_hello_command(shell):
    """Test the hello command."""
    lines = shell.exec_command("hello")
    assert "Hello from Zephyr!" in lines, f"Unexpected output: {lines}"

def test_add_command(shell):
    """Test the add command."""
    lines = shell.exec_command("add 2 3")
    assert "Result: 5" in lines, f"Unexpected output: {lines}"

def test_add_large_numbers(shell):
    """Test add with larger numbers."""
    lines = shell.exec_command("add 100 200")
    assert "Result: 300" in lines, f"Unexpected output: {lines}"

def test_add_negative(shell):
    """Test add with negative numbers."""
    lines = shell.exec_command("add -5 10")
    assert "Result: 5" in lines, f"Unexpected output: {lines}"

def test_add_missing_args(shell):
    """Test add with missing arguments."""
    lines = shell.exec_command("add 5")
    assert "Usage:" in lines or "error" in lines.lower(), \
        f"Expected error message, got: {lines}"
```

### Run

```bash
./scripts/twister -T tests/integration/shell_test/ -p native_sim
```

---

## Notes

1. **Integration tests** use full Zephyr and can run on actual boards or emulators
2. **Unit tests** compile only the module under test (faster iteration)
3. **Fixtures** are best for shared setup that needs cleanup
4. **FFF mocks** are essential for isolating code from dependencies
5. **Test rules** apply to all tests in the binary
6. **Pytest** is powerful for complex integration scenarios requiring host logic
