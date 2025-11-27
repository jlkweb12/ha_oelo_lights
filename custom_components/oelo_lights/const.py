"""Constants for the Oelo Lights integration."""
from datetime import timedelta

DOMAIN = "oelo_lights"

# Polling and timing
SCAN_INTERVAL = timedelta(seconds=30)
DEFAULT_TIMEOUT = 10  # seconds
DEBOUNCE_INTERVAL = 1.0  # seconds

# Storage
STORAGE_VERSION = 1
STORAGE_KEY_BASE = f"{DOMAIN}_entity_data"

# Light defaults
DEFAULT_BRIGHTNESS = 255
DEFAULT_COLOR = (255, 255, 255)
MAX_COLORS = 20
NUM_ZONES = 6

# Pattern types
PATTERN_TYPE_CUSTOM = "custom"
PATTERN_TYPE_OFF = "off"
VALID_PATTERN_TYPES = ["custom", "chase", "scroll", "bounce", "spread", "wave"]

# Service modes
MODE_PRESET = "Preset"
MODE_CUSTOM = "Custom"