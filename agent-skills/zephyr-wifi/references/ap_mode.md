# Access Point Mode (AP / SoftAP)

Access Point mode allows the device to create a WiFi network that other devices can connect to.

## Prerequisites

AP mode requires the wpa_supplicant network manager:

```
CONFIG_WIFI_NM_WPA_SUPPLICANT=y
CONFIG_WIFI_NM_WPA_SUPPLICANT_AP=y
```

## Basic AP Configuration

```c
#include <zephyr/net/wifi_mgmt.h>
#include <zephyr/net/net_mgmt.h>
#include <zephyr/net/net_if.h>

static struct net_mgmt_event_callback ap_cb;

static void ap_event_handler(struct net_mgmt_event_callback *cb,
                             uint32_t mgmt_event, struct net_if *iface)
{
    switch (mgmt_event) {
    case NET_EVENT_WIFI_AP_ENABLE_RESULT: {
        const struct wifi_status *status =
            (const struct wifi_status *)cb->info;
        if (status->status == 0) {
            printk("AP mode enabled\n");
        } else {
            printk("AP enable failed: %d\n", status->status);
        }
        break;
    }
    case NET_EVENT_WIFI_AP_DISABLE_RESULT:
        printk("AP mode disabled\n");
        break;
    case NET_EVENT_WIFI_AP_STA_CONNECTED: {
        const struct wifi_ap_sta_info *sta =
            (const struct wifi_ap_sta_info *)cb->info;
        printk("Station connected: %02x:%02x:%02x:%02x:%02x:%02x\n",
               sta->mac[0], sta->mac[1], sta->mac[2],
               sta->mac[3], sta->mac[4], sta->mac[5]);
        break;
    }
    case NET_EVENT_WIFI_AP_STA_DISCONNECTED: {
        const struct wifi_ap_sta_info *sta =
            (const struct wifi_ap_sta_info *)cb->info;
        printk("Station disconnected: %02x:%02x:%02x:%02x:%02x:%02x\n",
               sta->mac[0], sta->mac[1], sta->mac[2],
               sta->mac[3], sta->mac[4], sta->mac[5]);
        break;
    }
    }
}

void start_ap(void)
{
    struct net_if *iface = net_if_get_wifi_sap();
    if (!iface) {
        printk("SoftAP interface not found\n");
        return;
    }

    /* Register event callbacks */
    net_mgmt_init_event_callback(&ap_cb, ap_event_handler,
                                 NET_EVENT_WIFI_AP_ENABLE_RESULT |
                                 NET_EVENT_WIFI_AP_DISABLE_RESULT |
                                 NET_EVENT_WIFI_AP_STA_CONNECTED |
                                 NET_EVENT_WIFI_AP_STA_DISCONNECTED);
    net_mgmt_add_event_callback(&ap_cb);

    /* Configure AP parameters */
    struct wifi_connect_req_params params = {
        .ssid = "MyAccessPoint",
        .ssid_length = strlen("MyAccessPoint"),
        .psk = "password123",
        .psk_length = strlen("password123"),
        .security = WIFI_SECURITY_TYPE_PSK,
        .channel = 6,
        .band = WIFI_FREQ_BAND_2_4_GHZ,
    };

    int ret = net_mgmt(NET_REQUEST_WIFI_AP_ENABLE, iface,
                       &params, sizeof(params));
    if (ret) {
        printk("AP enable request failed: %d\n", ret);
    }
}
```

## Stop AP Mode

```c
void stop_ap(struct net_if *iface)
{
    int ret = net_mgmt(NET_REQUEST_WIFI_AP_DISABLE, iface, NULL, 0);
    if (ret) {
        printk("AP disable request failed: %d\n", ret);
    }
}
```

## AP Configuration Parameters

The same `wifi_connect_req_params` structure is used for AP mode:

```c
struct wifi_connect_req_params params = {
    .ssid = "NetworkName",       /* AP SSID (1-32 chars) */
    .ssid_length = 11,
    .psk = "password",           /* For WPA2 (8-63 chars) */
    .psk_length = 8,
    .security = WIFI_SECURITY_TYPE_PSK,  /* Open or PSK */
    .channel = 6,                /* Specific channel */
    .band = WIFI_FREQ_BAND_2_4_GHZ,
    .bandwidth = WIFI_FREQ_BANDWIDTH_20MHZ,  /* Optional */
};
```

### Security Options for AP

| Security | Configuration |
|----------|---------------|
| Open | `.security = WIFI_SECURITY_TYPE_NONE` |
| WPA2-PSK | `.security = WIFI_SECURITY_TYPE_PSK`, `.psk` required |
| WPA3-SAE | `.security = WIFI_SECURITY_TYPE_SAE`, `.sae_password` required |

## Get Connected Stations

```c
void list_connected_stations(struct net_if *iface)
{
    struct wifi_ap_sta_list sta_list = {0};

    int ret = net_mgmt(NET_REQUEST_WIFI_AP_STA_LIST, iface,
                       &sta_list, sizeof(sta_list));
    if (ret) {
        printk("Failed to get station list: %d\n", ret);
        return;
    }

    printk("Connected stations: %d\n", sta_list.num_sta);
    for (int i = 0; i < sta_list.num_sta; i++) {
        printk("  %d: %02x:%02x:%02x:%02x:%02x:%02x\n", i,
               sta_list.sta[i].mac[0], sta_list.sta[i].mac[1],
               sta_list.sta[i].mac[2], sta_list.sta[i].mac[3],
               sta_list.sta[i].mac[4], sta_list.sta[i].mac[5]);
    }
}
```

## Disconnect a Station

```c
void disconnect_station(struct net_if *iface, const uint8_t *mac)
{
    struct wifi_ap_sta_info sta = {0};
    memcpy(sta.mac, mac, WIFI_MAC_ADDR_LEN);

    int ret = net_mgmt(NET_REQUEST_WIFI_AP_STA_DISCONNECT, iface,
                       &sta, sizeof(sta));
    if (ret) {
        printk("Failed to disconnect station: %d\n", ret);
    }
}
```

## AP + STA Mode (Concurrent)

Some drivers support running AP and STA modes simultaneously:

```c
/* Get both interfaces */
struct net_if *sta_iface = net_if_get_wifi_sta();
struct net_if *ap_iface = net_if_get_wifi_sap();

/* Connect as STA first */
struct wifi_connect_req_params sta_params = {
    .ssid = "ExternalNetwork",
    .ssid_length = strlen("ExternalNetwork"),
    .psk = "password",
    .psk_length = strlen("password"),
    .security = WIFI_SECURITY_TYPE_PSK,
};
net_mgmt(NET_REQUEST_WIFI_CONNECT, sta_iface, &sta_params, sizeof(sta_params));

/* Then enable AP */
struct wifi_connect_req_params ap_params = {
    .ssid = "MyHotspot",
    .ssid_length = strlen("MyHotspot"),
    .psk = "appassword",
    .psk_length = strlen("appassword"),
    .security = WIFI_SECURITY_TYPE_PSK,
    .channel = 6,
};
net_mgmt(NET_REQUEST_WIFI_AP_ENABLE, ap_iface, &ap_params, sizeof(ap_params));
```

## AP Mode Kconfig

```
# Core requirements
CONFIG_WIFI=y
CONFIG_WIFI_NRF70=y                        # Or your driver
CONFIG_NET_L2_WIFI_MGMT=y
CONFIG_NETWORKING=y

# wpa_supplicant for AP
CONFIG_WIFI_NM_WPA_SUPPLICANT=y
CONFIG_WIFI_NM_WPA_SUPPLICANT_AP=y

# Network configuration
CONFIG_NET_IPV4=y
CONFIG_NET_CONFIG_SETTINGS=y
CONFIG_NET_CONFIG_MY_IPV4_ADDR="192.168.4.1"
CONFIG_NET_CONFIG_MY_IPV4_NETMASK="255.255.255.0"

# Optional: DHCP server for clients
CONFIG_NET_DHCPV4_SERVER=y

# Max stations
CONFIG_WIFI_MGMT_AP_MAX_NUM_STA=8
```

## DHCP Server for AP Mode

To provide IP addresses to connected clients:

```c
#include <zephyr/net/dhcpv4_server.h>

void setup_dhcp_server(struct net_if *iface)
{
    struct in_addr base_addr;
    struct in_addr netmask;

    net_addr_pton(AF_INET, "192.168.4.2", &base_addr);

    int ret = net_dhcpv4_server_start(iface, &base_addr);
    if (ret) {
        printk("DHCP server start failed: %d\n", ret);
    }
}
```

## AP Events

| Event | Description | Info Structure |
|-------|-------------|----------------|
| `NET_EVENT_WIFI_AP_ENABLE_RESULT` | AP enabled/failed | `wifi_status` |
| `NET_EVENT_WIFI_AP_DISABLE_RESULT` | AP disabled | `wifi_status` |
| `NET_EVENT_WIFI_AP_STA_CONNECTED` | Client connected | `wifi_ap_sta_info` |
| `NET_EVENT_WIFI_AP_STA_DISCONNECTED` | Client disconnected | `wifi_ap_sta_info` |

## Common Issues

### AP Won't Start
- Verify `CONFIG_WIFI_NM_WPA_SUPPLICANT_AP=y` is set
- Check if channel is valid for the regulatory domain
- Ensure driver supports AP mode

### Clients Can't Connect
- Verify SSID is being broadcast (check with external device)
- Check security settings match client configuration
- Ensure IP configuration is correct

### No IP for Clients
- Enable DHCP server (`CONFIG_NET_DHCPV4_SERVER=y`)
- Configure static IP for AP interface
- Verify subnet configuration
