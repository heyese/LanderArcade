import arcade
from typing import NamedTuple

# Constants
SCREEN_TITLE = "Lander Arcade"
SCALING = 1.0
WORLD_WIDTH = 20000
WORLD_HEIGHT = 2500
SPACE_END = int((5 / 6) * WORLD_HEIGHT)
SPACE_START = int((2/3) * WORLD_HEIGHT)
BACKGROUND_COLOR = arcade.color.BLACK


class Levels(NamedTuple):
    hostages: int
    missile_launchers: int
    fuel: int
    shield: int
    max_gravity: int

# With hostages and missile lauchers, I'm saying 'up to' these values
# There might not be enough space to place them all on the terrain
level_1 = Levels(hostages=0, missile_launchers=0, fuel=200, shield=200, max_gravity=50)
level_2 = Levels(hostages=1, missile_launchers=0, fuel=200, shield=200, max_gravity=70)
level_3 = Levels(hostages=2, missile_launchers=2, fuel=150, shield=150, max_gravity=100)
level_4 = Levels(hostages=3, missile_launchers=2, fuel=150, shield=150, max_gravity=140)
level_5 = Levels(hostages=3, missile_launchers=5, fuel=150, shield=150, max_gravity=190)
level_6 = Levels(hostages=3, missile_launchers=10, fuel=100, shield=100, max_gravity=200)  # 200 is max gravity
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
    return LEVELS[max(i for i in LEVELS)]
