# Oelo Lights Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![version](https://img.shields.io/badge/version-1.1.0-blue)](https://github.com/jlkweb12/ha_oelo_lights)
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
| `target` | Entity | **Yes** | Target Oelo light entity (e.g., `light.oelo_lights_192_168_30_18_zone_1`). |
| `mode` | Select | **Yes** | `Preset` or `Custom`. |
| `target_zones` | List | No | Override zones to control (e.g., `["1", "2"]`). If omitted, uses the target entity's zone. |
| `preset_name` | String | No | **(Mode: Preset)** Name of the preset (see available presets below). |
| `colors` | List | No | **(Mode: Custom)** List of RGB colors (e.g., `[[255,0,0], [0,255,0]]`). Max 20. |
| `custom_pattern_type` | String | No | **(Mode: Custom)** Motion type (see available motions below). Default: `stationary`. |
| `speed` | Number | No | Speed of effect (0-20). Default: 1. |
| `gap` | Number | No | Spacing between lit LEDs (0-20). Default: 0. |

### Available Motions (for Custom mode)

| Motion | Description |
| :--- | :--- |
| `stationary` | Static, no movement |
| `arcade` | Arcade-style animation |
| `blend` | Smooth color blending |
| `bolt` | Lightning bolt effect |
| `chase` | Colors chase each other |
| `fade` | Fade in/out effect |
| `fill` | Fill animation |
| `lightning` | Lightning flash effect |
| `march` | Marching colors |
| `river` | Flowing river effect |
| `shuffle` | Random shuffle |
| `split` | Split from center |
| `sprinkle` | Sprinkle effect |
| `streak` | Streaking lights |
| `storm` | Storm effect |
| `takeover` | Color takeover |
| `twinkle` | Twinkling lights |

### Available Presets

<details>
<summary><b>Solid Colors (10)</b></summary>

- Solid Color: White
- Solid Color: Red
- Solid Color: Green
- Solid Color: Blue
- Solid Color: Yellow
- Solid Color: Orange
- Solid Color: Purple
- Solid Color: Pink
- Solid Color: Cyan
- Solid Color: Warm White
</details>

<details>
<summary><b>American Liberty (2)</b></summary>

- American Liberty: Marching with Red White and Blue
- American Liberty: Standing with Red White and Blue
</details>

<details>
<summary><b>Birthdays (2)</b></summary>

- Birthdays: Birthday Cake
- Birthdays: Birthday Confetti
</details>

<details>
<summary><b>Canadian Strong (1)</b></summary>

- Canadian Strong: O Canada
</details>

<details>
<summary><b>Christmas (11)</b></summary>

- Christmas: Candy Cane Glimmer
- Christmas: Candy Cane Lane
- Christmas: Christmas Glow
- Christmas: Christmas at Oelo
- Christmas: Decorating the Christmas Tree
- Christmas: Dreaming of a White Christmas
- Christmas: Icicle Chase
- Christmas: Icicle Shimmer
- Christmas: Icicle Stream
- Christmas: Saturnalia Christmas
- Christmas: The Grinch Stole Christmas
</details>

<details>
<summary><b>Cinco De Mayo (3)</b></summary>

- Cinco De Mayo: Furious Fiesta
- Cinco De Mayo: Mexican Spirit
- Cinco De Mayo: Salsa Line
</details>

<details>
<summary><b>Day of the Dead (4)</b></summary>

- Day of the Dead: Calaveras Dash
- Day of the Dead: Calaveras Shimmer
- Day of the Dead: Marigold Breeze
- Day of the Dead: Sugar Skull Still
</details>

<details>
<summary><b>Easter (2)</b></summary>

- Easter: Delicate Dance
- Easter: Pastel Unwind
</details>

<details>
<summary><b>Election Day (2)</b></summary>

- Election Day: A More Perfect Union
- Election Day: We The People
</details>

<details>
<summary><b>Fathers Day (2)</b></summary>

- Fathers Day: Fresh Cut Grass
- Fathers Day: Grilling Time
</details>

<details>
<summary><b>Fourth of July (2)</b></summary>

- Fourth of July: Fast Fireworks
- Fourth of July: Founders Endurance
</details>

<details>
<summary><b>Halloween (7)</b></summary>

- Halloween: Candy Corn Glow
- Halloween: Goblin Delight
- Halloween: Goblin Delight Trance
- Halloween: Halloween Dancing Bash
- Halloween: Hocus Pocus
- Halloween: Hocus Pocus Takeover
- Halloween: Pumpkin Patch
</details>

<details>
<summary><b>Hanukkah (2)</b></summary>

- Hanukkah: Eight Days Of Lights
- Hanukkah: Hanukkah Glide
</details>

<details>
<summary><b>Labor Day (2)</b></summary>

- Labor Day: Continued Progress
- Labor Day: United Strong
</details>

<details>
<summary><b>Memorial Day (2)</b></summary>

- Memorial Day: In Honor Of Service
- Memorial Day: Unity Of Service
</details>

<details>
<summary><b>Mothers Day (3)</b></summary>

- Mothers Day: Breakfast In Bed
- Mothers Day: Love For A Mother
- Mothers Day: Twinkling Memories
</details>

<details>
<summary><b>New Years (4)</b></summary>

- New Years: Golden Shine
- New Years: River of Gold
- New Years: Sliding Into the New Year
- New Years: Year of Change
</details>

<details>
<summary><b>Presidents Day (2)</b></summary>

- Presidents Day: Flight Of The President
- Presidents Day: The Presidents March
</details>

<details>
<summary><b>Pride (1)</b></summary>

- Pride: Split
</details>

<details>
<summary><b>Quinceanera (3)</b></summary>

- Quinceanera: Perfectly Pink
- Quinceanera: Twinkle Eyes
- Quinceanera: Vibrant Celebration
</details>

<details>
<summary><b>St. Patricks Day (2)</b></summary>

- St. Patricks Day: Follow The Rainbow
- St. Patricks Day: Sprinkle Of Dust
</details>

<details>
<summary><b>Thanksgiving (2)</b></summary>

- Thanksgiving: Thanksgiving Apple Pie
- Thanksgiving: Thanksgiving Turkey
</details>

<details>
<summary><b>Valentines (4)</b></summary>

- Valentines: Adorations Smile
- Valentines: Cupids Twinkle
- Valentines: My Heart Is Yours
- Valentines: Powerful Love
</details>

---

## Automation Examples

### 1. Trigger a Preset (Christmas Icicle Chase)

```yaml
action: oelo_lights.control_lights
target:
  entity_id: light.oelo_lights_192_168_30_18_zone_1
data:
  mode: Preset
  preset_name: "Christmas: Icicle Chase"
```

### 2. Custom Chase Pattern on Multiple Zones

```yaml
action: oelo_lights.control_lights
target:
  entity_id:
    - light.oelo_lights_192_168_30_18_zone_1
    - light.oelo_lights_192_168_30_18_zone_2
data:
  mode: Custom
  custom_pattern_type: chase
  speed: 9
  gap: 5
  colors:
    - - 255
      - 0
      - 0
    - - 255
      - 127
      - 0
  target_zones:
    - "1"
    - "2"
```

### 3. Custom Rainbow March

```yaml
action: oelo_lights.control_lights
target:
  entity_id: light.oelo_lights_192_168_30_18_zone_1
data:
  mode: Custom
  custom_pattern_type: march
  speed: 5
  gap: 0
  colors:
    - [255, 0, 0]
    - [255, 127, 0]
    - [255, 255, 0]
    - [0, 255, 0]
    - [0, 0, 255]
    - [148, 0, 211]
```

### 4. Simple Color Control
Set a zone to solid blue using standard light service.

```yaml
action: light.turn_on
target:
  entity_id: light.oelo_lights_192_168_30_18_zone_1
data:
  rgb_color: [0, 0, 255]
  brightness: 200
```

### 5. Turn Off All Zones

```yaml
action: light.turn_off
target:
  entity_id:
    - light.oelo_lights_192_168_30_18_zone_1
    - light.oelo_lights_192_168_30_18_zone_2
    - light.oelo_lights_192_168_30_18_zone_3
    - light.oelo_lights_192_168_30_18_zone_4
    - light.oelo_lights_192_168_30_18_zone_5
    - light.oelo_lights_192_168_30_18_zone_6
```

### 6. Scheduled Holiday Theme

```yaml
automation:
  - alias: "Christmas Lights at Sunset"
    trigger:
      - platform: sun
        event: sunset
    action:
      - action: oelo_lights.control_lights
        target:
          entity_id: light.oelo_lights_192_168_30_18_zone_1
        data:
          mode: Preset
          preset_name: "Christmas: Candy Cane Lane"
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
