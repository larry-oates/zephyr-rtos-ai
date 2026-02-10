# SMF API Reference

## Table of Contents

- [Kconfig Options](#kconfig-options)
- [Macros](#macros)
- [Types](#types)
- [Functions](#functions)

## Kconfig Options

| Option | Description |
|--------|-------------|
| `CONFIG_SMF` | Enable State Machine Framework |
| `CONFIG_SMF_ANCESTOR_SUPPORT` | Enable parent state support (hierarchical state machines) |
| `CONFIG_SMF_INITIAL_TRANSITION` | Enable initial transitions to child states (requires `SMF_ANCESTOR_SUPPORT`) |

## Macros

### SMF_CREATE_STATE

Create a state definition.

```c
SMF_CREATE_STATE(entry, run, exit, parent, initial)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `entry` | `state_method` or `NULL` | Entry action function |
| `run` | `state_execution` or `NULL` | Run action function |
| `exit` | `state_method` or `NULL` | Exit action function |
| `parent` | `const struct smf_state *` or `NULL` | Parent state (requires `CONFIG_SMF_ANCESTOR_SUPPORT`) |
| `initial` | `const struct smf_state *` or `NULL` | Initial child state (requires `CONFIG_SMF_INITIAL_TRANSITION`) |

### SMF_CTX

Cast user object to state machine context.

```c
SMF_CTX(o)
```

**Usage**: `SMF_CTX(&user_obj)` instead of `(struct smf_ctx *)&user_obj`

## Types

### struct smf_state

```c
struct smf_state {
    const state_method entry;           // Entry action (optional)
    const state_execution run;          // Run action (optional)
    const state_method exit;            // Exit action (optional)
#ifdef CONFIG_SMF_ANCESTOR_SUPPORT
    const struct smf_state *parent;     // Parent state (optional)
#ifdef CONFIG_SMF_INITIAL_TRANSITION
    const struct smf_state *initial;    // Initial child state (optional)
#endif
#endif
};
```

### struct smf_ctx

```c
struct smf_ctx {
    const struct smf_state *current;    // Current leaf state
    const struct smf_state *previous;   // Previous state
#ifdef CONFIG_SMF_ANCESTOR_SUPPORT
    const struct smf_state *executing;  // Currently executing state (may be parent)
#endif
    int32_t terminate_val;              // Termination value
    uint32_t internal;                  // Internal state tracking
};
```

### enum smf_state_result

```c
enum smf_state_result {
    SMF_EVENT_HANDLED,    // Event was handled, don't propagate to parent
    SMF_EVENT_PROPAGATE,  // Propagate event to parent run action (HSM only)
};
```

### Function Pointer Types

```c
typedef void (*state_method)(void *obj);              // Entry/exit signature
typedef enum smf_state_result (*state_execution)(void *obj);  // Run signature
```

## Functions

### smf_set_initial

Initialize the state machine and set initial state.

```c
void smf_set_initial(struct smf_ctx *ctx, const struct smf_state *init_state);
```

| Parameter | Description |
|-----------|-------------|
| `ctx` | State machine context |
| `init_state` | Initial state (should be leaf state unless `CONFIG_SMF_INITIAL_TRANSITION` is enabled) |

**Behavior**:
- Sets `ctx->current` to `init_state`
- Sets `ctx->previous` to `NULL`
- Executes entry actions from topmost ancestor to `init_state`
- With `CONFIG_SMF_INITIAL_TRANSITION`: follows initial transitions to deepest child

### smf_set_state

Transition to a new state.

```c
void smf_set_state(struct smf_ctx *ctx, const struct smf_state *new_state);
```

| Parameter | Description |
|-----------|-------------|
| `ctx` | State machine context |
| `new_state` | Target state (must not be `NULL`) |

**Behavior**:
- Executes exit actions from current state up to (not including) Least Common Ancestor (LCA)
- Executes entry actions from LCA down to `new_state`
- For self-transitions: both exit and entry are called
- With `CONFIG_SMF_INITIAL_TRANSITION`: follows initial transitions to deepest child

**Restrictions**:
- Call only from entry or run actions, NEVER from exit actions
- Calling from exit action logs error and is ignored

### smf_run_state

Execute one iteration of the state machine.

```c
int32_t smf_run_state(struct smf_ctx *ctx);
```

| Parameter | Description |
|-----------|-------------|
| `ctx` | State machine context |

**Returns**:
- `0`: Continue running
- Non-zero: Termination value (stop calling `smf_run_state`)

**Behavior**:
- Executes current state's run action
- With `CONFIG_SMF_ANCESTOR_SUPPORT`: propagates to parent run actions if `SMF_EVENT_PROPAGATE` returned

### smf_set_terminate

Request state machine termination.

```c
void smf_set_terminate(struct smf_ctx *ctx, int32_t val);
```

| Parameter | Description |
|-----------|-------------|
| `ctx` | State machine context |
| `val` | Non-zero termination value returned by `smf_run_state` |

**Usage**: Call from any action (entry, run, or exit).

### smf_get_current_leaf_state

Get the current leaf state.

```c
static inline const struct smf_state *smf_get_current_leaf_state(const struct smf_ctx *const ctx);
```

**Returns**: `ctx->current` (the leaf state)

**Note**: May return parent state if HSM is malformed (missing initial transitions).

### smf_get_current_executing_state

Get the state whose action is currently executing.

```c
static inline const struct smf_state *smf_get_current_executing_state(const struct smf_ctx *const ctx);
```

**Returns**:
- With `CONFIG_SMF_ANCESTOR_SUPPORT`: `ctx->executing` (may be parent)
- Without: `ctx->current`

## Header Location

```c
#include <zephyr/smf.h>
```
