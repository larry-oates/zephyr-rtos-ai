# ZBus (Zephyr Bus)

ZBus is a lightweight publish-subscribe inter-process communication framework for Zephyr.

## Concepts

-   **Channel**: Named message buffer with a defined message type. The central entity for communication.
-   **Publisher**: Any context (thread, ISR, work queue) that sends messages to a channel.
-   **Subscriber**: Observer that receives notifications when a channel is updated.
-   **Listener**: Callback-based subscriber (runs in publisher's context).
-   **Message Subscriber**: Thread-based subscriber with its own message queue.
-   **Observation**: The act of a subscriber watching a channel.

## When to Use ZBus

-   **Decoupled communication**: Publishers and subscribers don't need to know each other.
-   **One-to-many**: Single publisher, multiple subscribers.
-   **Many-to-one**: Multiple publishers, single subscriber.
-   **Event-driven architecture**: React to state changes across the system.
-   **Sensor data distribution**: Broadcast sensor readings to multiple consumers.

## Kconfig

```kconfig
CONFIG_ZBUS=y                    # Enable ZBus
CONFIG_ZBUS_CHANNEL_NAME=y       # Store channel names (for debugging)
CONFIG_ZBUS_RUNTIME_OBSERVERS=y  # Allow dynamic observer registration
```

## Implementation

### Defining a Channel

```c
#include <zephyr/zbus/zbus.h>

struct sensor_data {
    int temperature;
    int humidity;
};

/* Define a channel with initial value */
ZBUS_CHAN_DEFINE(sensor_chan,           /* Channel name */
                 struct sensor_data,     /* Message type */
                 NULL,                   /* Optional validator */
                 NULL,                   /* Optional user data */
                 ZBUS_OBSERVERS_EMPTY,   /* Static observers (or list) */
                 ZBUS_MSG_INIT(.temperature = 0, .humidity = 0)  /* Initial value */
);
```

### Publishing

```c
struct sensor_data data = {.temperature = 25, .humidity = 60};

/* Publish with timeout */
int ret = zbus_chan_pub(&sensor_chan, &data, K_MSEC(100));
if (ret != 0) {
    /* Handle publish failure (channel busy, timeout) */
}
```

### Subscribing (Listener - Callback)

Listeners execute in the publisher's context. Keep them short.

```c
void sensor_listener_cb(const struct zbus_channel *chan)
{
    struct sensor_data data;
    zbus_chan_read(chan, &data, K_NO_WAIT);
    printk("Temp: %d, Humidity: %d\n", data.temperature, data.humidity);
}

ZBUS_LISTENER_DEFINE(my_listener, sensor_listener_cb);

/* Static observation (at compile time) */
ZBUS_CHAN_DEFINE(sensor_chan, ...,
                 ZBUS_OBSERVERS(my_listener),  /* Add listener here */
                 ...);

/* OR runtime observation */
zbus_chan_add_obs(&sensor_chan, &my_listener, K_FOREVER);
```

### Subscribing (Message Subscriber - Thread)

Message subscribers have their own FIFO and process messages in their own thread context.

```c
ZBUS_MSG_SUBSCRIBER_DEFINE(my_msg_sub);

/* Add to channel observers */
ZBUS_CHAN_ADD_OBS(sensor_chan, my_msg_sub, 3);  /* priority 3 */

void subscriber_thread(void)
{
    const struct zbus_channel *chan;
    struct sensor_data data;

    while (1) {
        /* Wait for any observed channel to be published */
        if (zbus_sub_wait(&my_msg_sub, &chan, K_FOREVER) == 0) {
            zbus_chan_read(chan, &data, K_NO_WAIT);
            /* Process data */
        }
    }
}
```

### Reading Channel (Without Subscribing)

```c
struct sensor_data data;
zbus_chan_read(&sensor_chan, &data, K_MSEC(100));
```

## Key APIs

| Function | Description |
| :--- | :--- |
| `ZBUS_CHAN_DEFINE` | Define a channel at compile time |
| `zbus_chan_pub` | Publish a message to a channel |
| `zbus_chan_read` | Read current channel value |
| `zbus_chan_claim` / `zbus_chan_finish` | Claim exclusive access for read-modify-write |
| `ZBUS_LISTENER_DEFINE` | Define a callback-based observer |
| `ZBUS_MSG_SUBSCRIBER_DEFINE` | Define a thread-based observer |
| `zbus_sub_wait` | Wait for a message (for msg subscribers) |
| `zbus_chan_add_obs` / `zbus_chan_rm_obs` | Runtime observer management |

## Comparison with Traditional Objects

| Aspect | ZBus | Message Queue |
| :--- | :--- | :--- |
| **Pattern** | Pub/Sub (1:N, N:1, N:M) | Point-to-point (1:1) |
| **Coupling** | Loose (via channel name) | Tight (direct queue reference) |
| **Delivery** | Latest value (can miss updates) | Queued (all messages buffered) |
| **ISR Safe** | Yes (publish) | Yes (with K_NO_WAIT) |
| **Overhead** | Higher (observer management) | Lower |

## Best Practices

1.  **Keep listeners short**: They run in publisher context.
2.  **Use message subscribers for heavy processing**: They have their own thread.
3.  **Validate messages**: Use the validator callback to reject invalid data.
4.  **Use `zbus_chan_claim`/`finish`**: For atomic read-modify-write operations.
5.  **Consider memory**: Each channel stores one message; message subscribers add FIFO overhead.
