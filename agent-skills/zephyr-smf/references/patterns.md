# SMF Common Patterns

## Table of Contents

- [Event-Driven Pattern](#event-driven-pattern)
- [Polling Pattern](#polling-pattern)
- [Timeout Pattern](#timeout-pattern)
- [Error Handling Pattern](#error-handling-pattern)
- [Multiple State Machines](#multiple-state-machines)
- [State Machine Termination](#state-machine-termination)

## Event-Driven Pattern

Use Zephyr `k_event` for event-driven state machines:

```c
#include <zephyr/kernel.h>
#include <zephyr/smf.h>

#define EVENT_BUTTON    BIT(0)
#define EVENT_TIMEOUT   BIT(1)
#define EVENT_DATA      BIT(2)

struct s_object {
    struct smf_ctx ctx;
    struct k_event smf_event;
    uint32_t events;
    /* application data */
};

static struct s_object obj;

// ISR or other context posts events
void button_isr(void) {
    k_event_post(&obj.smf_event, EVENT_BUTTON);
}

// Run action checks events
static enum smf_state_result state_run(void *o) {
    struct s_object *s = (struct s_object *)o;

    if (s->events & EVENT_BUTTON) {
        smf_set_state(SMF_CTX(&obj), &states[NEXT_STATE]);
    }
    return SMF_EVENT_HANDLED;
}

// Main loop waits for events
int main(void) {
    k_event_init(&obj.smf_event);
    smf_set_initial(SMF_CTX(&obj), &states[INITIAL]);

    while (1) {
        // Block until event occurs
        obj.events = k_event_wait(&obj.smf_event,
            EVENT_BUTTON | EVENT_TIMEOUT | EVENT_DATA,
            true,       // Clear events after wait
            K_FOREVER);

        if (smf_run_state(SMF_CTX(&obj))) {
            break;
        }
    }
    return 0;
}
```

## Polling Pattern

Simple periodic state machine execution:

```c
int main(void) {
    smf_set_initial(SMF_CTX(&obj), &states[INITIAL]);

    while (1) {
        if (smf_run_state(SMF_CTX(&obj))) {
            break;
        }
        k_msleep(100);  // Poll interval
    }
    return 0;
}
```

## Timeout Pattern

State-specific timeouts using `k_timer`:

```c
struct s_object {
    struct smf_ctx ctx;
    struct k_timer timeout;
    bool timeout_expired;
};

static void timeout_handler(struct k_timer *timer) {
    struct s_object *s = CONTAINER_OF(timer, struct s_object, timeout);
    s->timeout_expired = true;
}

static void waiting_entry(void *o) {
    struct s_object *s = (struct s_object *)o;
    s->timeout_expired = false;
    k_timer_start(&s->timeout, K_SECONDS(5), K_NO_WAIT);
}

static enum smf_state_result waiting_run(void *o) {
    struct s_object *s = (struct s_object *)o;

    if (s->timeout_expired) {
        smf_set_state(SMF_CTX(s), &states[TIMEOUT_STATE]);
    }
    return SMF_EVENT_HANDLED;
}

static void waiting_exit(void *o) {
    struct s_object *s = (struct s_object *)o;
    k_timer_stop(&s->timeout);  // Cancel if transitioning early
}

int main(void) {
    k_timer_init(&obj.timeout, timeout_handler, NULL);
    // ...
}
```

## Error Handling Pattern

Centralized error handling with termination:

```c
enum states { INIT, RUNNING, ERROR };

struct s_object {
    struct smf_ctx ctx;
    int error_code;
};

static enum smf_state_result running_run(void *o) {
    struct s_object *s = (struct s_object *)o;
    int ret = do_operation();

    if (ret < 0) {
        s->error_code = ret;
        smf_set_state(SMF_CTX(s), &states[ERROR]);
    }
    return SMF_EVENT_HANDLED;
}

static void error_entry(void *o) {
    struct s_object *s = (struct s_object *)o;
    LOG_ERR("State machine error: %d", s->error_code);

    // Terminate with error code
    smf_set_terminate(SMF_CTX(s), s->error_code);
}

static const struct smf_state states[] = {
    [INIT]    = SMF_CREATE_STATE(init_entry, init_run, NULL, NULL, NULL),
    [RUNNING] = SMF_CREATE_STATE(NULL, running_run, NULL, NULL, NULL),
    [ERROR]   = SMF_CREATE_STATE(error_entry, NULL, NULL, NULL, NULL),
};

int main(void) {
    smf_set_initial(SMF_CTX(&obj), &states[INIT]);

    while (1) {
        int32_t ret = smf_run_state(SMF_CTX(&obj));
        if (ret) {
            LOG_ERR("State machine terminated with: %d", ret);
            // Handle cleanup
            break;
        }
        k_msleep(100);
    }
    return 0;
}
```

## Multiple State Machines

Run independent state machines in parallel:

```c
// Separate state machines
static struct sm_input input_obj;
static struct sm_output output_obj;

static const struct smf_state input_states[] = { /* ... */ };
static const struct smf_state output_states[] = { /* ... */ };

int main(void) {
    smf_set_initial(SMF_CTX(&input_obj), &input_states[0]);
    smf_set_initial(SMF_CTX(&output_obj), &output_states[0]);

    while (1) {
        int32_t ret1 = smf_run_state(SMF_CTX(&input_obj));
        int32_t ret2 = smf_run_state(SMF_CTX(&output_obj));

        if (ret1 || ret2) {
            break;
        }
        k_msleep(10);
    }
    return 0;
}
```

### Orthogonal Regions (UML)

Model UML orthogonal regions as separate state machines sharing a context:

```c
struct shared_context {
    struct smf_ctx region1_ctx;
    struct smf_ctx region2_ctx;
    uint32_t shared_data;
};

// Run both regions
smf_run_state(SMF_CTX(&ctx.region1_ctx));
smf_run_state(SMF_CTX(&ctx.region2_ctx));
```

## State Machine Termination

### Clean Termination

```c
static enum smf_state_result shutdown_run(void *o) {
    // Cleanup complete
    smf_set_terminate(SMF_CTX(o), 0);  // Success
    return SMF_EVENT_HANDLED;
}
```

### Error Termination

```c
static enum smf_state_result error_run(void *o) {
    smf_set_terminate(SMF_CTX(o), -EFAULT);  // Error code
    return SMF_EVENT_HANDLED;
}
```

### Checking Termination

```c
while (1) {
    int32_t ret = smf_run_state(SMF_CTX(&obj));
    if (ret) {
        if (ret > 0) {
            LOG_INF("Clean shutdown");
        } else {
            LOG_ERR("Error: %d", ret);
        }
        break;
    }
}
```

## Thread-Based Pattern

Run state machine in dedicated thread:

```c
#define SM_STACK_SIZE 1024
#define SM_PRIORITY 5

K_THREAD_STACK_DEFINE(sm_stack, SM_STACK_SIZE);
static struct k_thread sm_thread;

static void sm_thread_entry(void *p1, void *p2, void *p3) {
    struct s_object *obj = (struct s_object *)p1;

    smf_set_initial(SMF_CTX(obj), &states[INITIAL]);

    while (1) {
        if (smf_run_state(SMF_CTX(obj))) {
            break;
        }
        k_msleep(10);
    }
}

void start_state_machine(void) {
    k_thread_create(&sm_thread, sm_stack, SM_STACK_SIZE,
        sm_thread_entry, &obj, NULL, NULL,
        SM_PRIORITY, 0, K_NO_WAIT);
}
```
