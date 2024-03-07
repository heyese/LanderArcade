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
    # I can't adjust the pan of a sound mid-sound.  I think this probably makes in not very useful
    # for continuous noises that last several seconds that I play on a loop (eg. an engine).
    # Something can cross the screen and it's pan might only get updated a few times
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


def play_or_update_sound(*, delta_time: float, sound: arcade.Sound, loop: bool = False, obj):

    # We don't play a sound WHEN the engine in activated specifically, as it plays continuously,
    # so it's triggered by on_update()
    mp = obj.media_player
    if (not mp
            # Line below is so it repeats without a gap - messy, but seems necessary?  \@/
            or (pos := sound.get_stream_position(mp)) > sound.get_length() - 5 * delta_time and loop):
        obj.media_player = arcade.play_sound(sound,
                                             volume=obj.max_volume * get_volume_multiplier(obj.position),
                                             pan=get_pan(obj.position),
                                             speed=get_speed(obj.position, (obj.velocity_x, obj.velocity_y)))
    # Testing the below out - the pan effect only works if we regularly update it.
    # So I'm testing out updating attributes every obj.sound_attributes_update_interval ...
    elif mp and sound.is_playing(mp) and obj.sound_timer > obj.sound_attributes_update_interval:
        obj.sound_timer = 0
        pos = sound.get_stream_position(mp)
        sound.stop(mp)
        obj.media_player = arcade.play_sound(sound,
                                             volume=obj.max_volume * get_volume_multiplier(obj.position),
                                             pan=get_pan(obj.position),
                                             speed=get_speed(obj.position, (obj.velocity_x, obj.velocity_y)))
        obj.media_player.seek(pos)
