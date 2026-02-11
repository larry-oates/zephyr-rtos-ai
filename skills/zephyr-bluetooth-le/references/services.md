# Built-in GATT Services

Zephyr provides ready-to-use implementations of common Bluetooth SIG services.

## Table of Contents

- [Battery Service (BAS)](#battery-service-bas)
- [Device Information Service (DIS)](#device-information-service-dis)
- [Heart Rate Service (HRS)](#heart-rate-service-hrs)
- [Nordic UART Service (NUS)](#nordic-uart-service-nus)
- [Object Transfer Service (OTS)](#object-transfer-service-ots)
- [Immediate Alert Service (IAS)](#immediate-alert-service-ias)

## Battery Service (BAS)

Exposes battery level as a percentage (0-100).

### Kconfig

```
CONFIG_BT_BAS=y
```

### API

```c
#include <zephyr/bluetooth/services/bas.h>

/* Get current battery level */
uint8_t level = bt_bas_get_battery_level();

/* Set battery level (triggers notification if enabled) */
int err = bt_bas_set_battery_level(75);
```

### Sample Usage

```c
/* Periodically update battery level */
void update_battery(void)
{
    uint8_t level = read_battery_percentage();  /* Your ADC/fuel gauge code */
    bt_bas_set_battery_level(level);
}
```

### Advertising

```c
BT_DATA_BYTES(BT_DATA_UUID16_ALL, BT_UUID_16_ENCODE(BT_UUID_BAS_VAL)),
```

## Device Information Service (DIS)

Exposes device manufacturer, model, serial number, and other info.

### Kconfig

```
CONFIG_BT_DIS=y
CONFIG_BT_DIS_MANUF="My Company"
CONFIG_BT_DIS_MODEL="My Product"
CONFIG_BT_DIS_SERIAL_NUMBER=y
CONFIG_BT_DIS_FW_REV=y
CONFIG_BT_DIS_HW_REV=y
CONFIG_BT_DIS_SW_REV=y

# Optional PnP ID
CONFIG_BT_DIS_PNP=y
CONFIG_BT_DIS_PNP_VID_SRC=1       # 1=Bluetooth SIG, 2=USB
CONFIG_BT_DIS_PNP_VID=0x05F1      # Vendor ID
CONFIG_BT_DIS_PNP_PID=0x0001      # Product ID
CONFIG_BT_DIS_PNP_VER=0x0001      # Product version
```

### Dynamic Strings

For runtime-configurable values:

```
CONFIG_BT_DIS_SERIAL_NUMBER_STR=""
CONFIG_BT_DIS_FW_REV_STR=""
CONFIG_BT_DIS_HW_REV_STR=""
CONFIG_BT_DIS_SW_REV_STR=""
```

Then set via settings subsystem or implement `bt_dis_str_t` callbacks.

### Advertising

```c
BT_DATA_BYTES(BT_DATA_UUID16_ALL, BT_UUID_16_ENCODE(BT_UUID_DIS_VAL)),
```

## Heart Rate Service (HRS)

Exposes heart rate measurements with optional body sensor location.

### Kconfig

```
CONFIG_BT_HRS=y
CONFIG_BT_HRS_DEFAULT_PERM_RW=y  # Read/write permissions
```

### API

```c
#include <zephyr/bluetooth/services/hrs.h>

/* Send heart rate notification */
int err = bt_hrs_notify(heartrate_bpm);

/* Register callback for notification state changes */
static void hrs_ntf_changed(bool enabled)
{
    printk("HRS notifications %s\n", enabled ? "enabled" : "disabled");
}

static struct bt_hrs_cb hrs_cb = {
    .ntf_changed = hrs_ntf_changed,
};

bt_hrs_cb_register(&hrs_cb);
```

### Sample Usage

```c
/* Periodically send heart rate */
void update_heart_rate(void)
{
    uint8_t bpm = read_heart_rate_sensor();
    bt_hrs_notify(bpm);
}
```

### Advertising

```c
BT_DATA_BYTES(BT_DATA_UUID16_ALL, BT_UUID_16_ENCODE(BT_UUID_HRS_VAL)),
```

## Nordic UART Service (NUS)

Provides UART-like data transfer over BLE. Not a Bluetooth SIG service, but widely used.

### Kconfig

```
CONFIG_BT_NUS=y
```

### API

```c
#include <zephyr/bluetooth/services/nus.h>

/* Receive callback */
static void nus_received(struct bt_conn *conn, const uint8_t *data, uint16_t len)
{
    printk("Received %d bytes\n", len);
}

/* Send enabled callback */
static void nus_sent(struct bt_conn *conn)
{
    printk("Data sent\n");
}

static struct bt_nus_cb nus_cb = {
    .received = nus_received,
    .sent = nus_sent,
};

/* Initialize */
err = bt_nus_init(&nus_cb);

/* Send data */
err = bt_nus_send(conn, data, len);
```

### Custom UUIDs (Nordic UART)

```
Service:     6E400001-B5A3-F393-E0A9-E50E24DCCA9E
TX Char:     6E400003-B5A3-F393-E0A9-E50E24DCCA9E (notify)
RX Char:     6E400002-B5A3-F393-E0A9-E50E24DCCA9E (write)
```

## Object Transfer Service (OTS)

Enables transfer of arbitrary data objects (files, images, etc.).

### Kconfig

```
CONFIG_BT_OTS=y
CONFIG_BT_OTS_MAX_OBJ_CNT=10
```

### Complex API

OTS has a complex API for managing objects. Key structures:

- `struct bt_ots` - OTS instance
- `struct bt_ots_obj` - Object metadata
- `struct bt_ots_cb` - Callbacks for object operations

See `samples/bluetooth/peripheral_ots` for complete example.

### Advertising

```c
BT_DATA_BYTES(BT_DATA_UUID16_ALL, BT_UUID_16_ENCODE(BT_UUID_OTS_VAL)),
```

## Immediate Alert Service (IAS)

Simple alerting service (e.g., for "Find Me" functionality).

### Kconfig

```
CONFIG_BT_IAS=y
CONFIG_BT_IAS_CLIENT=y  /* For central role */
```

### Server API

```c
#include <zephyr/bluetooth/services/ias.h>

static void alert_stop(void)
{
    /* Stop alerting */
}

static void alert_start(void)
{
    /* Start alerting */
}

static void alert_high(void)
{
    /* High alert */
}

BT_IAS_CB_DEFINE(ias_callbacks) = {
    .no_alert = alert_stop,
    .mild_alert = alert_start,
    .high_alert = alert_high,
};
```

### Client API

```c
/* Set alert level on remote device */
err = bt_ias_client_alert_write(conn, BT_IAS_ALERT_LVL_HIGH_ALERT);
```

## Current Time Service (CTS)

Exposes current date/time.

### Kconfig

```
CONFIG_BT_CTS=y
```

### API

```c
#include <zephyr/bluetooth/services/cts.h>

/* Server: Set current time */
struct bt_cts_current_time ct = {
    .exact_time_256.year = 2024,
    .exact_time_256.month = 12,
    .exact_time_256.day = 25,
    /* ... */
};
bt_cts_set_current_time(&ct);
```

## TX Power Service (TPS)

Exposes transmit power level.

### Kconfig

```
CONFIG_BT_TPS=y
```

Service is automatically available; no additional API needed.

## Service Summary

| Service | UUID | Kconfig | Primary Use |
|---------|------|---------|-------------|
| BAS | 0x180F | `CONFIG_BT_BAS=y` | Battery level |
| DIS | 0x180A | `CONFIG_BT_DIS=y` | Device info |
| HRS | 0x180D | `CONFIG_BT_HRS=y` | Heart rate |
| NUS | Custom | `CONFIG_BT_NUS=y` | UART over BLE |
| OTS | 0x1825 | `CONFIG_BT_OTS=y` | File transfer |
| IAS | 0x1802 | `CONFIG_BT_IAS=y` | Find me alerts |
| CTS | 0x1805 | `CONFIG_BT_CTS=y` | Current time |
| TPS | 0x1804 | `CONFIG_BT_TPS=y` | TX power |
