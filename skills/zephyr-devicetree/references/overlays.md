# Devicetree Overlays

Overlays (.overlay files) allow you to modify the base devicetree without changing the original board files.

## Common Tasks

### Overriding a Property
Use a node label to refer to the node and override its property.

```devicetree
&uart0 {
    current-speed = <9600>;
    status = "okay";
};
```

### Adding an Alias or Chosen Node
```devicetree
/ {
    aliases {
        debug-uart = &uart0;
    };

    chosen {
        zephyr,console = &uart0;
    };
};
```

### Deleting a Property or Node
```devicetree
&uart0 {
    /delete-property/ hw-flow-control;
};

/ {
    /delete-node/ unwanted-node;
};
```

### Adding a Child Device (e.g., I2C Sensor)
```devicetree
&i2c1 {
    status = "okay";
    my_sensor: sensor@4a {
        compatible = "vendor,sensor-model";
        reg = <0x4a>;
        label = "ENV_SENSOR";
    };
};
```

## Overlay Search Order
If not explicitly set via `DTC_OVERLAY_FILE`, Zephyr looks for:
1. `socs/<SOC>_<BOARD_QUALIFIERS>.overlay`
2. `boards/<BOARD>.overlay`
3. `boards/<BOARD>_<revision>.overlay`
4. `<BOARD>.overlay`
5. `app.overlay`
