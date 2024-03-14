from __future__ import annotations
import arcade
import collisions
import constants
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from classes.lander import Lander
    import pyglet.media as media

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


def get_speed(sound_position: tuple[float, float], sound_velocity: tuple[float, float], speed: float | None = None) -> float:
    """Speed (or pitch) of sound.  1 is default, 2 is octave higher, 0.5 is octave lower, can't have 0.
      Idea here is to apply a doppler affect.  Need positions and velocities"""
    # on looped sounds, I might want to vary the speed to apply a doppler effect.  But for one off sounds,
    # the object itself sometimes knows the speed we want to play the sound at
    if speed is not None:
        return speed
    return 1


def play_or_update_sound(*, delta_time: None | float = None,
                         sound: arcade.Sound,
                         player: media.player,
                         loop: bool = False,
                         obj):
    # This is for when I want to do funky things with sounds - eg. update their pitch / volume as they are playing
    # (by stopping the sound, adjusting the attribute, and restarting at that point).
    # If we just want to play a one of sound (eg. teleport complete), easier to use arcade.play_sound()

    if (not player  # First time sound has played
            # If I wait for a loop-able sound to finish before repeating, it sounds very bitty
            # The line below is so it repeats without a gap - messy, but seems necessary?  \@/

            # The line below is what's causing the "media.Source._players.remove(player) ValueError: list.remove(x): x not in list" bug
            # I play a new sound whilst the old one is still going, but we've lost the reference to the old one, I think.
            or loop and sound.get_stream_position(player) > sound.get_length() - 5 * delta_time):
        player = arcade.play_sound(sound,
                                   volume=obj.max_volume * get_volume_multiplier(obj.position),
                                   pan=get_pan(obj.position),
                                   speed=get_speed(obj.position, (obj.velocity_x, obj.velocity_y),
                                                   getattr(obj, "sound_speed", None)))
    # Testing the below out - the pan effect only works if we regularly update it.
    # So I'm testing out updating attributes every obj.sound_attributes_update_interval ...
    elif player and sound.is_playing(player) and obj.sound_timer > obj.sound_attributes_update_interval:
        obj.sound_timer = 0
        pos = sound.get_stream_position(player)
        sound.stop(player)
        player = arcade.play_sound(sound,
                                   volume=obj.max_volume * get_volume_multiplier(obj.position),
                                   pan=get_pan(obj.position),
                                   speed=get_speed(obj.position, (obj.velocity_x, obj.velocity_y)))
        player.seek(pos)
    return player
