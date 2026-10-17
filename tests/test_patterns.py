"""Tests for the preset pattern definitions.

These guard the contract between `services.yaml` (what the UI offers the user)
and `patterns.py` (what the service can actually resolve). Adding a preset to
one file and forgetting the other produces a service call that silently fails,
so the two lists are asserted to match exactly.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from custom_components.oelo_lights.const import (
    MAX_COLORS,
    VALID_MOTIONS,
    VALID_PATTERN_TYPES,
)
from custom_components.oelo_lights.patterns import (
    PRESET_PATTERNS,
    PatternConfig,
    get_preset,
    get_preset_names,
)

COMPONENT_DIR = Path(__file__).parent.parent / "custom_components" / "oelo_lights"


def _ui_preset_options() -> list[str]:
    """Return the preset names offered by the service UI."""
    services = yaml.safe_load((COMPONENT_DIR / "services.yaml").read_text())
    selector = services["control_lights"]["fields"]["preset_name"]["selector"]
    return selector["select"]["options"]


def test_presets_are_not_empty() -> None:
    """The integration ships at least one preset."""
    assert PRESET_PATTERNS


def test_every_ui_preset_resolves() -> None:
    """Every preset the UI offers must resolve via get_preset()."""
    unresolvable = [name for name in _ui_preset_options() if get_preset(name) is None]
    assert not unresolvable, (
        f"offered in services.yaml but missing from patterns.py: {unresolvable}"
    )


def test_no_unreachable_presets() -> None:
    """Every defined preset must be reachable from the UI."""
    missing = sorted(set(PRESET_PATTERNS) - set(_ui_preset_options()))
    assert not missing, f"defined in patterns.py but not offered in services.yaml: {missing}"


def test_ui_preset_options_are_unique() -> None:
    """A duplicated dropdown entry is a copy/paste slip."""
    options = _ui_preset_options()
    duplicates = sorted({name for name in options if options.count(name) > 1})
    assert not duplicates, f"duplicated in services.yaml: {duplicates}"


def test_get_preset_names_matches_definitions() -> None:
    """get_preset_names() reflects the defined presets."""
    assert sorted(get_preset_names()) == sorted(PRESET_PATTERNS)


def test_get_preset_unknown_returns_none() -> None:
    """An unknown preset name resolves to None rather than raising."""
    assert get_preset("No Such Preset") is None


@pytest.mark.parametrize("name", sorted(PRESET_PATTERNS))
def test_preset_is_well_formed(name: str) -> None:
    """Each preset carries a usable pattern type, colors, speed and gap."""
    preset = PRESET_PATTERNS[name]
    assert isinstance(preset, PatternConfig)

    # PatternConfig.direction is deliberately not asserted: the integration
    # hardcodes direction=F when building commands, so the field is inert.

    assert preset.pattern_type in set(VALID_MOTIONS) | set(VALID_PATTERN_TYPES), (
        f"{name}: unknown pattern_type {preset.pattern_type!r}"
    )

    assert preset.colors, f"{name}: has no colors"
    assert len(preset.colors) <= MAX_COLORS, f"{name}: exceeds MAX_COLORS"

    for rgb in preset.colors:
        assert len(rgb) == 3, f"{name}: {rgb!r} is not a 3-tuple"
        for channel in rgb:
            assert isinstance(channel, int), f"{name}: {rgb!r} has a non-int channel"
            assert 0 <= channel <= 255, f"{name}: {rgb!r} is out of 0-255 range"

    assert 0 <= preset.speed <= 20, f"{name}: speed {preset.speed} out of range"
    assert 0 <= preset.gap <= 20, f"{name}: gap {preset.gap} out of range"
