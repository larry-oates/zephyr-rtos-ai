# GAP (Generic Access Profile)

GAP defines device discovery, connection establishment, and security procedures.

## Table of Contents

- [Advertising](#advertising)
- [Scanning](#scanning)
- [Connections](#connections)
- [Extended Advertising](#extended-advertising)
- [Connection Parameters](#connection-parameters)

## Advertising

### Legacy Advertising

```c
#include <zephyr/bluetooth/bluetooth.h>

/* Advertising data (max 31 bytes) */
static const struct bt_data ad[] = {
    BT_DATA_BYTES(BT_DATA_FLAGS, (BT_LE_AD_GENERAL | BT_LE_AD_NO_BREDR)),
    BT_DATA_BYTES(BT_DATA_UUID16_ALL,
                  BT_UUID_16_ENCODE(BT_UUID_HRS_VAL),
                  BT_UUID_16_ENCODE(BT_UUID_BAS_VAL)),
};

/* Scan response data (max 31 bytes) */
static const struct bt_data sd[] = {
    BT_DATA(BT_DATA_NAME_COMPLETE, CONFIG_BT_DEVICE_NAME,
            sizeof(CONFIG_BT_DEVICE_NAME) - 1),
};

/* Start connectable advertising */
err = bt_le_adv_start(BT_LE_ADV_CONN, ad, ARRAY_SIZE(ad), sd, ARRAY_SIZE(sd));
```

### Advertising Parameters

| Macro | Description |
|-------|-------------|
| `BT_LE_ADV_CONN` | Connectable, scannable |
| `BT_LE_ADV_CONN_FAST_1` | Fast connectable (30-60ms interval) |
| `BT_LE_ADV_CONN_FAST_2` | Fast connectable (100-150ms interval) |
| `BT_LE_ADV_NCONN` | Non-connectable, non-scannable |
| `BT_LE_ADV_NCONN_NAME` | Non-connectable with name in ad data |

### Advertising Data Types

| Macro | Description |
|-------|-------------|
| `BT_DATA_FLAGS` | Advertising flags |
| `BT_DATA_UUID16_ALL` | Complete list of 16-bit UUIDs |
| `BT_DATA_UUID16_SOME` | Incomplete list of 16-bit UUIDs |
| `BT_DATA_UUID128_ALL` | Complete list of 128-bit UUIDs |
| `BT_DATA_NAME_COMPLETE` | Complete local name |
| `BT_DATA_NAME_SHORTENED` | Shortened local name |
| `BT_DATA_MANUFACTURER_DATA` | Manufacturer-specific data |
| `BT_DATA_SVC_DATA16` | Service data with 16-bit UUID |

### Custom Advertising Parameters

```c
struct bt_le_adv_param param = {
    .id = BT_ID_DEFAULT,
    .options = BT_LE_ADV_OPT_CONNECTABLE | BT_LE_ADV_OPT_USE_NAME,
    .interval_min = BT_GAP_ADV_FAST_INT_MIN_1,  /* 30ms */
    .interval_max = BT_GAP_ADV_FAST_INT_MAX_1,  /* 60ms */
};

err = bt_le_adv_start(&param, ad, ARRAY_SIZE(ad), sd, ARRAY_SIZE(sd));
```

### Stopping Advertising

```c
err = bt_le_adv_stop();
```

## Scanning

### Basic Scanning

```c
static void scan_cb(const bt_addr_le_t *addr, int8_t rssi,
                    uint8_t adv_type, struct net_buf_simple *buf)
{
    char addr_str[BT_ADDR_LE_STR_LEN];
    bt_addr_le_to_str(addr, addr_str, sizeof(addr_str));
    printk("Device: %s, RSSI: %d\n", addr_str, rssi);

    /* Parse advertising data */
    while (buf->len > 1) {
        uint8_t len = net_buf_simple_pull_u8(buf);
        uint8_t type;

        if (len == 0 || len > buf->len) {
            break;
        }

        type = net_buf_simple_pull_u8(buf);
        /* Handle type... */
        net_buf_simple_pull(buf, len - 1);
    }
}

/* Start active scanning */
err = bt_le_scan_start(BT_LE_SCAN_ACTIVE, scan_cb);

/* Stop scanning */
err = bt_le_scan_stop();
```

### Scan Parameters

| Macro | Description |
|-------|-------------|
| `BT_LE_SCAN_ACTIVE` | Active scanning (requests scan responses) |
| `BT_LE_SCAN_PASSIVE` | Passive scanning |
| `BT_LE_SCAN_CODED` | Scan on LE Coded PHY |

### Custom Scan Parameters

```c
struct bt_le_scan_param scan_param = {
    .type = BT_LE_SCAN_TYPE_ACTIVE,
    .options = BT_LE_SCAN_OPT_FILTER_DUPLICATE,
    .interval = BT_GAP_SCAN_FAST_INTERVAL,  /* 60ms */
    .window = BT_GAP_SCAN_FAST_WINDOW,      /* 30ms */
};

err = bt_le_scan_start(&scan_param, scan_cb);
```

## Connections

### Creating Connection (Central)

```c
static struct bt_conn *default_conn;

static void connected(struct bt_conn *conn, uint8_t err)
{
    if (err) {
        printk("Failed to connect (err %u)\n", err);
        bt_conn_unref(default_conn);
        default_conn = NULL;
        return;
    }
    printk("Connected\n");
}

static void disconnected(struct bt_conn *conn, uint8_t reason)
{
    printk("Disconnected (reason %u)\n", reason);
    bt_conn_unref(default_conn);
    default_conn = NULL;
}

BT_CONN_CB_DEFINE(conn_callbacks) = {
    .connected = connected,
    .disconnected = disconnected,
};

/* From scan callback, connect to device */
bt_le_scan_stop();
err = bt_conn_le_create(addr, BT_CONN_LE_CREATE_CONN,
                        BT_LE_CONN_PARAM_DEFAULT, &default_conn);
```

### Connection Parameters

| Macro | Description |
|-------|-------------|
| `BT_LE_CONN_PARAM_DEFAULT` | Default parameters (30-50ms interval) |

### Custom Connection Parameters

```c
struct bt_le_conn_param conn_param = {
    .interval_min = 24,  /* 30ms (N * 1.25ms) */
    .interval_max = 40,  /* 50ms */
    .latency = 0,
    .timeout = 400,      /* 4s (N * 10ms) */
};

err = bt_conn_le_create(addr, BT_CONN_LE_CREATE_CONN, &conn_param, &conn);
```

### Updating Connection Parameters

```c
err = bt_conn_le_param_update(conn, BT_LE_CONN_PARAM_DEFAULT);
```

### Disconnecting

```c
err = bt_conn_disconnect(conn, BT_HCI_ERR_REMOTE_USER_TERM_CONN);
```

## Extended Advertising

Requires: `CONFIG_BT_EXT_ADV=y`

```c
static struct bt_le_ext_adv *adv;

struct bt_le_adv_param adv_param = {
    .id = BT_ID_DEFAULT,
    .sid = 0,
    .secondary_max_skip = 0,
    .options = BT_LE_ADV_OPT_EXT_ADV | BT_LE_ADV_OPT_CONN,
    .interval_min = BT_GAP_ADV_FAST_INT_MIN_2,
    .interval_max = BT_GAP_ADV_FAST_INT_MAX_2,
    .peer = NULL,
};

/* Create extended advertising set */
err = bt_le_ext_adv_create(&adv_param, NULL, &adv);

/* Set advertising data */
err = bt_le_ext_adv_set_data(adv, ad, ARRAY_SIZE(ad), NULL, 0);

/* Start extended advertising */
err = bt_le_ext_adv_start(adv, BT_LE_EXT_ADV_START_DEFAULT);

/* Stop and delete */
err = bt_le_ext_adv_stop(adv);
err = bt_le_ext_adv_delete(adv);
```

### Extended Advertising Options

| Option | Description |
|--------|-------------|
| `BT_LE_ADV_OPT_EXT_ADV` | Use extended advertising PDUs |
| `BT_LE_ADV_OPT_CODED` | Use LE Coded PHY |
| `BT_LE_ADV_OPT_NO_2M` | Disable 2M PHY for secondary |
| `BT_LE_ADV_OPT_ANONYMOUS` | Anonymous advertising |

## Connection Parameters

### GAP Timing Constants

| Define | Value | Description |
|--------|-------|-------------|
| `BT_GAP_ADV_FAST_INT_MIN_1` | 30ms | Fast advertising min |
| `BT_GAP_ADV_FAST_INT_MAX_1` | 60ms | Fast advertising max |
| `BT_GAP_ADV_SLOW_INT_MIN` | 1s | Slow advertising min |
| `BT_GAP_SCAN_FAST_INTERVAL` | 60ms | Fast scan interval |
| `BT_GAP_SCAN_FAST_WINDOW` | 30ms | Fast scan window |
| `BT_GAP_INIT_CONN_INT_MIN` | 30ms | Initial connection interval min |
| `BT_GAP_INIT_CONN_INT_MAX` | 50ms | Initial connection interval max |

### Address Types

```c
/* Get local identity address */
size_t count = 1;
bt_id_get(addrs, &count);

/* Address types */
BT_ADDR_LE_PUBLIC   /* Public device address */
BT_ADDR_LE_RANDOM   /* Random device address */
```

### PHY Options

```c
/* LE PHY types */
BT_GAP_LE_PHY_1M     /* 1 Mbps */
BT_GAP_LE_PHY_2M     /* 2 Mbps */
BT_GAP_LE_PHY_CODED  /* Coded PHY (long range) */
```
