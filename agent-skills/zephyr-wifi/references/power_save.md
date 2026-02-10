# Power Save and Target Wake Time (TWT)

Power management is critical for battery-powered WiFi devices. Zephyr supports legacy power save, WMM power save, and WiFi 6 Target Wake Time (TWT).

## Power Save Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| Legacy PS | 802.11 power save, wakes on DTIM | Simple, broad compatibility |
| WMM PS | WiFi Multimedia power save, per-AC | Better for mixed traffic |
| TWT | WiFi 6 scheduled wake times | Maximum power savings |

## Enable Power Save

### Basic Power Save

```c
#include <zephyr/net/wifi_mgmt.h>

void enable_power_save(struct net_if *iface)
{
    struct wifi_ps_params params = {
        .enabled = WIFI_PS_ENABLED,
        .mode = WIFI_PS_MODE_WMM,  /* or WIFI_PS_MODE_LEGACY */
    };

    int ret = net_mgmt(NET_REQUEST_WIFI_PS, iface, &params, sizeof(params));
    if (ret) {
        printk("Power save enable failed: %d\n", ret);
    }
}

void disable_power_save(struct net_if *iface)
{
    struct wifi_ps_params params = {
        .enabled = WIFI_PS_DISABLED,
    };

    int ret = net_mgmt(NET_REQUEST_WIFI_PS, iface, &params, sizeof(params));
    if (ret) {
        printk("Power save disable failed: %d\n", ret);
    }
}
```

### Power Save Configuration Structure

```c
struct wifi_ps_params {
    enum wifi_ps enabled;           /* WIFI_PS_ENABLED/DISABLED */
    enum wifi_ps_mode mode;         /* LEGACY or WMM */
    int listen_interval;            /* Beacon intervals to sleep */
    enum wifi_ps_wakeup_mode wakeup_mode;
    unsigned short timeout_ms;      /* Inactivity timeout */
    enum wifi_config_ps_exit_strategy exit_strategy;
};
```

### Advanced Power Save Settings

```c
struct wifi_ps_params params = {
    .enabled = WIFI_PS_ENABLED,
    .mode = WIFI_PS_MODE_WMM,
    .listen_interval = 3,        /* Wake every 3 beacons */
    .wakeup_mode = WIFI_PS_WAKEUP_MODE_DTIM,
    .timeout_ms = 100,           /* Enter PS after 100ms idle */
    .exit_strategy = WIFI_PS_EXIT_EVERY_TIM,
};
```

## Get Power Save Status

```c
void get_ps_status(struct net_if *iface)
{
    struct wifi_ps_config config = {0};

    int ret = net_mgmt(NET_REQUEST_WIFI_PS_CONFIG, iface,
                       &config, sizeof(config));
    if (ret) {
        printk("PS config get failed: %d\n", ret);
        return;
    }

    printk("Power Save: %s\n",
           config.ps_params.enabled == WIFI_PS_ENABLED ? "enabled" : "disabled");
    printk("Mode: %s\n",
           config.ps_params.mode == WIFI_PS_MODE_WMM ? "WMM" : "Legacy");
    printk("Listen interval: %d\n", config.ps_params.listen_interval);
}
```

## Target Wake Time (TWT) - WiFi 6

TWT allows the device to negotiate specific wake times with the AP, providing predictable power consumption and reduced contention.

### TWT Requirements
- WiFi 6 (802.11ax) capable hardware
- WiFi 6 AP with TWT support
- `CONFIG_WIFI_MGMT_TWT=y`

### TWT Setup

```c
#include <zephyr/net/wifi_mgmt.h>

static struct net_mgmt_event_callback twt_cb;

static void twt_event_handler(struct net_mgmt_event_callback *cb,
                              uint32_t mgmt_event, struct net_if *iface)
{
    if (mgmt_event == NET_EVENT_WIFI_TWT) {
        const struct wifi_twt_params *twt =
            (const struct wifi_twt_params *)cb->info;

        switch (twt->operation) {
        case WIFI_TWT_SETUP:
            if (twt->resp_status == WIFI_TWT_RESP_RECEIVED) {
                printk("TWT setup complete\n");
                printk("  Wake interval: %llu us\n", twt->setup.twt_wake_interval);
                printk("  Wake duration: %u us\n", twt->setup.twt_interval);
            } else {
                printk("TWT setup failed: %d\n", twt->fail_reason);
            }
            break;
        case WIFI_TWT_TEARDOWN:
            printk("TWT teardown complete\n");
            break;
        }
    }
}

void setup_twt(struct net_if *iface)
{
    /* Register TWT event callback */
    net_mgmt_init_event_callback(&twt_cb, twt_event_handler,
                                 NET_EVENT_WIFI_TWT);
    net_mgmt_add_event_callback(&twt_cb);

    struct wifi_twt_params params = {
        .operation = WIFI_TWT_SETUP,
        .negotiation_type = WIFI_TWT_INDIVIDUAL,
        .setup_cmd = WIFI_TWT_SETUP_CMD_REQUEST,
        .dialog_token = 1,
        .flow_id = 0,
        .setup = {
            .responder = 0,             /* AP is responder */
            .trigger = 1,               /* Trigger-enabled */
            .implicit = 1,              /* Implicit TWT */
            .announce = 0,              /* Unannounced */
            .twt_wake_interval = 65000, /* Wake interval in us */
            .twt_interval = 1,          /* Min wake duration */
        },
    };

    int ret = net_mgmt(NET_REQUEST_WIFI_TWT, iface, &params, sizeof(params));
    if (ret) {
        printk("TWT setup request failed: %d\n", ret);
    }
}
```

### TWT Teardown

```c
void teardown_twt(struct net_if *iface, uint8_t flow_id)
{
    struct wifi_twt_params params = {
        .operation = WIFI_TWT_TEARDOWN,
        .flow_id = flow_id,
        .teardown = {
            .teardown_all = 0,  /* Only this flow */
        },
    };

    int ret = net_mgmt(NET_REQUEST_WIFI_TWT, iface, &params, sizeof(params));
    if (ret) {
        printk("TWT teardown failed: %d\n", ret);
    }
}

/* Teardown all TWT flows */
void teardown_all_twt(struct net_if *iface)
{
    struct wifi_twt_params params = {
        .operation = WIFI_TWT_TEARDOWN,
        .teardown = {
            .teardown_all = 1,
        },
    };

    net_mgmt(NET_REQUEST_WIFI_TWT, iface, &params, sizeof(params));
}
```

### TWT Parameters Structure

```c
struct wifi_twt_params {
    enum wifi_twt_operation operation;      /* SETUP/TEARDOWN */
    enum wifi_twt_negotiation_type negotiation_type;
    enum wifi_twt_setup_cmd setup_cmd;      /* REQUEST/SUGGEST/DEMAND */
    uint8_t dialog_token;
    uint8_t flow_id;                        /* 0-7 */
    enum wifi_twt_setup_resp_status resp_status;
    enum wifi_twt_fail_reason fail_reason;

    union {
        struct {
            uint64_t twt_wake_interval;     /* Wake interval in us */
            uint32_t twt_interval;          /* Service period in us */
            bool responder;
            bool trigger;
            bool implicit;
            bool announce;
            bool wake_ahead;
        } setup;

        struct {
            bool teardown_all;
        } teardown;
    };
};
```

## TWT Types

| Type | Description |
|------|-------------|
| Individual | Negotiated between single STA and AP |
| Broadcast | AP broadcasts TWT schedule to all STAs |
| Implicit | Intervals repeat automatically |
| Explicit | Each interval explicitly signaled |
| Triggered | AP triggers transmission |
| Untriggered | STA can transmit anytime during SP |

## Power Save Kconfig

```
# Basic power save
CONFIG_WIFI_MGMT_PS=y

# TWT support (WiFi 6)
CONFIG_WIFI_MGMT_TWT=y

# TWT IP address check before setup
CONFIG_WIFI_MGMT_TWT_CHECK_IP=y
```

## Power Consumption Guidelines

### Maximum Power Save
1. Enable TWT with long wake intervals
2. Use implicit TWT for periodic data
3. Minimize beacon listen interval
4. Use triggered mode if AP supports it

### Balanced Performance
1. Enable WMM power save
2. Use moderate listen interval (3-5)
3. Consider latency requirements

### Low Latency
1. Disable power save or use short timeout
2. Use DTIM wakeup mode
3. Avoid TWT for real-time traffic

## Common Issues

### Power Save Not Working
- Verify AP supports power save features
- Check if traffic pattern prevents sleep
- Ensure connected state before enabling PS

### TWT Setup Rejected
- AP may not support TWT
- Requested parameters may be out of range
- Try different wake interval/duration

### High Latency with Power Save
- Reduce listen interval
- Use triggered TWT
- Consider disabling PS for latency-critical apps
