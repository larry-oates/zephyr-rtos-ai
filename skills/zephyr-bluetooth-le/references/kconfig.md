# Bluetooth LE Kconfig Options

Common Kconfig options for BLE development in Zephyr.

## Table of Contents

- [Core Options](#core-options)
- [GAP Role Options](#gap-role-options)
- [GATT Options](#gatt-options)
- [Security Options](#security-options)
- [Connection Options](#connection-options)
- [Buffer Options](#buffer-options)
- [Logging Options](#logging-options)

## Core Options

### Enable Bluetooth

```
CONFIG_BT=y
```

### Device Name and Appearance

```
CONFIG_BT_DEVICE_NAME="My Device"
CONFIG_BT_DEVICE_APPEARANCE=0    # Generic (see Bluetooth SIG assigned numbers)
```

Common appearance values:
- `0` - Unknown
- `64` - Generic Phone
- `128` - Generic Computer
- `833` - Heart Rate Sensor
- `961` - Running/Walking Sensor

### Bluetooth Shell (Debugging)

```
CONFIG_BT_SHELL=y
```

## GAP Role Options

### Peripheral Role

```
CONFIG_BT_PERIPHERAL=y
```

### Central Role

```
CONFIG_BT_CENTRAL=y
```

### Broadcaster Role

```
CONFIG_BT_BROADCASTER=y
```

### Observer Role

```
CONFIG_BT_OBSERVER=y
```

## GATT Options

### Client Role

```
CONFIG_BT_GATT_CLIENT=y
```

### Dynamic Database

```
CONFIG_BT_GATT_DYNAMIC_DB=y          # Allow runtime service registration
```

### Auto-MTU Exchange

```
CONFIG_BT_GATT_AUTO_UPDATE_MTU=y     # Automatically negotiate MTU
CONFIG_BT_L2CAP_TX_MTU=247           # Maximum MTU size
```

### GATT Caching

```
CONFIG_BT_GATT_CACHING=y             # Enable GATT caching
CONFIG_BT_GATT_SERVICE_CHANGED=y     # Service changed characteristic
```

### Multiple Notifications

```
CONFIG_BT_GATT_NOTIFY_MULTIPLE=y     # Send multiple notifications at once
```

## Security Options

### SMP (Security Manager Protocol)

```
CONFIG_BT_SMP=y                      # Enable pairing/bonding
CONFIG_BT_SMP_SC_ONLY=n              # Allow legacy pairing
CONFIG_BT_SMP_SC_PAIR_ONLY=y         # Require LE Secure Connections
```

### Bonding

```
CONFIG_BT_SETTINGS=y                 # Required for bonding persistence
CONFIG_BT_MAX_PAIRED=5               # Max bonded devices
CONFIG_BT_BONDABLE=y                 # Allow bonding
CONFIG_BT_BONDING_REQUIRED=n         # Require bonding for connections
```

### Privacy

```
CONFIG_BT_PRIVACY=y                  # Enable RPA (Resolvable Private Address)
CONFIG_BT_RPA_TIMEOUT=900            # RPA rotation interval (seconds)
```

### Fixed Passkey

```
CONFIG_BT_FIXED_PASSKEY=y
CONFIG_BT_PASSKEY=123456             # 6-digit passkey
```

### OOB Pairing

```
CONFIG_BT_OOB_DATA_FIXED=y           # Use fixed OOB data (for testing)
```

## Connection Options

### Connection Count

```
CONFIG_BT_MAX_CONN=1                 # Max simultaneous connections
```

### Connection Parameters

```
CONFIG_BT_CONN_PARAM_UPDATE_TIMEOUT=5000   # Parameter update timeout (ms)
```

### PHY Options

```
CONFIG_BT_USER_PHY_UPDATE=y          # Allow application to control PHY
CONFIG_BT_PHY_UPDATE=y               # Enable PHY update procedure
```

### Data Length Extension

```
CONFIG_BT_USER_DATA_LEN_UPDATE=y     # Allow application to control data length
CONFIG_BT_DATA_LEN_UPDATE=y          # Enable data length extension
CONFIG_BT_CTLR_DATA_LENGTH_MAX=251   # Maximum data length
```

## Buffer Options

### ACL Buffers

```
CONFIG_BT_BUF_ACL_TX_SIZE=251        # TX buffer size
CONFIG_BT_BUF_ACL_TX_COUNT=7         # Number of TX buffers
CONFIG_BT_BUF_ACL_RX_SIZE=251        # RX buffer size
CONFIG_BT_BUF_ACL_RX_COUNT=6         # Number of RX buffers
```

### ATT MTU

```
CONFIG_BT_L2CAP_TX_MTU=247           # L2CAP MTU (ATT MTU = MTU - 4)
CONFIG_BT_ATT_PREPARE_COUNT=0        # Prepare write queue size
```

## Extended Advertising

```
CONFIG_BT_EXT_ADV=y                  # Enable extended advertising
CONFIG_BT_EXT_ADV_MAX_ADV_SET=1      # Maximum advertising sets
CONFIG_BT_EXT_ADV_LEGACY_SUPPORT=y   # Also support legacy advertising
```

## Periodic Advertising

```
CONFIG_BT_PER_ADV=y                  # Enable periodic advertising
CONFIG_BT_PER_ADV_SYNC=y             # Enable sync to periodic advertising
CONFIG_BT_PER_ADV_SYNC_MAX=1         # Maximum syncs
```

## Logging Options

```
CONFIG_BT_DEBUG_LOG=y                # General BT logging
CONFIG_BT_LOG_LEVEL_DBG=y            # Debug level

# Subsystem-specific logging
CONFIG_BT_HCI_CORE_LOG_LEVEL_DBG=y   # HCI logging
CONFIG_BT_CONN_LOG_LEVEL_DBG=y       # Connection logging
CONFIG_BT_GATT_LOG_LEVEL_DBG=y       # GATT logging
CONFIG_BT_SMP_LOG_LEVEL_DBG=y        # SMP logging
CONFIG_BT_ATT_LOG_LEVEL_DBG=y        # ATT logging
CONFIG_BT_L2CAP_LOG_LEVEL_DBG=y      # L2CAP logging
```

## Controller Options

For boards with Zephyr's BLE controller:

```
CONFIG_BT_LL_SW_SPLIT=y              # Use Zephyr's LL implementation
CONFIG_BT_CTLR_TX_PWR_PLUS_8=y       # Set TX power (+8 dBm example)
CONFIG_BT_CTLR_TX_BUFFER_SIZE=251    # Controller TX buffer
```

## Common Configurations

### Minimal Peripheral

```
CONFIG_BT=y
CONFIG_BT_PERIPHERAL=y
CONFIG_BT_DEVICE_NAME="Minimal"
```

### Peripheral with Bonding

```
CONFIG_BT=y
CONFIG_BT_PERIPHERAL=y
CONFIG_BT_DEVICE_NAME="Secure Device"
CONFIG_BT_SMP=y
CONFIG_BT_SETTINGS=y
CONFIG_FLASH=y
CONFIG_FLASH_MAP=y
CONFIG_NVS=y
CONFIG_SETTINGS=y
```

### Central with GATT Client

```
CONFIG_BT=y
CONFIG_BT_CENTRAL=y
CONFIG_BT_GATT_CLIENT=y
CONFIG_BT_SCAN_NAME_MAX_LEN=32
```

### High-Throughput Configuration

```
CONFIG_BT=y
CONFIG_BT_PERIPHERAL=y
CONFIG_BT_L2CAP_TX_MTU=247
CONFIG_BT_BUF_ACL_TX_SIZE=251
CONFIG_BT_BUF_ACL_TX_COUNT=10
CONFIG_BT_CTLR_DATA_LENGTH_MAX=251
CONFIG_BT_GATT_NOTIFY_MULTIPLE=y
```

### Long-Range (Coded PHY)

```
CONFIG_BT=y
CONFIG_BT_PERIPHERAL=y
CONFIG_BT_EXT_ADV=y
CONFIG_BT_CTLR_PHY_CODED=y
```
