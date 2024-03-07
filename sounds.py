from __future__ import annotations
import arcade
import collisions
import constants
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from classes.lander import Lander

# Generally speaking, the functions here will depend on the lander - it's velocity and position.
# I don't want to have to keep on passing it in to all the functions, so I set it in game.py as soon
# as its created.  Doesn't feel quite right, though ...
GAME_OBJECTS = constants.GAME_OBJECTS


def get_lander_and_camera():
    lander: Lander = constants.GAME_OBJECTS["lander"]
    camera: arcade.Camera = constants.GAME_OBJECTS["camera"]
    return lander, camera


def get_pan(position):
    """Pan (-1 is fully left, 0 is centre, 1 is fully right) of sound as
    determined by relative positions of sound and lander"""
    lander, camera = get_lander_and_camera()
    if not lander and camera:
        return 0
    # This just depends on position.X, not the Y values
    # I suddenly kind of wonder if, when an object is on the left, we should pan fully on the left.  And the same
    # for the right.  In the 2D sense, that feels appropriate - but I don't think it's what I want.
    # I think I want it to be fully on the left, and then gradually change to zero when they have the same x coordinates,
    # and then pan to the right.
    pan = min(max(-1, (position[0] - lander.center_x) / camera.viewport_width), 1)
    return pan


def get_volume_multiplier(position: tuple[float, float]) -> float:
    """Volume (0 silent, 1 full) of sound as determined by relative positions of sound and lander."""
    # I think I want to be able to set the max volume of a sound on the object itself, so it's easy to tweek
    # the volume of individual sounds.  This functions should just turn that up and down depending on where the lander is
    # I think the idea will be that you can't hear objects greater than a screen's width from the lander, and the
    # volume increases as it gets closer
    lander, camera = get_lander_and_camera()
    if not lander and camera:
        return 1
    # Don't need to worry about world wrapping here, because the game ensures sprites are always on the side of the lander
    distance = collisions.modulus((lander.center_x - position[0], lander.center_y - position[1]))
    if distance > camera.viewport_width:
        return 0
    # Gets louder as it gets closer.  Like having a circle of radius camera.viewport_width centred on the lander
    return 1 - distance / camera.viewport_width


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
