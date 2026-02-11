# GATT (Generic Attribute Profile)

GATT defines the data structure and procedures for exchanging data over BLE connections.

## Table of Contents

- [GATT Server (Peripheral)](#gatt-server-peripheral)
- [GATT Client (Central)](#gatt-client-central)
- [Custom Services](#custom-services)
- [Notifications and Indications](#notifications-and-indications)
- [Attribute Permissions](#attribute-permissions)

## GATT Server (Peripheral)

### Defining a Service

```c
#include <zephyr/bluetooth/gatt.h>
#include <zephyr/bluetooth/uuid.h>

/* Custom 128-bit UUID */
#define BT_UUID_MY_SERVICE_VAL \
    BT_UUID_128_ENCODE(0x12345678, 0x1234, 0x5678, 0x1234, 0x56789abcdef0)

#define BT_UUID_MY_SERVICE BT_UUID_DECLARE_128(BT_UUID_MY_SERVICE_VAL)
#define BT_UUID_MY_CHAR    BT_UUID_DECLARE_128(BT_UUID_128_ENCODE( \
    0x12345678, 0x1234, 0x5678, 0x1234, 0x56789abcdef1))

static uint8_t my_value[20];

/* Read callback */
static ssize_t read_my_char(struct bt_conn *conn,
                            const struct bt_gatt_attr *attr,
                            void *buf, uint16_t len, uint16_t offset)
{
    return bt_gatt_attr_read(conn, attr, buf, len, offset,
                             my_value, sizeof(my_value));
}

/* Write callback */
static ssize_t write_my_char(struct bt_conn *conn,
                             const struct bt_gatt_attr *attr,
                             const void *buf, uint16_t len,
                             uint16_t offset, uint8_t flags)
{
    if (offset + len > sizeof(my_value)) {
        return BT_GATT_ERR(BT_ATT_ERR_INVALID_OFFSET);
    }

    memcpy(my_value + offset, buf, len);
    return len;
}

/* Service definition */
BT_GATT_SERVICE_DEFINE(my_svc,
    BT_GATT_PRIMARY_SERVICE(BT_UUID_MY_SERVICE),
    BT_GATT_CHARACTERISTIC(BT_UUID_MY_CHAR,
                           BT_GATT_CHRC_READ | BT_GATT_CHRC_WRITE,
                           BT_GATT_PERM_READ | BT_GATT_PERM_WRITE,
                           read_my_char, write_my_char, my_value),
);
```

### Service Macros

| Macro | Description |
|-------|-------------|
| `BT_GATT_SERVICE_DEFINE` | Statically define a GATT service |
| `BT_GATT_PRIMARY_SERVICE` | Declare primary service |
| `BT_GATT_SECONDARY_SERVICE` | Declare secondary service |
| `BT_GATT_INCLUDE_SERVICE` | Include another service |
| `BT_GATT_CHARACTERISTIC` | Declare characteristic with value |
| `BT_GATT_DESCRIPTOR` | Declare descriptor |
| `BT_GATT_CCC` | Client Characteristic Configuration |
| `BT_GATT_CUD` | Characteristic User Description |
| `BT_GATT_CEP` | Characteristic Extended Properties |

### Dynamic Service Registration

```c
static struct bt_gatt_attr attrs[] = {
    BT_GATT_PRIMARY_SERVICE(BT_UUID_MY_SERVICE),
    BT_GATT_CHARACTERISTIC(BT_UUID_MY_CHAR,
                           BT_GATT_CHRC_READ,
                           BT_GATT_PERM_READ,
                           read_my_char, NULL, NULL),
};

static struct bt_gatt_service my_svc = BT_GATT_SERVICE(attrs);

/* Register at runtime */
err = bt_gatt_service_register(&my_svc);

/* Unregister */
err = bt_gatt_service_unregister(&my_svc);
```

## GATT Client (Central)

Requires: `CONFIG_BT_GATT_CLIENT=y`

### Service Discovery

```c
static struct bt_gatt_discover_params discover_params;

static uint8_t discover_cb(struct bt_conn *conn,
                           const struct bt_gatt_attr *attr,
                           struct bt_gatt_discover_params *params)
{
    if (!attr) {
        printk("Discovery complete\n");
        return BT_GATT_ITER_STOP;
    }

    printk("Handle: %u\n", attr->handle);

    /* Continue discovery */
    return BT_GATT_ITER_CONTINUE;
}

/* Discover all primary services */
discover_params.uuid = NULL;
discover_params.func = discover_cb;
discover_params.start_handle = BT_ATT_FIRST_ATTRIBUTE_HANDLE;
discover_params.end_handle = BT_ATT_LAST_ATTRIBUTE_HANDLE;
discover_params.type = BT_GATT_DISCOVER_PRIMARY;

err = bt_gatt_discover(conn, &discover_params);
```

### Discovery Types

| Type | Description |
|------|-------------|
| `BT_GATT_DISCOVER_PRIMARY` | Primary services |
| `BT_GATT_DISCOVER_SECONDARY` | Secondary services |
| `BT_GATT_DISCOVER_INCLUDE` | Included services |
| `BT_GATT_DISCOVER_CHARACTERISTIC` | Characteristics |
| `BT_GATT_DISCOVER_DESCRIPTOR` | Descriptors |
| `BT_GATT_DISCOVER_ATTRIBUTE` | Any attribute |

### Reading Attributes

```c
static struct bt_gatt_read_params read_params;

static uint8_t read_cb(struct bt_conn *conn, uint8_t err,
                       struct bt_gatt_read_params *params,
                       const void *data, uint16_t length)
{
    if (err) {
        printk("Read failed (err %u)\n", err);
        return BT_GATT_ITER_STOP;
    }

    if (!data) {
        printk("Read complete\n");
        return BT_GATT_ITER_STOP;
    }

    printk("Data: ");
    for (int i = 0; i < length; i++) {
        printk("%02x ", ((uint8_t *)data)[i]);
    }
    printk("\n");

    return BT_GATT_ITER_CONTINUE;
}

read_params.func = read_cb;
read_params.handle_count = 1;
read_params.single.handle = char_handle;
read_params.single.offset = 0;

err = bt_gatt_read(conn, &read_params);
```

### Writing Attributes

```c
static struct bt_gatt_write_params write_params;

static void write_cb(struct bt_conn *conn, uint8_t err,
                     struct bt_gatt_write_params *params)
{
    if (err) {
        printk("Write failed (err %u)\n", err);
    } else {
        printk("Write complete\n");
    }
}

static uint8_t data[] = {0x01, 0x02, 0x03};

write_params.func = write_cb;
write_params.handle = char_handle;
write_params.offset = 0;
write_params.data = data;
write_params.length = sizeof(data);

err = bt_gatt_write(conn, &write_params);

/* Write without response */
err = bt_gatt_write_without_response(conn, char_handle, data, sizeof(data), false);
```

## Custom Services

### With Notifications

```c
static void ccc_cfg_changed(const struct bt_gatt_attr *attr, uint16_t value)
{
    bool notify_enabled = (value == BT_GATT_CCC_NOTIFY);
    printk("Notifications %s\n", notify_enabled ? "enabled" : "disabled");
}

BT_GATT_SERVICE_DEFINE(my_svc,
    BT_GATT_PRIMARY_SERVICE(BT_UUID_MY_SERVICE),
    BT_GATT_CHARACTERISTIC(BT_UUID_MY_CHAR,
                           BT_GATT_CHRC_READ | BT_GATT_CHRC_NOTIFY,
                           BT_GATT_PERM_READ,
                           read_my_char, NULL, my_value),
    BT_GATT_CCC(ccc_cfg_changed, BT_GATT_PERM_READ | BT_GATT_PERM_WRITE),
);
```

### With Indications

```c
BT_GATT_SERVICE_DEFINE(my_svc,
    BT_GATT_PRIMARY_SERVICE(BT_UUID_MY_SERVICE),
    BT_GATT_CHARACTERISTIC(BT_UUID_MY_CHAR,
                           BT_GATT_CHRC_INDICATE,
                           BT_GATT_PERM_NONE,
                           NULL, NULL, NULL),
    BT_GATT_CCC(ccc_cfg_changed, BT_GATT_PERM_READ | BT_GATT_PERM_WRITE),
);
```

## Notifications and Indications

### Server-Side (Sending)

```c
/* Get attribute for the characteristic value */
const struct bt_gatt_attr *attr = &my_svc.attrs[2];  /* Index of char value */

/* Send notification */
err = bt_gatt_notify(NULL, attr, data, sizeof(data));

/* Send notification with callback */
static struct bt_gatt_notify_params notify_params;

static void notify_cb(struct bt_conn *conn, void *user_data)
{
    printk("Notification sent\n");
}

notify_params.attr = attr;
notify_params.data = data;
notify_params.len = sizeof(data);
notify_params.func = notify_cb;

err = bt_gatt_notify_cb(conn, &notify_params);

/* Send indication */
static struct bt_gatt_indicate_params ind_params;

static void indicate_cb(struct bt_conn *conn,
                        struct bt_gatt_indicate_params *params,
                        uint8_t err)
{
    printk("Indication %s\n", err ? "failed" : "acknowledged");
}

ind_params.attr = attr;
ind_params.data = data;
ind_params.len = sizeof(data);
ind_params.func = indicate_cb;

err = bt_gatt_indicate(conn, &ind_params);
```

### Client-Side (Subscribing)

```c
static struct bt_gatt_subscribe_params subscribe_params;

static uint8_t notify_cb(struct bt_conn *conn,
                         struct bt_gatt_subscribe_params *params,
                         const void *data, uint16_t length)
{
    if (!data) {
        printk("Unsubscribed\n");
        params->value_handle = 0;
        return BT_GATT_ITER_STOP;
    }

    printk("Notification received: %u bytes\n", length);
    return BT_GATT_ITER_CONTINUE;
}

subscribe_params.notify = notify_cb;
subscribe_params.value_handle = char_value_handle;
subscribe_params.ccc_handle = ccc_handle;
subscribe_params.value = BT_GATT_CCC_NOTIFY;  /* or BT_GATT_CCC_INDICATE */

err = bt_gatt_subscribe(conn, &subscribe_params);

/* Unsubscribe */
err = bt_gatt_unsubscribe(conn, &subscribe_params);
```

## Attribute Permissions

| Permission | Description |
|------------|-------------|
| `BT_GATT_PERM_NONE` | No access |
| `BT_GATT_PERM_READ` | Read access |
| `BT_GATT_PERM_WRITE` | Write access |
| `BT_GATT_PERM_READ_ENCRYPT` | Read with encryption |
| `BT_GATT_PERM_WRITE_ENCRYPT` | Write with encryption |
| `BT_GATT_PERM_READ_AUTHEN` | Read with authentication |
| `BT_GATT_PERM_WRITE_AUTHEN` | Write with authentication |
| `BT_GATT_PERM_READ_LESC` | Read with LE Secure Connections |
| `BT_GATT_PERM_WRITE_LESC` | Write with LE Secure Connections |
| `BT_GATT_PERM_PREPARE_WRITE` | Allow prepare writes |

### Characteristic Properties

| Property | Description |
|----------|-------------|
| `BT_GATT_CHRC_BROADCAST` | Broadcast supported |
| `BT_GATT_CHRC_READ` | Read supported |
| `BT_GATT_CHRC_WRITE_WITHOUT_RESP` | Write without response |
| `BT_GATT_CHRC_WRITE` | Write with response |
| `BT_GATT_CHRC_NOTIFY` | Notify supported |
| `BT_GATT_CHRC_INDICATE` | Indicate supported |
| `BT_GATT_CHRC_AUTH` | Authenticated signed writes |
| `BT_GATT_CHRC_EXT_PROP` | Extended properties |

## UUIDs

### Standard 16-bit UUIDs

```c
#include <zephyr/bluetooth/uuid.h>

/* Using standard UUIDs */
BT_UUID_GAP       /* Generic Access */
BT_UUID_GATT      /* Generic Attribute */
BT_UUID_HRS       /* Heart Rate Service */
BT_UUID_BAS       /* Battery Service */
BT_UUID_DIS       /* Device Information Service */

/* Compare UUIDs */
if (bt_uuid_cmp(uuid, BT_UUID_HRS) == 0) {
    /* UUID matches Heart Rate Service */
}
```

### Custom 128-bit UUIDs

```c
/* Define custom UUID */
#define MY_UUID_VAL BT_UUID_128_ENCODE(0x12345678, 0x1234, 0x5678, 0x1234, 0x56789abcdef0)
#define MY_UUID BT_UUID_DECLARE_128(MY_UUID_VAL)

/* At compile time */
static struct bt_uuid_128 my_uuid = BT_UUID_INIT_128(MY_UUID_VAL);

/* String to UUID */
struct bt_uuid_128 uuid;
bt_uuid_create(&uuid.uuid, "12345678-1234-5678-1234-56789abcdef0", 36);
```
