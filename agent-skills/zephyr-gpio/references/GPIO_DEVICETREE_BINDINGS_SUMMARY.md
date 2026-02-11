# GPIO Devicetree Binding Properties and Examples

## Overview
This document summarizes the key GPIO devicetree binding properties and patterns extracted from Zephyr RTOS. These are generic patterns applicable to GPIO controller, GPIO-based input devices (buttons), and GPIO-based output devices (LEDs).

---

## 1. GPIO Controller Bindings

### File: `gpio-controller.yaml`
**Purpose**: Defines common properties for GPIO controller nodes

#### Required Properties

| Property | Type | Description |
|----------|------|-------------|
| `gpio-controller` | boolean | Conveys that this node is a GPIO controller. **Must be present.** |
| `#gpio-cells` | int | Number of items to expect in a GPIO specifier (typically 2: pin + flags) |

#### Optional Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `ngpios` | int | 32 | Number of in-use GPIO slots. Example: if hardware has 32-bit register but only 18 bits are physically available, set `ngpios = <18>`. Useful when only first N GPIOs (0...N-1) are in use. |
| `gpio-reserved-ranges` | array | — | Specifies unusable GPIO offsets as tuples (start, size). Example: `gpio-reserved-ranges = <3 2>, <10 1>;` marks offsets 3, 4, and 10 as unavailable. |
| `gpio-line-names` | string-array | — | Array of strings naming the GPIO lines on this controller. Helps with documentation and debugging. |

#### Example GPIO Controller DTS

```devicetree
gpio0: gpio@40022000 {
	compatible = "st,stm32-gpio";
	reg = <0x40022000 0x400>;
	clocks = <&clk_ahb1 5>;
	gpio-controller;
	#gpio-cells = <2>;
	ngpios = <16>;
	gpio-line-names = "LED1", "LED2", "BUTTON1", "", "", "", "", "",
	                  "", "", "", "", "", "", "", "";
};

gpio1: gpio@40023000 {
	compatible = "st,stm32-gpio";
	reg = <0x40023000 0x400>;
	clocks = <&clk_ahb1 6>;
	gpio-controller;
	#gpio-cells = <2>;
	ngpios = <16>;
	gpio-reserved-ranges = <12 4>;  /* Pins 12-15 not usable */
};
```

---

## 2. GPIO Specifier Format

### The `gpios` Property Syntax

The `gpios` property is used to reference GPIO pins. Format depends on `#gpio-cells`:

```
gpios = <&gpio_controller pin flags>;
```

For `#gpio-cells = <2>` (most common):
- **First cell**: Pin number (0-based index)
- **Second cell**: Flags (active level, drive mode, bias, interrupts)

### GPIO Flags Reference

Defined in `zephyr/dt-bindings/gpio/gpio.h`:

#### Active Level Flags

| Flag | Value | Description |
|------|-------|-------------|
| `GPIO_ACTIVE_LOW` | `(1 << 0)` | Pin is active when LOW. Output high to deactivate. |
| `GPIO_ACTIVE_HIGH` | `(0 << 0)` | Pin is active when HIGH (default). Output low to deactivate. |

#### Drive Mode Flags

| Flag | Description |
|------|-------------|
| `GPIO_OPEN_DRAIN` | Output behaves like open collector (wired AND). Pin connects to ground when active, high-impedance when inactive. |
| `GPIO_OPEN_SOURCE` | Output behaves like open emitter (wired OR). Pin connects to supply when active. |
| `GPIO_PUSH_PULL` | Standard output (default). Pin actively driven high or low. |

#### Bias Flags

| Flag | Description |
|------|-------------|
| `GPIO_PULL_UP` | Enable internal pull-up resistor |
| `GPIO_PULL_DOWN` | Enable internal pull-down resistor |

#### Interrupt/Wakeup Flag

| Flag | Description |
|------|-------------|
| `GPIO_INT_WAKEUP` | GPIO interrupt capable of waking system from low power mode |

#### Combined Flags

Flags are combined bitwise using `|` operator:

```devicetree
gpios = <&gpio0 13 (GPIO_PULL_UP | GPIO_ACTIVE_LOW)>;
```

### GPIO Specifier Examples

```devicetree
/* Simple output, active high */
gpios = <&gpio0 1 GPIO_ACTIVE_HIGH>;

/* Input with pull-up, active low */
gpios = <&gpio0 13 (GPIO_PULL_UP | GPIO_ACTIVE_LOW)>;

/* Output with pull-up, active low */
gpios = <&gpio1 15 (GPIO_PULL_UP | GPIO_ACTIVE_LOW)>;

/* Open-drain output */
gpios = <&gpio0 5 (GPIO_OPEN_DRAIN | GPIO_ACTIVE_LOW)>;
```

---

## 3. GPIO Hogs (Automatic GPIO Configuration)

### GPIO Hog Binding
**Requires**: `CONFIG_GPIO_HOGS` enabled

Allows GPIO configuration to happen automatically during driver initialization without requiring application code.

#### Required Properties (GPIO Hog Child Nodes)

| Property | Type | Description |
|----------|------|-------------|
| `gpio-hog` | boolean | Marks this node as a GPIO hog configuration |
| `gpios` | array | GPIO specifiers to be hogged. Array entries must be integer multiples of controller's `#gpio-cells`. |

#### Optional Properties (Hog Configuration)

| Property | Type | Description | Precedence |
|----------|------|-------------|------------|
| `input` | boolean | Configure GPIO as input | Highest |
| `output-low` | boolean | Configure GPIO as output, set to LOW | Medium |
| `output-high` | boolean | Configure GPIO as output, set to HIGH | Lowest |
| `line-name` | string | Optional descriptive name for GPIO line | — |

#### Example GPIO Hogs

```devicetree
&gpio0 {
	mux-hog {
		gpio-hog;
		gpios = <10 GPIO_ACTIVE_HIGH>, <11 GPIO_ACTIVE_HIGH>;
		output-high;
		line-name = "MUX_SEL0", "MUX_SEL1";
	};
};

&gpio1 {
	test-hog {
		gpio-hog;
		gpios = <26 GPIO_ACTIVE_HIGH>;
		output-low;
		line-name = "TEST_GPIO";
	};
};

&gpio2 {
	button-hog {
		gpio-hog;
		gpios = <5 (GPIO_PULL_UP | GPIO_ACTIVE_LOW)>;
		input;
		line-name = "BUTTON_INPUT";
	};
};
```

---

## 4. GPIO-Based Input Devices (Buttons)

### File: `gpio-keys.yaml`
**Compatible**: `"gpio-keys"`

Defines a group of buttons/keys that generate input events.

#### Parent Node Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `compatible` | string | — | Must be `"gpio-keys"` |
| `debounce-interval-ms` | int | 30 | Debounce interval in milliseconds |
| `polling-mode` | boolean | — | If set, poll pins periodically instead of using interrupts |
| `no-disconnect` | boolean | — | Don't disconnect pin on suspend (for GPIO controllers lacking GPIO_DISCONNECTED support) |

#### Child Node Properties (Button Definition)

| Property | Type | Description |
|----------|------|-------------|
| `gpios` | phandle-array | **Required.** GPIO specifier(s) for the button pin |
| `label` | string | Descriptive name of the button (e.g., "User Button") |
| `zephyr,code` | int | Input event code to emit when button pressed (see `zephyr/dt-bindings/input/input-event-codes.h`) |

#### Example GPIO Keys

```devicetree
#include <zephyr/dt-bindings/input/input-event-codes.h>

buttons {
	compatible = "gpio-keys";
	debounce-interval-ms = <50>;

	button_0 {
		gpios = <&gpio0 13 (GPIO_PULL_UP | GPIO_ACTIVE_LOW)>;
		zephyr,code = <INPUT_KEY_0>;
		label = "User Button";
	};

	button_1 {
		gpios = <&gpio1 5 (GPIO_PULL_UP | GPIO_ACTIVE_LOW)>;
		zephyr,code = <INPUT_KEY_1>;
		label = "Reset Button";
	};
};

/* Alternative with polling instead of interrupts */
buttons_polling {
	compatible = "gpio-keys";
	debounce-interval-ms = <30>;
	polling-mode;

	key_select {
		gpios = <&gpio0 3 (GPIO_PULL_UP | GPIO_ACTIVE_LOW)>;
		zephyr,code = <INPUT_KEY_ENTER>;
	};
};
```

---

## 5. GPIO-Based Output Devices (LEDs)

### File: `gpio-leds.yaml`
**Compatible**: `"gpio-leds"`

Defines a group of LEDs controlled by GPIO pins.

#### Parent Node Properties

| Property | Type | Description |
|----------|------|-------------|
| `compatible` | string | Must be `"gpio-leds"` |

#### Child Node Properties (LED Definition)

| Property | Type | Description |
|----------|------|-------------|
| `gpios` | phandle-array | **Required.** GPIO specifier for the LED pin |
| `label` | string | Name of the LED (optional, from inherited led-node.yaml) |

#### Example GPIO LEDs

```devicetree
leds {
	compatible = "gpio-leds";

	led_0 {
		gpios = <&gpio0 1 GPIO_ACTIVE_LOW>;
		label = "Red LED";
	};

	led_1 {
		gpios = <&gpio0 2 GPIO_ACTIVE_HIGH>;
		label = "Green LED";
	};

	led_2 {
		gpios = <&gpio1 15 (GPIO_PULL_UP | GPIO_ACTIVE_LOW)>;
		label = "Blue LED";
	};
};
```

**Interpretation**:
- `led_0`: Pin 1 on GPIO0, LED is ON when pin is LOW, OFF when HIGH
- `led_1`: Pin 2 on GPIO0, LED is ON when pin is HIGH, OFF when LOW
- `led_2`: Pin 15 on GPIO1, LED is ON when pin is LOW, internal pull-up enabled

---

## 6. GPIO Nexus Binding

### File: `gpio-nexus.yaml`
**Purpose**: Provides GPIO mapping/redirection between controllers

Used for complex scenarios where GPIO references need to be mapped or multiplexed.

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `gpio-map` | compound | **Required.** Defines GPIO mapping entries |
| `gpio-map-mask` | array | Mask for matching GPIO specifiers |
| `gpio-map-pass-thru` | array | Flags to pass through mapping |
| `#gpio-cells` | int | Number of cells in GPIO specifiers |

#### Example GPIO Nexus

```devicetree
/* GPIO multiplexer/redirector */
gpio_mux: gpio-mux {
	compatible = "gpio-nexus";
	#gpio-cells = <2>;

	gpio-map =
		<0 0 &gpio0 1 0>,
		<1 0 &gpio0 2 0>,
		<2 0 &gpio1 5 0>;

	gpio-map-mask = <0xF 0x0>;
	gpio-map-pass-thru = <0x0 0x7>;
};

/* Usage: reference the mux instead of individual GPIO controllers */
led {
	gpios = <&gpio_mux 0 GPIO_ACTIVE_HIGH>;  /* Maps to &gpio0 1 */
};
```

---

## 7. Real-World Examples

### Complete Board Definition

```devicetree
/ {
	soc {
		gpio0: gpio@40022000 {
			compatible = "st,stm32-gpio";
			reg = <0x40022000 0x400>;
			clocks = <&clk_ahb1 5>;
			gpio-controller;
			#gpio-cells = <2>;
			ngpios = <16>;
			gpio-line-names =
				"SDA", "SCL", "LED_RED", "LED_GREEN",
				"LED_BLUE", "BUTTON", "TX", "RX",
				"", "", "", "", "", "", "", "";
		};

		gpio1: gpio@40023000 {
			compatible = "st,stm32-gpio";
			reg = <0x40023000 0x400>;
			clocks = <&clk_ahb1 6>;
			gpio-controller;
			#gpio-cells = <2>;
			ngpios = <16>;
		};
	};

	leds {
		compatible = "gpio-leds";

		led_red {
			gpios = <&gpio0 2 GPIO_ACTIVE_HIGH>;
			label = "Red";
		};

		led_green {
			gpios = <&gpio0 3 GPIO_ACTIVE_HIGH>;
			label = "Green";
		};

		led_blue {
			gpios = <&gpio0 4 GPIO_ACTIVE_HIGH>;
			label = "Blue";
		};
	};

	buttons {
		compatible = "gpio-keys";
		debounce-interval-ms = <30>;

		button_user {
			gpios = <&gpio0 5 (GPIO_PULL_UP | GPIO_ACTIVE_LOW)>;
			zephyr,code = <INPUT_KEY_0>;
			label = "User Button";
		};
	};

	/* GPIO hogging - automatic configuration */
	&gpio0 {
		status-hog {
			gpio-hog;
			gpios = <8 GPIO_ACTIVE_HIGH>;
			output-low;
			line-name = "STATUS";
		};
	};
};
```

---

## 8. Key Patterns & Best Practices

### Pattern 1: Active Level Selection
```devicetree
/* LED that's on when pin is LOW (common with open-drain outputs) */
gpios = <&gpio0 1 GPIO_ACTIVE_LOW>;

/* Button that triggers when pin goes LOW (with pull-up) */
gpios = <&gpio0 13 (GPIO_PULL_UP | GPIO_ACTIVE_LOW)>;
```

### Pattern 2: Multiple GPIO Hogging
```devicetree
&gpio0 {
	multi-hog {
		gpio-hog;
		gpios = <10 GPIO_ACTIVE_HIGH>,
		        <11 GPIO_ACTIVE_HIGH>,
		        <12 GPIO_ACTIVE_HIGH>;
		output-low;
	};
};
```

### Pattern 3: GPIO with Reserved Ranges
```devicetree
gpio_restricted: gpio@40030000 {
	compatible = "vendor,gpio";
	reg = <0x40030000 0x400>;
	gpio-controller;
	#gpio-cells = <2>;
	ngpios = <32>;
	/* Pins 12-15 and 28-31 cannot be used */
	gpio-reserved-ranges = <12 4>, <28 4>;
};
```

---

## 9. Related Header Files

For implementation, include:
- `zephyr/dt-bindings/gpio/gpio.h` - GPIO flag definitions
- `zephyr/dt-bindings/input/input-event-codes.h` - Button event codes
- Driver-specific headers: `zephyr/dt-bindings/gpio/<vendor>-gpio.h`

---

## Summary Table

| Component | Compatible | Purpose | Key Properties |
|-----------|-----------|---------|-----------------|
| GPIO Controller | Device-specific (e.g., `st,stm32-gpio`) | Manages GPIO pins | `gpio-controller`, `#gpio-cells`, `ngpios` |
| GPIO Hog | `gpio-hog` (child of controller) | Auto-configure GPIO at boot | `gpios`, `input`/`output-high`/`output-low` |
| GPIO Keys | `gpio-keys` | Button/switch input device | `debounce-interval-ms`, child `gpios`, `zephyr,code` |
| GPIO LEDs | `gpio-leds` | LED output device | Child nodes with `gpios` |
| GPIO Nexus | `gpio-nexus` | GPIO mapping/redirection | `gpio-map`, `#gpio-cells` |

---

**Document Generated**: From Zephyr RTOS devicetree bindings
**Sources**:
- `dts/bindings/gpio/gpio-controller.yaml`
- `dts/bindings/gpio/gpio-nexus.yaml`
- `dts/bindings/input/gpio-keys.yaml`
- `dts/bindings/led/gpio-leds.yaml`
- `include/zephyr/dt-bindings/gpio/gpio.h`
