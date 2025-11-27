# Oelo Lights Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![version](https://img.shields.io/badge/version-1.0.0-blue)](https://github.com/jlkweb12/ha_oelo_lights)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/jlkweb12/ha_oelo_lights/graphs/commit-activity)

A robust Home Assistant integration for **Oelo Permanent Holiday Lights**. This custom component allows for local control of your Oelo lighting system, supporting multi-zone control, premade pattern presets, and highly customizable user-defined patterns.

> **Disclaimer:** This is an **unofficial**, community-developed integration. It is not created, endorsed, or supported by Oelo LLC. This project is maintained independently and is provided "as-is" without warranty. Use at your own risk.

## Features

* **Local Control:** Communicates directly with the Oelo Controller via IP (no cloud required).
* **Multi-Zone Support:** Control up to 6 distinct zones individually or grouped together.
* **Unified Service:** A single powerful service (`oelo_lights.control_lights`) to handle both simple presets and complex custom animations.
* **Custom Patterns:** Create patterns on the fly with up to 20 colors, custom movement types (Chase, Scroll, Bounce, etc.), speed, and light spacing (gap).
* **State Persistence:** Remembers the last successful command per zone across restarts.
* **Debouncing:** Built-in logic to prevent controller overload from rapid automation changes.

---

## Installation

### Option 1: HACS (Recommended)

1. Open **HACS** in Home Assistant.
2. Click the 3 dots in the top right corner and select **Custom repositories**.
3. Add the URL: `https://github.com/jlkweb12/ha_oelo_lights`
4. Select **Integration** as the category.
5. Click **Add** and then install **Oelo Lights Controller**.
6. Restart Home Assistant.

### Option 2: Manual Installation

1. Download the latest release from this repository.
2. Extract the `custom_components/oelo_lights` folder.
3. Copy this folder into your Home Assistant's `config/custom_components/` directory.
4. Restart Home Assistant.

---

## Configuration

1. Navigate to **Settings** > **Devices & Services**.
2. Click **+ Add Integration**.
3. Search for **Oelo Lights**.
4. Enter the **IP Address** of your Oelo Controller (e.g., `192.168.1.50`).
   * *Tip: You can usually find this in your router's client list or the Oelo App settings.*
5. The integration will validate the connection and automatically create entities for Zones 1-6.

---

## Usage

You can control your lights like any standard Home Assistant light entity:
- **On/Off** toggle
- **Brightness** control
- **RGB Color** picker
- **Effects** dropdown (presets)

For advanced control, use the custom service.

### Service: `oelo_lights.control_lights`

This service allows you to trigger built-in presets OR create complex custom patterns on the fly.

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `mode` | Select | **Yes** | `Preset` or `Custom`. |
| `target_zones` | List | No | Which zones to control (e.g., `["1", "2"]`). Defaults to the entity's zone. |
| `preset_name` | String | No | **(Mode: Preset)** Name of the preset (see available presets below). |
| `colors` | List | No | **(Mode: Custom)** List of RGB colors (e.g., `[[255,0,0], [0,255,0]]`). Max 20. |
| `custom_pattern_type` | String | No | **(Mode: Custom)** Movement type: `custom`, `chase`, `scroll`, `bounce`, `spread`, `wave`. Default: `custom`. |
| `speed` | Number | No | Speed of effect (0-100). Default: 1. |
| `gap` | Number | No | Spacing between lit LEDs (0-100). Default: 0. |

### Available Presets

| Preset Name | Description |
| :--- | :--- |
| `Solid White` | Static white lights |
| `Candy Cane` | Red and white alternating |
| `July 4th` | Red, white, and blue patriotic |
| `Christmas` | Red and green holiday |
| `Halloween` | Orange and purple spooky |

---

## Automation Examples

### 1. Trigger a Preset (Candy Cane)
Sets Zone 1 and Zone 2 to the "Candy Cane" preset.

```yaml
action:
  - service: oelo_lights.control_lights
    target:
      entity_id: light.oelo_lights_zone_1
    data:
      mode: "Preset"
      preset_name: "Candy Cane"
      target_zones:
        - "1"
        - "2"
```

### 2. Custom Rainbow Chase
Create a custom rainbow chase effect across all zones.

```yaml
action:
  - service: oelo_lights.control_lights
    target:
      entity_id: light.oelo_lights_zone_1
    data:
      mode: "Custom"
      custom_pattern_type: "chase"
      colors:
        - [255, 0, 0]      # Red
        - [255, 127, 0]    # Orange
        - [255, 255, 0]    # Yellow
        - [0, 255, 0]      # Green
        - [0, 0, 255]      # Blue
        - [148, 0, 211]    # Violet
      speed: 50
      gap: 2
      target_zones:
        - "1"
        - "2"
        - "3"
        - "4"
        - "5"
        - "6"
```

### 3. Simple Color Control
Set a zone to solid blue using standard light service.

```yaml
action:
  - service: light.turn_on
    target:
      entity_id: light.oelo_lights_zone_1
    data:
      rgb_color: [0, 0, 255]
      brightness: 200
```

### 4. Turn Off All Zones

```yaml
action:
  - service: light.turn_off
    target:
      entity_id:
        - light.oelo_lights_zone_1
        - light.oelo_lights_zone_2
        - light.oelo_lights_zone_3
        - light.oelo_lights_zone_4
        - light.oelo_lights_zone_5
        - light.oelo_lights_zone_6
```

### 5. Scheduled Holiday Theme

```yaml
automation:
  - alias: "Christmas Lights at Sunset"
    trigger:
      - platform: sun
        event: sunset
    action:
      - service: oelo_lights.control_lights
        target:
          entity_id: light.oelo_lights_zone_1
        data:
          mode: "Preset"
          preset_name: "Christmas"
          target_zones:
            - "1"
            - "2"
            - "3"
```

---

## Troubleshooting

### Integration won't connect
- Verify the IP address is correct and the controller is powered on.
- Ensure Home Assistant can reach the controller (same network/VLAN).
- Check your router's firewall settings.

### Commands are delayed
- The integration uses debouncing (1 second) to prevent overwhelming the controller.
- Rapid successive commands will be combined.

### State doesn't update
- The integration polls the controller every 30 seconds.
- Use the refresh button on the entity or trigger a manual update.

---

## Support

For bugs or feature requests, please open an issue on [GitHub](https://github.com/jlkweb12/ha_oelo_lights/issues).

---

## License

This project is licensed under the MIT License.

---

## Thank you

This is a fork of https://github.com/Cinegration/Oelo_Lights_HA from @Cinegration.
