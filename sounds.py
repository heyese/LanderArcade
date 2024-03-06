from __future__ import annotations
import arcade
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from classes.lander import Lander

# Generally speaking, the functions here will depend on the lander - it's velocity and position.
# I don't want to have to keep on passing it in to all the functions, so I set it in game.py as soon
# as its created.  Doesn't feel quite right, though ...
lander: Lander | None = None


def get_pan(sound_position):
    """Pan (-1 is fully left, 0 is centre, 1 is fully right) of sound as
    determined by relative positions of sound and lander"""
    return 0


def get_volume_multiplier(sound_position):
    """Volume (0 silent, 1 full) of sound as determined by relative positions of sound and lander."""
    return 1


def get_speed(sound_position: tuple[float, float], sound_velocity: tuple[float, float]):
    """Speed (or pitch) of sound.  1 is default, 2 is octave higher, 0.5 is octave lower, can't have 0.
      Idea here is to apply a doppler affect.  Need positions and velocities"""
    return 1


def play_sound(sound_enabled: bool,
               sound: arcade.Sound,
               *,
               volume: float = 1.0,
               pan: float = 0.0,
               looping: bool = False,
               speed: float = 1.0, ):
    if sound_enabled:
        return arcade.play_sound(sound,
                                 volume=volume,
                                 pan=pan,
                                 looping=looping,
                                 speed=speed)
    return None
