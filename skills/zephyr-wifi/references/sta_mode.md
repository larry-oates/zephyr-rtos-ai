# Station Mode (STA)

Station mode connects to an existing WiFi access point. This is the most common WiFi operation.

## Scanning for Networks

### Basic Scan

```c
#include <zephyr/net/wifi_mgmt.h>
#include <zephyr/net/net_mgmt.h>

static struct net_mgmt_event_callback scan_cb;

static void scan_handler(struct net_mgmt_event_callback *cb,
                         uint32_t mgmt_event, struct net_if *iface)
{
    if (mgmt_event == NET_EVENT_WIFI_SCAN_RESULT) {
        const struct wifi_scan_result *entry =
            (const struct wifi_scan_result *)cb->info;

        printk("%-32s | Ch: %3d | RSSI: %4d | Security: %s\n",
               entry->ssid,
               entry->channel,
               entry->rssi,
               wifi_security_txt(entry->security));
    }

    if (mgmt_event == NET_EVENT_WIFI_SCAN_DONE) {
        printk("Scan complete\n");
    }
}

void start_scan(struct net_if *iface)
{
    net_mgmt_init_event_callback(&scan_cb, scan_handler,
                                 NET_EVENT_WIFI_SCAN_RESULT |
                                 NET_EVENT_WIFI_SCAN_DONE);
    net_mgmt_add_event_callback(&scan_cb);

    int ret = net_mgmt(NET_REQUEST_WIFI_SCAN, iface, NULL, 0);
    if (ret) {
        printk("Scan request failed: %d\n", ret);
    }
}
```

### Filtered Scan

Use `wifi_scan_params` to filter scan results:

```c
struct wifi_scan_params params = {
    .scan_type = WIFI_SCAN_TYPE_ACTIVE,
    .bands = WIFI_FREQ_BAND_2_4_GHZ | WIFI_FREQ_BAND_5_GHZ,
    .dwell_time_active = 50,   /* ms per channel */
    .dwell_time_passive = 130, /* ms for passive scan */
    .max_bss_cnt = 10,         /* Max results to return */
};

/* Scan specific SSID */
params.ssids[0] = "TargetNetwork";
params.num_ssids = 1;

/* Scan specific channels */
params.chan[0].channel = 6;
params.chan[0].band = WIFI_FREQ_BAND_2_4_GHZ;
params.num_chans = 1;

int ret = net_mgmt(NET_REQUEST_WIFI_SCAN, iface, &params, sizeof(params));
```

### Scan Result Structure

```c
struct wifi_scan_result {
    uint8_t ssid[WIFI_SSID_MAX_LEN];
    uint8_t ssid_length;
    uint8_t band;                    /* WIFI_FREQ_BAND_* */
    uint8_t channel;
    enum wifi_security_type security;
    enum wifi_mfp_options mfp;       /* Management Frame Protection */
    int8_t rssi;
    uint8_t mac[6];                  /* BSSID */
    uint8_t mac_length;
};
```

## Connecting to a Network

### WPA2-PSK Connection

```c
static struct net_mgmt_event_callback conn_cb;

static void connection_handler(struct net_mgmt_event_callback *cb,
                               uint32_t mgmt_event, struct net_if *iface)
{
    if (mgmt_event == NET_EVENT_WIFI_CONNECT_RESULT) {
        const struct wifi_status *status =
            (const struct wifi_status *)cb->info;

        if (status->status == 0) {
            printk("Connected successfully\n");
        } else {
            printk("Connection failed: %d\n", status->status);
        }
    }
}

void connect_to_network(struct net_if *iface)
{
    net_mgmt_init_event_callback(&conn_cb, connection_handler,
                                 NET_EVENT_WIFI_CONNECT_RESULT);
    net_mgmt_add_event_callback(&conn_cb);

    struct wifi_connect_req_params params = {
        .ssid = "MyNetwork",
        .ssid_length = strlen("MyNetwork"),
        .psk = "MyPassword",
        .psk_length = strlen("MyPassword"),
        .security = WIFI_SECURITY_TYPE_PSK,
        .channel = WIFI_CHANNEL_ANY,
        .band = WIFI_FREQ_BAND_UNKNOWN,
        .mfp = WIFI_MFP_OPTIONAL,
    };

    int ret = net_mgmt(NET_REQUEST_WIFI_CONNECT, iface,
                       &params, sizeof(params));
    if (ret) {
        printk("Connection request failed: %d\n", ret);
    }
}
```

### WPA3-SAE Connection

```c
struct wifi_connect_req_params params = {
    .ssid = "SecureNetwork",
    .ssid_length = strlen("SecureNetwork"),
    .sae_password = "MyPassword",
    .sae_password_length = strlen("MyPassword"),
    .security = WIFI_SECURITY_TYPE_SAE,
    .mfp = WIFI_MFP_REQUIRED,  /* Mandatory for WPA3 */
    .channel = WIFI_CHANNEL_ANY,
};
```

### Enterprise (EAP-TLS) Connection

```c
struct wifi_connect_req_params params = {
    .ssid = "EnterpriseNetwork",
    .ssid_length = strlen("EnterpriseNetwork"),
    .security = WIFI_SECURITY_TYPE_EAP_TLS,
    .mfp = WIFI_MFP_OPTIONAL,
    /* Certificates configured via wifi_credentials or runtime */
};
```

### Connect Parameters Structure

```c
struct wifi_connect_req_params {
    const uint8_t *ssid;
    uint8_t ssid_length;
    const uint8_t *psk;           /* For WPA2-PSK */
    uint8_t psk_length;
    const uint8_t *sae_password;  /* For WPA3-SAE */
    uint8_t sae_password_length;
    uint8_t band;                 /* WIFI_FREQ_BAND_* or UNKNOWN */
    uint8_t channel;              /* WIFI_CHANNEL_ANY or specific */
    enum wifi_security_type security;
    enum wifi_mfp_options mfp;
    int timeout;                  /* Connection timeout in seconds */
};
```

## Disconnecting

```c
static void disconnect_handler(struct net_mgmt_event_callback *cb,
                               uint32_t mgmt_event, struct net_if *iface)
{
    if (mgmt_event == NET_EVENT_WIFI_DISCONNECT_RESULT) {
        const struct wifi_status *status =
            (const struct wifi_status *)cb->info;
        printk("Disconnected: reason %d\n", status->status);
    }
}

void disconnect(struct net_if *iface)
{
    int ret = net_mgmt(NET_REQUEST_WIFI_DISCONNECT, iface, NULL, 0);
    if (ret) {
        printk("Disconnect request failed: %d\n", ret);
    }
}
```

## Checking Connection Status

```c
void check_status(struct net_if *iface)
{
    struct wifi_iface_status status = {0};

    int ret = net_mgmt(NET_REQUEST_WIFI_IFACE_STATUS, iface,
                       &status, sizeof(status));
    if (ret) {
        printk("Status request failed: %d\n", ret);
        return;
    }

    printk("State: %s\n", wifi_state_txt(status.state));

    if (status.state >= WIFI_STATE_ASSOCIATED) {
        printk("SSID: %s\n", status.ssid);
        printk("BSSID: %02x:%02x:%02x:%02x:%02x:%02x\n",
               status.bssid[0], status.bssid[1], status.bssid[2],
               status.bssid[3], status.bssid[4], status.bssid[5]);
        printk("Channel: %d\n", status.channel);
        printk("RSSI: %d dBm\n", status.rssi);
        printk("Security: %s\n", wifi_security_txt(status.security));
        printk("Link mode: %s\n", wifi_link_mode_txt(status.link_mode));
    }
}
```

### Interface Status Structure

```c
struct wifi_iface_status {
    enum wifi_iface_state state;     /* WIFI_STATE_* */
    unsigned int ssid_len;
    char ssid[WIFI_SSID_MAX_LEN];
    char bssid[WIFI_MAC_ADDR_LEN];
    enum wifi_frequency_bands band;
    unsigned int channel;
    enum wifi_iface_mode iface_mode; /* STA, AP, etc. */
    enum wifi_link_mode link_mode;   /* WiFi 4/5/6/6E/7 */
    enum wifi_security_type security;
    enum wifi_mfp_options mfp;
    int rssi;
    unsigned int beacon_interval;
    unsigned int dtim_period;
    enum wifi_twt_sleep_state twt_capable;
};
```

## Credential Storage

For persistent credentials, use the WiFi credentials API:

```c
#include <zephyr/net/wifi_credentials.h>

/* Store credentials */
struct wifi_credentials_personal creds = {
    .header = {
        .type = WIFI_SECURITY_TYPE_PSK,
        .ssid = "MyNetwork",
        .ssid_len = strlen("MyNetwork"),
    },
    .password = "MyPassword",
    .password_len = strlen("MyPassword"),
};

wifi_credentials_set_personal(&creds);

/* Auto-connect using stored credentials */
wifi_credentials_connect_stored(iface);
```

Kconfig for credentials:
```
CONFIG_WIFI_CREDENTIALS=y
CONFIG_WIFI_CREDENTIALS_BACKEND_SETTINGS=y
CONFIG_SETTINGS=y
CONFIG_NVS=y
CONFIG_FLASH=y
CONFIG_FLASH_MAP=y
```

## Connection State Machine

```
DISCONNECTED
    │
    ▼ (NET_REQUEST_WIFI_CONNECT)
ASSOCIATING
    │
    ├──(fail)──► DISCONNECTED
    ▼
ASSOCIATED
    │
    ▼ (4-way handshake)
COMPLETED (Connected)
    │
    ▼ (NET_REQUEST_WIFI_DISCONNECT or AP loss)
DISCONNECTED
```

## Common Issues

### Connection Timeout
- Increase timeout in `wifi_connect_req_params.timeout`
- Check signal strength (RSSI should be > -80 dBm)
- Verify SSID and password are correct

### Authentication Failure
- Verify security type matches AP configuration
- For WPA3, ensure `mfp = WIFI_MFP_REQUIRED`
- Check password length (8-63 chars for WPA2/WPA3)

### No Scan Results
- Ensure WiFi is enabled and interface is up
- Check regulatory domain settings
- Try both active and passive scan types
