from __future__ import annotations
import arcade
from typing import NamedTuple
from dataclasses import dataclass
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from classes.lander import Lander


# Constants
SCREEN_TITLE = "Lander Arcade"
SCALING = 1.0
WORLD_WIDTH = 20000
WORLD_HEIGHT = 2500
SPACE_END = int((5 / 7) * WORLD_HEIGHT)
SPACE_START = int((2/3) * WORLD_HEIGHT)
BACKGROUND_COLOR = arcade.color.BLACK

TERRAIN_SPRITELISTS = [
    # Purposefully ordered left to right, for explosion collision logic
    "Terrain Left Edge",
    "Terrain Centre",
    "Terrain Right Edge"
]

GENERAL_OBJECT_SPRITELISTS = [
    "Lander",
    "Shields",
    "Missiles",
    "Air Enemies",
    'Ground Enemies',
]

ALLOWED_TERRAIN_SHIELD_COLLISIONS_SPRITELISTS = ['Landing Pad', 'Hostages', 'Ground Enemies']
PLACE_ON_WORLD_SPRITELISTS = ["Landing Pad", "Ground Enemies", "Hostages"]

# Have to admit this feels wrong, but I often want to easily get a hold of the lander or the game camera
# And it feels weird to have to pass them around absolutely everywhere ...
# So I'm going to see what issues I run into by simply putting them here, and setting them in the constants
# module namespace as soon as they're defined (they get defined for each level in game.py).
GAME_OBJECTS = {
    "lander": None,
    "camera": None
}


@dataclass
class Levels:
    fuel: int = 80
    shield: int = 60
    max_gravity: int = 200  # Values higher than this will need more engine power
    hostages: int = 3
    missile_launchers: int = 0
    shielded_missile_launchers: int = 10
    super_missile_launchers: int = 2


# With hostages and missile lauchers, I'm saying 'up to' these values
# There might not be enough space to place them all on the terrain
level_1 = Levels(hostages=0, fuel=200, shield=200, max_gravity=50, missile_launchers=0, shielded_missile_launchers=0, super_missile_launchers=0)
level_2 = Levels(hostages=1, fuel=200, shield=200, max_gravity=70, missile_launchers=0, shielded_missile_launchers=0, super_missile_launchers=0)
level_3 = Levels(hostages=2, missile_launchers=1, fuel=150, shield=150, max_gravity=100, shielded_missile_launchers=0, super_missile_launchers=0)
level_4 = Levels(missile_launchers=2, fuel=150, shield=150, max_gravity=140, shielded_missile_launchers=0, super_missile_launchers=0)
level_5 = Levels(missile_launchers=4, shielded_missile_launchers=0, super_missile_launchers=1, fuel=150, shield=150, max_gravity=190)
level_6 = Levels(missile_launchers=7, shielded_missile_launchers=0, fuel=100, shield=100)
level_7 = Levels(shielded_missile_launchers=7)
# Future levels just match the latest one

LEVELS = {
    1: level_1,
    2: level_2,
    3: level_3,
    4: level_4,
    5: level_5,
    6: level_6
}


def get_level_config(level: int) -> Levels:
    if level in LEVELS:
        return LEVELS[level]
    # otherwise, return max(i) such that i in LEVELS
    return Levels()
