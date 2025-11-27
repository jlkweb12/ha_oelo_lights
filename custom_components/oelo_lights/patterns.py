"""Preset pattern definitions for Oelo Lights."""
from typing import NamedTuple


class PatternConfig(NamedTuple):
    """Configuration for a preset pattern."""
    pattern_type: str
    colors: list[tuple[int, int, int]]
    speed: int = 0
    gap: int = 0
    direction: str = "F"


# Preset patterns with their configurations
PRESET_PATTERNS: dict[str, PatternConfig] = {
    "Solid White": PatternConfig(
        pattern_type="custom",
        colors=[(255, 255, 255)],
        speed=0,
    ),
    "Candy Cane": PatternConfig(
        pattern_type="custom",
        colors=[(255, 0, 0), (255, 255, 255)],
        speed=3,
    ),
    "July 4th": PatternConfig(
        pattern_type="custom",
        colors=[(255, 0, 0), (255, 255, 255), (0, 0, 255)],
        speed=3,
    ),
    "Christmas": PatternConfig(
        pattern_type="custom",
        colors=[(255, 0, 0), (0, 255, 0)],
        speed=3,
    ),
    "Halloween": PatternConfig(
        pattern_type="custom",
        colors=[(255, 100, 0), (128, 0, 128)],
        speed=3,
    ),
}


def get_preset_names() -> list[str]:
    """Return list of available preset names."""
    return list(PRESET_PATTERNS.keys())


def get_preset(name: str) -> PatternConfig | None:
    """Get a preset pattern by name."""
    return PRESET_PATTERNS.get(name)