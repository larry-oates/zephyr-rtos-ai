# Hierarchical State Machines (HSM)

## Table of Contents

- [Overview](#overview)
- [Kconfig Setup](#kconfig-setup)
- [Parent-Child State Structure](#parent-child-state-structure)
- [Initial Transitions](#initial-transitions)
- [Action Execution Order](#action-execution-order)
- [Event Propagation](#event-propagation)
- [UML Compliance](#uml-compliance)
- [Complete Example](#complete-example)

## Overview

Hierarchical state machines enable:
- **Shared behavior**: Common entry/exit logic in parent states
- **Reduced duplication**: Child states inherit parent behavior
- **Event bubbling**: Unhandled events propagate to parent run actions

## Kconfig Setup

```
CONFIG_SMF=y
CONFIG_SMF_ANCESTOR_SUPPORT=y
# Optional: enable auto-transition to child states
CONFIG_SMF_INITIAL_TRANSITION=y
```

## Parent-Child State Structure

```c
enum states { PARENT, CHILD_A, CHILD_B, STANDALONE };

static const struct smf_state app_states[] = {
    // Parent state - no run action (children handle events)
    [PARENT]     = SMF_CREATE_STATE(parent_entry, NULL, parent_exit, NULL, NULL),
    // Children reference parent
    [CHILD_A]    = SMF_CREATE_STATE(NULL, child_a_run, NULL, &app_states[PARENT], NULL),
    [CHILD_B]    = SMF_CREATE_STATE(NULL, child_b_run, NULL, &app_states[PARENT], NULL),
    // State without parent
    [STANDALONE] = SMF_CREATE_STATE(NULL, standalone_run, NULL, NULL, NULL),
};
```

### Multi-Level Nesting

```c
enum states { ROOT, LEVEL1, LEVEL2_A, LEVEL2_B };

static const struct smf_state app_states[] = {
    [ROOT]      = SMF_CREATE_STATE(root_entry, NULL, root_exit, NULL, NULL),
    [LEVEL1]    = SMF_CREATE_STATE(l1_entry, NULL, l1_exit, &app_states[ROOT], NULL),
    [LEVEL2_A]  = SMF_CREATE_STATE(NULL, l2a_run, NULL, &app_states[LEVEL1], NULL),
    [LEVEL2_B]  = SMF_CREATE_STATE(NULL, l2b_run, NULL, &app_states[LEVEL1], NULL),
};
```

## Initial Transitions

With `CONFIG_SMF_INITIAL_TRANSITION=y`, parent states can auto-transition to a child:

```c
// Forward declaration required for self-reference
static const struct smf_state app_states[];

static const struct smf_state app_states[] = {
    // PARENT has initial transition to CHILD_A
    [PARENT]  = SMF_CREATE_STATE(parent_entry, NULL, parent_exit, NULL, &app_states[CHILD_A]),
    [CHILD_A] = SMF_CREATE_STATE(NULL, child_a_run, NULL, &app_states[PARENT], NULL),
    [CHILD_B] = SMF_CREATE_STATE(NULL, child_b_run, NULL, &app_states[PARENT], NULL),
};

// Can now transition to PARENT - will auto-resolve to CHILD_A
smf_set_state(SMF_CTX(&obj), &app_states[PARENT]);
```

**Without initial transitions**: Always transition to leaf states directly.

## Action Execution Order

### Entry Actions

Executed **parent-first** (top-down):

```
Transition to LEVEL2_A:
1. ROOT entry
2. LEVEL1 entry
3. LEVEL2_A entry
```

### Exit Actions

Executed **child-first** (bottom-up):

```
Leaving LEVEL2_A to STANDALONE:
1. LEVEL2_A exit
2. LEVEL1 exit
3. ROOT exit
```

### Run Actions

Executed **child-first**, propagation controlled by return value:

```c
static enum smf_state_result child_run(void *o) {
    if (handled_event) {
        return SMF_EVENT_HANDLED;    // Stop here
    }
    return SMF_EVENT_PROPAGATE;      // Let parent handle
}

static enum smf_state_result parent_run(void *o) {
    // Only called if child returned SMF_EVENT_PROPAGATE
    return SMF_EVENT_HANDLED;
}
```

### Sibling Transitions (LCA Rule)

When transitioning between siblings with shared parent, the **Least Common Ancestor (LCA)** entry/exit actions are NOT executed:

```
Transition from CHILD_A to CHILD_B (both under PARENT):
1. CHILD_A exit
2. CHILD_B entry
// PARENT entry/exit are NOT called
```

## Event Propagation

The run action return value controls propagation:

| Return Value | Behavior |
|--------------|----------|
| `SMF_EVENT_HANDLED` | Stop propagation, don't call parent run |
| `SMF_EVENT_PROPAGATE` | Call parent's run action |

**Note**: Calling `smf_set_state()` in a run action always stops propagation.

### Propagation Example

```c
static enum smf_state_result child_run(void *o) {
    struct s_object *s = (struct s_object *)o;

    if (s->event == EVENT_CHILD_SPECIFIC) {
        // Handle locally
        return SMF_EVENT_HANDLED;
    }
    // Let parent handle unknown events
    return SMF_EVENT_PROPAGATE;
}

static enum smf_state_result parent_run(void *o) {
    struct s_object *s = (struct s_object *)o;

    if (s->event == EVENT_COMMON) {
        // Handle common events for all children
        return SMF_EVENT_HANDLED;
    }
    return SMF_EVENT_PROPAGATE;  // Propagate to grandparent if exists
}
```

## UML Compliance

SMF follows UML hierarchical state machine rules with these exceptions:

1. **Transition actions**: Executed in source state context (before exit), not after exit
2. **External self-transitions**: Only to self, not to sub-states. Transition to child is treated as local
3. **Exit transitions**: Prohibited - `smf_set_state()` in exit action logs error and is ignored

**Supported pseudostates**:
- Initial Pseudostate (via `CONFIG_SMF_INITIAL_TRANSITION`)

**Unsupported pseudostates**:
- Terminate pseudostate (model with `smf_set_terminate()` in entry action)
- Orthogonal regions (model with separate `smf_run_state()` calls)

## Complete Example

Three-level HSM with shared behavior:

```c
#include <zephyr/smf.h>

enum states { ROOT, ACTIVE, IDLE, RUNNING, PAUSED };

struct s_object {
    struct smf_ctx ctx;
    uint32_t event;
    uint32_t counter;
};

static struct s_object obj;
static const struct smf_state states[];

// ROOT: Top-level, handles global events
static void root_entry(void *o) {
    struct s_object *s = (struct s_object *)o;
    s->counter = 0;
}

static enum smf_state_result root_run(void *o) {
    struct s_object *s = (struct s_object *)o;
    if (s->event == EVENT_RESET) {
        s->counter = 0;
        smf_set_state(SMF_CTX(&obj), &states[IDLE]);
    }
    return SMF_EVENT_HANDLED;
}

// ACTIVE: Shared behavior for RUNNING and PAUSED
static void active_entry(void *o) { /* common setup */ }
static void active_exit(void *o) { /* common cleanup */ }

// RUNNING: Leaf state
static enum smf_state_result running_run(void *o) {
    struct s_object *s = (struct s_object *)o;
    if (s->event == EVENT_PAUSE) {
        smf_set_state(SMF_CTX(&obj), &states[PAUSED]);
        return SMF_EVENT_HANDLED;
    }
    return SMF_EVENT_PROPAGATE;  // Let ROOT handle other events
}

// PAUSED: Leaf state
static enum smf_state_result paused_run(void *o) {
    struct s_object *s = (struct s_object *)o;
    if (s->event == EVENT_RESUME) {
        smf_set_state(SMF_CTX(&obj), &states[RUNNING]);
        return SMF_EVENT_HANDLED;
    }
    return SMF_EVENT_PROPAGATE;
}

// IDLE: Leaf state, not under ACTIVE
static enum smf_state_result idle_run(void *o) {
    struct s_object *s = (struct s_object *)o;
    if (s->event == EVENT_START) {
        smf_set_state(SMF_CTX(&obj), &states[RUNNING]);
        return SMF_EVENT_HANDLED;
    }
    return SMF_EVENT_PROPAGATE;
}

static const struct smf_state states[] = {
    [ROOT]    = SMF_CREATE_STATE(root_entry, root_run, NULL, NULL, NULL),
    [ACTIVE]  = SMF_CREATE_STATE(active_entry, NULL, active_exit, &states[ROOT], NULL),
    [IDLE]    = SMF_CREATE_STATE(NULL, idle_run, NULL, &states[ROOT], NULL),
    [RUNNING] = SMF_CREATE_STATE(NULL, running_run, NULL, &states[ACTIVE], NULL),
    [PAUSED]  = SMF_CREATE_STATE(NULL, paused_run, NULL, &states[ACTIVE], NULL),
};

int main(void) {
    smf_set_initial(SMF_CTX(&obj), &states[IDLE]);

    while (1) {
        obj.event = get_next_event();  // Application-specific
        if (smf_run_state(SMF_CTX(&obj))) {
            break;
        }
    }
    return 0;
}
```

**Transition behavior in this example**:

| From | To | Entry/Exit Sequence |
|------|-----|---------------------|
| IDLE | RUNNING | IDLE exit → ACTIVE entry → RUNNING entry |
| RUNNING | PAUSED | RUNNING exit → PAUSED entry (ACTIVE skipped - LCA) |
| PAUSED | IDLE | PAUSED exit → ACTIVE exit → IDLE entry |
