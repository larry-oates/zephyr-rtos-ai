# ISR Work Offloading

## Table of Contents

1. [Why Offload](#why-offload)
2. [Pattern 1: Semaphore Signaling](#pattern-1-semaphore-signaling)
3. [Pattern 2: Work Queue](#pattern-2-work-queue)
4. [Pattern 3: Message Queue](#pattern-3-message-queue)
5. [Pattern 4: FIFO](#pattern-4-fifo)
6. [Comparison](#comparison)

## Why Offload

ISRs should execute quickly for system responsiveness. Time-consuming processing blocks other interrupts and threads.

**Offload when ISR needs to:**
- Process data (parsing, calculations)
- Access slow peripherals
- Make blocking kernel calls
- Perform memory allocation
- Execute long-running algorithms

**ISR-safe operations (no offload needed):**
- Reading/writing hardware registers
- Acknowledging interrupts
- Simple flag updates
- Non-blocking semaphore give
- Work submission

## Pattern 1: Semaphore Signaling

Simplest pattern: ISR signals, dedicated thread processes.

### Use When

- Single event type
- Thread can determine what happened
- Order of events doesn't matter (or only latest matters)

### Implementation

```c
#include <zephyr/kernel.h>
#include <zephyr/irq.h>

K_SEM_DEFINE(data_ready, 0, 1);

volatile uint32_t raw_data;

void my_isr(const void *arg)
{
    /* Quick read from hardware */
    raw_data = *(volatile uint32_t *)0x40001000;

    /* Signal processing thread */
    k_sem_give(&data_ready);
}

void processing_thread(void *p1, void *p2, void *p3)
{
    while (1) {
        /* Block until ISR signals */
        k_sem_take(&data_ready, K_FOREVER);

        /* Safe to do time-consuming work here */
        uint32_t local = raw_data;
        process_data(local);  /* Complex processing */
    }
}

K_THREAD_DEFINE(proc_tid, 1024, processing_thread, NULL, NULL, NULL, 5, 0, 0);

void setup(void)
{
    IRQ_CONNECT(MY_IRQ, 2, my_isr, NULL, 0);
    irq_enable(MY_IRQ);
}
```

### Caveats

- Binary semaphore (limit=1): If ISR fires twice before thread runs, one signal lost
- Use counting semaphore (higher limit) if every event must be processed
- No data passed through semaphore itself

## Pattern 2: Work Queue

Submit work items to the system work queue or custom queue.

### Use When

- Don't want to manage a dedicated thread
- Work can be deferred
- Processing is moderate duration
- Order matters (FIFO processing)

### Implementation: System Work Queue

```c
#include <zephyr/kernel.h>
#include <zephyr/irq.h>

struct sensor_work {
    struct k_work work;
    uint32_t sample;
};

static struct sensor_work sensor_data;

void sensor_work_handler(struct k_work *work)
{
    struct sensor_work *sw = CONTAINER_OF(work, struct sensor_work, work);

    /* Can block here, runs in system workqueue thread */
    process_sensor_sample(sw->sample);
}

void sensor_isr(const void *arg)
{
    /* Quick read */
    sensor_data.sample = read_sensor_hw();

    /* Submit to system workqueue */
    k_work_submit(&sensor_data.work);
}

void setup(void)
{
    k_work_init(&sensor_data.work, sensor_work_handler);

    IRQ_CONNECT(SENSOR_IRQ, 2, sensor_isr, NULL, 0);
    irq_enable(SENSOR_IRQ);
}
```

### Implementation: Delayable Work

For processing that should happen after a delay:

```c
#include <zephyr/kernel.h>

struct debounce_work {
    struct k_work_delayable dwork;
    bool pressed;
};

static struct debounce_work button_data;

void button_handler(struct k_work *work)
{
    struct k_work_delayable *dwork = k_work_delayable_from_work(work);
    struct debounce_work *data = CONTAINER_OF(dwork, struct debounce_work, dwork);

    if (data->pressed) {
        handle_button_press();
    }
}

void button_isr(const void *arg)
{
    button_data.pressed = read_button_state();

    /* Schedule debounced processing in 50ms */
    k_work_reschedule(&button_data.dwork, K_MSEC(50));
}

void setup(void)
{
    k_work_init_delayable(&button_data.dwork, button_handler);

    IRQ_CONNECT(BUTTON_IRQ, 2, button_isr, NULL, 0);
    irq_enable(BUTTON_IRQ);
}
```

### Implementation: Custom Work Queue

For priority control or isolation:

```c
#include <zephyr/kernel.h>

#define WORKQ_STACK_SIZE 1024
#define WORKQ_PRIORITY   5

K_THREAD_STACK_DEFINE(my_stack, WORKQ_STACK_SIZE);
static struct k_work_q my_workq;

static struct k_work my_work;

void work_handler(struct k_work *work)
{
    /* Processing in dedicated thread */
}

void my_isr(const void *arg)
{
    /* Submit to custom queue (not system queue) */
    k_work_submit_to_queue(&my_workq, &my_work);
}

void setup(void)
{
    /* Create custom work queue with high priority */
    k_work_queue_init(&my_workq);
    k_work_queue_start(&my_workq, my_stack, WORKQ_STACK_SIZE,
                       WORKQ_PRIORITY, NULL);

    k_work_init(&my_work, work_handler);

    IRQ_CONNECT(MY_IRQ, 2, my_isr, NULL, 0);
    irq_enable(MY_IRQ);
}
```

## Pattern 3: Message Queue

Pass structured data from ISR to thread.

### Use When

- Need to pass data with each event
- Multiple event types
- Must preserve event order
- Can tolerate message loss if queue full

### Implementation

```c
#include <zephyr/kernel.h>
#include <zephyr/irq.h>

struct sensor_msg {
    uint32_t timestamp;
    uint16_t channel;
    uint16_t value;
};

K_MSGQ_DEFINE(sensor_msgq, sizeof(struct sensor_msg), 10, 4);

void sensor_isr(const void *arg)
{
    struct sensor_msg msg = {
        .timestamp = k_uptime_get_32(),
        .channel = read_channel(),
        .value = read_value()
    };

    /* Non-blocking put - drops message if queue full */
    k_msgq_put(&sensor_msgq, &msg, K_NO_WAIT);
}

void processing_thread(void *p1, void *p2, void *p3)
{
    struct sensor_msg msg;

    while (1) {
        /* Block until message available */
        if (k_msgq_get(&sensor_msgq, &msg, K_FOREVER) == 0) {
            printf("Ch %d: %d @ %u\n",
                   msg.channel, msg.value, msg.timestamp);
            process_measurement(&msg);
        }
    }
}
```

### Handling Queue Full

```c
void sensor_isr(const void *arg)
{
    struct sensor_msg msg = { /* ... */ };

    if (k_msgq_put(&sensor_msgq, &msg, K_NO_WAIT) != 0) {
        /* Queue full - options:
         * 1. Drop message (shown above)
         * 2. Increment overflow counter
         * 3. Purge oldest and retry
         */
        overflow_count++;
    }
}
```

## Pattern 4: FIFO

Linked-list queue for variable-size data or memory-efficient operation.

### Use When

- Need to pass varying amounts of data
- Have pre-allocated buffers
- Want zero-copy transfer

### Implementation

```c
#include <zephyr/kernel.h>
#include <zephyr/irq.h>

struct packet {
    void *fifo_reserved;  /* Required first member */
    uint8_t data[64];
    size_t len;
};

K_FIFO_DEFINE(rx_fifo);

/* Pre-allocated packet pool */
static struct packet packet_pool[4];
K_SEM_DEFINE(packet_sem, 4, 4);

struct packet *packet_alloc(void)
{
    static int idx = 0;
    if (k_sem_take(&packet_sem, K_NO_WAIT) == 0) {
        return &packet_pool[idx++ % 4];
    }
    return NULL;
}

void packet_free(struct packet *pkt)
{
    k_sem_give(&packet_sem);
}

void rx_isr(const void *arg)
{
    struct packet *pkt = packet_alloc();
    if (pkt) {
        pkt->len = read_hw_buffer(pkt->data, sizeof(pkt->data));
        k_fifo_put(&rx_fifo, pkt);
    }
    /* If alloc fails, packet is dropped */
}

void processing_thread(void *p1, void *p2, void *p3)
{
    while (1) {
        struct packet *pkt = k_fifo_get(&rx_fifo, K_FOREVER);

        process_packet(pkt->data, pkt->len);

        packet_free(pkt);
    }
}
```

## Comparison

| Pattern | Data Transfer | Blocking | Ordering | Memory | Best For |
|---------|---------------|----------|----------|--------|----------|
| **Semaphore** | External var | Thread waits | No guarantee | Minimal | Simple signaling |
| **Work Queue** | In work struct | System handles | FIFO | Work struct | Deferred processing |
| **Message Queue** | Copy to queue | Thread waits | FIFO | Fixed-size msgs | Structured events |
| **FIFO** | Pointer/link | Thread waits | FIFO | Pre-allocated | Variable data, zero-copy |

### Quick Selection

```
Need to pass data from ISR?
├── No → Semaphore (simplest)
├── Yes, small fixed-size → Message Queue
├── Yes, large or variable → FIFO with buffer pool
└── Processing can be deferred? → Work Queue
```
