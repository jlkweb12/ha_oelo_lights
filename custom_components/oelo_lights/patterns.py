"""Preset pattern definitions for Oelo Lights."""
from typing import NamedTuple


class PatternConfig(NamedTuple):
    """Configuration for a preset pattern."""
    pattern_type: str
    colors: list[tuple[int, int, int]]
    speed: int = 0
    gap: int = 0
    direction: str = "R"


# Preset patterns with their configurations
PRESET_PATTERNS: dict[str, PatternConfig] = {
    # Solid Colors
    "Solid Color: White": PatternConfig(
        pattern_type="stationary",
        colors=[(255, 255, 255)],
        speed=0,
    ),
    "Solid Color: Red": PatternConfig(
        pattern_type="stationary",
        colors=[(255, 0, 0)],
        speed=0,
    ),
    "Solid Color: Green": PatternConfig(
        pattern_type="stationary",
        colors=[(0, 255, 0)],
        speed=0,
    ),
    "Solid Color: Blue": PatternConfig(
        pattern_type="stationary",
        colors=[(0, 0, 255)],
        speed=0,
    ),
    "Solid Color: Yellow": PatternConfig(
        pattern_type="stationary",
        colors=[(255, 255, 0)],
        speed=0,
    ),
    "Solid Color: Orange": PatternConfig(
        pattern_type="stationary",
        colors=[(255, 165, 0)],
        speed=0,
    ),
    "Solid Color: Purple": PatternConfig(
        pattern_type="stationary",
        colors=[(128, 0, 255)],
        speed=0,
    ),
    "Solid Color: Pink": PatternConfig(
        pattern_type="stationary",
        colors=[(255, 105, 180)],
        speed=0,
    ),
    "Solid Color: Cyan": PatternConfig(
        pattern_type="stationary",
        colors=[(0, 255, 255)],
        speed=0,
    ),
    "Solid Color: Warm White": PatternConfig(
        pattern_type="stationary",
        colors=[(255, 244, 229)],
        speed=0,
    ),
    # American Liberty
    "American Liberty: Marching with Red White and Blue": PatternConfig(
        pattern_type="march",
        colors=[(255, 255, 255), (0, 0, 255), (0, 0, 255), (255, 255, 255), (255, 0, 0), (255, 0, 0)],
        speed=1,
    ),
    "American Liberty: Standing with Red White and Blue": PatternConfig(
        pattern_type="stationary",
        colors=[(255, 255, 255), (0, 0, 255), (0, 0, 255), (255, 255, 255), (255, 0, 0), (255, 0, 0)],
        speed=10,
    ),
    # Birthdays
    "Birthdays: Birthday Cake": PatternConfig(
        pattern_type="stationary",
        colors=[(255, 0, 0), (255, 255, 255), (255, 92, 0), (255, 255, 255), (255, 184, 0), (255, 255, 255), (97, 255, 0), (255, 255, 255), (0, 10, 255), (255, 255, 255), (189, 0, 255), (255, 255, 255), (255, 0, 199), (255, 255, 255)],
        speed=20,
    ),
    "Birthdays: Birthday Confetti": PatternConfig(
        pattern_type="river",
        colors=[(255, 0, 0), (255, 255, 255), (255, 92, 0), (255, 255, 255), (255, 184, 0), (255, 255, 255), (97, 255, 0), (255, 255, 255), (0, 10, 255), (255, 255, 255), (189, 0, 255), (255, 255, 255), (255, 0, 199), (255, 255, 255)],
        speed=20,
    ),
    # Canadian Strong
    "Canadian Strong: O Canada": PatternConfig(
        pattern_type="stationary",
        colors=[(237, 252, 255), (237, 252, 255), (237, 252, 255), (255, 0, 0), (255, 0, 0), (255, 255, 255), (255, 0, 0), (255, 0, 0)],
        speed=20,
    ),
    # Christmas
    "Christmas: Candy Cane Glimmer": PatternConfig(
        pattern_type="river",
        colors=[(255, 255, 255), (255, 0, 0), (255, 255, 255), (255, 0, 0)],
        speed=20,
    ),
    "Christmas: Candy Cane Lane": PatternConfig(
        pattern_type="stationary",
        colors=[(255, 255, 255), (255, 255, 255), (255, 255, 255), (255, 0, 0), (255, 0, 0), (255, 0, 0)],
        speed=4,
    ),
    "Christmas: Christmas Glow": PatternConfig(
        pattern_type="stationary",
        colors=[(255, 255, 255), (255, 255, 255), (255, 255, 255), (255, 153, 0), (255, 153, 0), (255, 153, 0)],
        speed=2,
    ),
    "Christmas: Christmas at Oelo": PatternConfig(
        pattern_type="stationary",
        colors=[(26, 213, 255), (26, 213, 255), (26, 213, 255), (26, 213, 255), (26, 213, 255), (255, 34, 0), (255, 34, 0)],
        speed=2,
    ),
    "Christmas: Decorating the Christmas Tree": PatternConfig(
        pattern_type="stationary",
        colors=[(0, 219, 11), (0, 219, 11), (0, 219, 11), (255, 153, 0), (255, 255, 255)],
        speed=2,
    ),
    "Christmas: Dreaming of a White Christmas": PatternConfig(
        pattern_type="stationary",
        colors=[(238, 252, 255), (237, 252, 255), (237, 252, 255), (0, 0, 0), (0, 0, 0)],
        speed=10,
    ),
    "Christmas: Icicle Chase": PatternConfig(
        pattern_type="chase",
        colors=[(255, 255, 255), (0, 183, 245), (0, 73, 245)],
        speed=5,
    ),
    "Christmas: Icicle Shimmer": PatternConfig(
        pattern_type="twinkle",
        colors=[(255, 255, 255), (0, 204, 255), (0, 70, 255), (0, 70, 255)],
        speed=4,
    ),
    "Christmas: Icicle Stream": PatternConfig(
        pattern_type="river",
        colors=[(255, 255, 255), (0, 204, 255), (0, 70, 255), (0, 70, 255)],
        speed=4,
    ),
    "Christmas: Saturnalia Christmas": PatternConfig(
        pattern_type="stationary",
        colors=[(255, 255, 255), (255, 255, 255), (255, 255, 255), (0, 255, 47), (0, 255, 47), (0, 255, 47), (255, 0, 0), (255, 0, 0), (255, 0, 0)],
        speed=2,
    ),
    "Christmas: The Grinch Stole Christmas": PatternConfig(
        pattern_type="twinkle",
        colors=[(15, 255, 0), (15, 255, 0), (15, 255, 0), (15, 255, 0), (255, 0, 0), (255, 0, 0), (255, 255, 255), (255, 255, 255)],
        speed=2,
    ),
    # Cinco De Mayo
    "Cinco De Mayo: Furious Fiesta": PatternConfig(
        pattern_type="twinkle",
        colors=[(255, 0, 0), (255, 0, 0), (255, 0, 0), (255, 255, 255), (255, 255, 255), (255, 255, 255), (0, 255, 0), (0, 255, 0), (0, 255, 0)],
        speed=10,
    ),
    "Cinco De Mayo: Mexican Spirit": PatternConfig(
        pattern_type="stationary",
        colors=[(255, 0, 0), (255, 0, 0), (255, 0, 0), (255, 255, 255), (255, 255, 255), (255, 255, 255), (0, 255, 0), (0, 255, 0), (0, 255, 0)],
        speed=1,
    ),
    "Cinco De Mayo: Salsa Line": PatternConfig(
        pattern_type="march",
        colors=[(255, 0, 0), (255, 0, 0), (255, 0, 0), (255, 255, 255), (255, 255, 255), (255, 255, 255), (0, 255, 0), (0, 255, 0), (0, 255, 0)],
        speed=5,
    ),
    # Day of the Dead
    "Day of the Dead: Calaveras Dash": PatternConfig(
        pattern_type="twinkle",
        colors=[(77, 248, 255), (255, 77, 209), (41, 144, 255), (255, 246, 41)],
        speed=4,
    ),
    "Day of the Dead: Calaveras Shimmer": PatternConfig(
        pattern_type="twinkle",
        colors=[(40, 255, 200), (255, 40, 200), (40, 120, 255), (255, 246, 40)],
        speed=1,
    ),
    "Day of the Dead: Marigold Breeze": PatternConfig(
        pattern_type="river",
        colors=[(255, 138, 0), (255, 138, 0), (255, 34, 0), (255, 34, 0)],
        speed=4,
    ),
    "Day of the Dead: Sugar Skull Still": PatternConfig(
        pattern_type="stationary",
        colors=[(255, 255, 255), (255, 255, 255), (225, 0, 250), (255, 255, 255), (255, 255, 255), (5, 180, 255), (255, 255, 255), (255, 255, 255), (255, 142, 0)],
        speed=1,
    ),
    # Easter
    "Easter: Delicate Dance": PatternConfig(
        pattern_type="march",
        colors=[(213, 50, 255), (213, 50, 255), (213, 50, 255), (50, 255, 184), (50, 255, 184), (50, 255, 184), (255, 149, 50), (255, 149, 50), (255, 149, 50)],
        speed=1,
    ),
    "Easter: Pastel Unwind": PatternConfig(
        pattern_type="stationary",
        colors=[(144, 50, 255), (144, 50, 255), (144, 50, 255), (213, 50, 255), (213, 50, 255), (213, 50, 255), (80, 205, 255), (80, 205, 255), (80, 205, 255)],
        speed=1,
    ),
    # Election Day
    "Election Day: A More Perfect Union": PatternConfig(
        pattern_type="split",
        colors=[(255, 0, 0), (255, 0, 0), (255, 0, 0), (0, 4, 255), (0, 39, 255), (0, 39, 255), (255, 255, 255), (255, 255, 255), (255, 255, 255)],
        speed=1,
    ),
    "Election Day: We The People": PatternConfig(
        pattern_type="march",
        colors=[(255, 0, 0), (255, 0, 0), (255, 0, 0), (0, 0, 255), (0, 0, 255), (0, 0, 255), (255, 255, 255), (255, 255, 255), (255, 255, 255)],
        speed=1,
    ),
    # Fathers Day
    "Fathers Day: Fresh Cut Grass": PatternConfig(
        pattern_type="sprinkle",
        colors=[(7, 82, 0)],
        speed=1,
        gap=1,
    ),
    "Fathers Day: Grilling Time": PatternConfig(
        pattern_type="takeover",
        colors=[(0, 0, 255), (0, 0, 255), (0, 0, 255), (255, 255, 255), (255, 255, 255), (255, 255, 255)],
        speed=1,
    ),
    # Fourth of July
    "Fourth of July: Fast Fireworks": PatternConfig(
        pattern_type="twinkle",
        colors=[(255, 255, 255), (0, 0, 255), (0, 0, 255), (255, 255, 255), (255, 0, 0), (255, 0, 0)],
        speed=10,
    ),
    "Fourth of July: Founders Endurance": PatternConfig(
        pattern_type="split",
        colors=[(255, 0, 0), (0, 39, 255), (255, 255, 255)],
        speed=1,
    ),
    # Halloween
    "Halloween: Candy Corn Glow": PatternConfig(
        pattern_type="march",
        colors=[(255, 215, 0), (255, 155, 0), (255, 64, 0), (255, 54, 0), (255, 74, 0), (255, 255, 255)],
        speed=3,
    ),
    "Halloween: Goblin Delight": PatternConfig(
        pattern_type="takeover",
        colors=[(176, 0, 255), (176, 0, 255), (176, 0, 255), (53, 255, 0), (53, 255, 0), (53, 255, 0)],
        speed=1,
    ),
    "Halloween: Goblin Delight Trance": PatternConfig(
        pattern_type="streak",
        colors=[(176, 0, 255), (176, 0, 255), (176, 0, 255), (53, 255, 0), (53, 255, 0), (53, 255, 0)],
        speed=3,
    ),
    "Halloween: Halloween Dancing Bash": PatternConfig(
        pattern_type="twinkle",
        colors=[(255, 155, 0), (240, 81, 0), (255, 155, 0)],
        speed=3,
    ),
    "Halloween: Hocus Pocus": PatternConfig(
        pattern_type="stationary",
        colors=[(176, 0, 255), (176, 0, 255), (176, 0, 255), (255, 85, 0), (255, 85, 0), (255, 85, 0)],
        speed=3,
    ),
    "Halloween: Hocus Pocus Takeover": PatternConfig(
        pattern_type="takeover",
        colors=[(176, 0, 255), (176, 0, 255), (176, 0, 255), (255, 85, 0), (255, 85, 0), (255, 85, 0)],
        speed=3,
    ),
    "Halloween: Pumpkin Patch": PatternConfig(
        pattern_type="stationary",
        colors=[(255, 54, 0), (255, 64, 0), (0, 28, 2), (0, 0, 0)],
        speed=3,
    ),
    # Hanukkah
    "Hanukkah: Eight Days Of Lights": PatternConfig(
        pattern_type="stationary",
        colors=[(255, 255, 255), (255, 255, 255), (255, 255, 255), (0, 0, 255), (0, 0, 255), (0, 0, 255)],
        speed=1,
    ),
    "Hanukkah: Hanukkah Glide": PatternConfig(
        pattern_type="river",
        colors=[(255, 255, 255), (0, 0, 255), (0, 0, 255), (255, 255, 255)],
        speed=4,
    ),
    # Labor Day
    "Labor Day: Continued Progress": PatternConfig(
        pattern_type="bolt",
        colors=[(255, 0, 0), (255, 0, 0), (255, 0, 0), (0, 0, 255), (0, 0, 255), (0, 0, 255), (255, 255, 255), (255, 255, 255), (255, 255, 255)],
        speed=1,
    ),
    "Labor Day: United Strong": PatternConfig(
        pattern_type="fade",
        colors=[(255, 0, 0), (0, 0, 0), (255, 255, 255), (0, 0, 0), (0, 0, 255), (0, 0, 0)],
        speed=8,
    ),
    # Memorial Day
    "Memorial Day: In Honor Of Service": PatternConfig(
        pattern_type="stationary",
        colors=[(255, 0, 0), (255, 0, 0), (255, 0, 0), (0, 0, 255), (0, 0, 255), (0, 0, 255), (255, 255, 255), (255, 255, 255), (255, 255, 255)],
        speed=1,
    ),
    "Memorial Day: Unity Of Service": PatternConfig(
        pattern_type="takeover",
        colors=[(255, 0, 0), (0, 0, 255), (255, 255, 255)],
        speed=1,
    ),
    # Mothers Day
    "Mothers Day: Breakfast In Bed": PatternConfig(
        pattern_type="stationary",
        colors=[(100, 20, 255), (100, 20, 255), (100, 20, 255), (230, 20, 255), (230, 20, 255), (230, 20, 255), (20, 205, 255), (20, 205, 255), (20, 205, 255)],
        speed=1,
    ),
    "Mothers Day: Love For A Mother": PatternConfig(
        pattern_type="stationary",
        colors=[(180, 10, 255), (255, 0, 0)],
        speed=1,
    ),
    "Mothers Day: Twinkling Memories": PatternConfig(
        pattern_type="twinkle",
        colors=[(255, 10, 228), (255, 255, 255)],
        speed=1,
    ),
    # New Years
    "New Years: Golden Shine": PatternConfig(
        pattern_type="twinkle",
        colors=[(255, 255, 255), (255, 161, 51)],
        speed=1,
    ),
    "New Years: River of Gold": PatternConfig(
        pattern_type="river",
        colors=[(255, 255, 255), (255, 145, 15), (255, 255, 255), (255, 145, 15), (255, 255, 255), (255, 145, 15)],
        speed=5,
    ),
    "New Years: Sliding Into the New Year": PatternConfig(
        pattern_type="streak",
        colors=[(255, 255, 255), (255, 145, 15)],
        speed=1,
    ),
    "New Years: Year of Change": PatternConfig(
        pattern_type="fade",
        colors=[(255, 255, 255), (255, 145, 15), (255, 145, 15)],
        speed=5,
    ),
    # Presidents Day
    "Presidents Day: Flight Of The President": PatternConfig(
        pattern_type="twinkle",
        colors=[(255, 0, 0), (255, 0, 0), (255, 0, 0), (0, 0, 255), (0, 0, 255), (0, 0, 255), (255, 255, 255), (255, 255, 255), (255, 255, 255)],
        speed=1,
    ),
    "Presidents Day: The Presidents March": PatternConfig(
        pattern_type="march",
        colors=[(255, 0, 0), (255, 0, 0), (255, 0, 0), (0, 0, 255), (0, 0, 255), (0, 0, 255), (255, 255, 255), (255, 255, 255), (255, 255, 255)],
        speed=1,
    ),
    # Pride
    "Pride: Split": PatternConfig(
        pattern_type="split",
        colors=[(255, 0, 0), (255, 50, 0), (255, 240, 0), (0, 255, 0), (0, 0, 255), (125, 0, 255)],
        speed=1,
    ),
    # Quinceanera
    "Quinceanera: Perfectly Pink": PatternConfig(
        pattern_type="twinkle",
        colors=[(255, 61, 183), (255, 46, 228), (255, 10, 164), (255, 46, 149), (255, 46, 228), (255, 46, 129)],
        speed=9,
    ),
    "Quinceanera: Twinkle Eyes": PatternConfig(
        pattern_type="twinkle",
        colors=[(255, 10, 228), (255, 255, 255)],
        speed=1,
    ),
    "Quinceanera: Vibrant Celebration": PatternConfig(
        pattern_type="stationary",
        colors=[(180, 10, 255), (255, 0, 0)],
        speed=1,
    ),
    # St. Patricks Day
    "St. Patricks Day: Follow The Rainbow": PatternConfig(
        pattern_type="split",
        colors=[(255, 0, 5), (255, 50, 0), (255, 230, 0), (63, 255, 0), (0, 136, 255), (100, 0, 255)],
        speed=1,
    ),
    "St. Patricks Day: Sprinkle Of Dust": PatternConfig(
        pattern_type="sprinkle",
        colors=[(97, 255, 0), (173, 255, 0)],
        speed=1,
    ),
    # Thanksgiving
    "Thanksgiving: Thanksgiving Apple Pie": PatternConfig(
        pattern_type="stationary",
        colors=[(255, 31, 0), (255, 31, 0), (255, 31, 0), (255, 94, 0), (255, 94, 0), (255, 94, 0)],
        speed=1,
    ),
    "Thanksgiving: Thanksgiving Turkey": PatternConfig(
        pattern_type="stationary",
        colors=[(255, 94, 0)],
        speed=1,
    ),
    # Valentines
    "Valentines: Adorations Smile": PatternConfig(
        pattern_type="stationary",
        colors=[(255, 10, 228), (255, 0, 76), (255, 143, 238)],
        speed=1,
    ),
    "Valentines: Cupids Twinkle": PatternConfig(
        pattern_type="twinkle",
        colors=[(255, 10, 228), (255, 255, 255)],
        speed=1,
    ),
    "Valentines: My Heart Is Yours": PatternConfig(
        pattern_type="fade",
        colors=[(255, 10, 228), (255, 255, 255), (255, 0, 0)],
        speed=1,
    ),
    "Valentines: Powerful Love": PatternConfig(
        pattern_type="stationary",
        colors=[(180, 10, 255), (255, 0, 0)],
        speed=1,
    ),
}


def get_preset_names() -> list[str]:
    """Return list of available preset names."""
    return list(PRESET_PATTERNS.keys())


def get_preset(name: str) -> PatternConfig | None:
    """Get a preset pattern by name."""
    return PRESET_PATTERNS.get(name)