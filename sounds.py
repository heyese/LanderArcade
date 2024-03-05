import arcade


def get_pan(sound_position, lander_position):
    """Pan (-1 is fully left, 0 is centre, 1 is fully right) of sound as
    determined by relative positions of sound and lander"""
    pass


def get_volume(sound_position, lander_position):
    """Volume (0 silent, 1 full) of sound as determined by relative positions of sound and lander."""
    pass


def get_speed(sound_object, lander):
    """Speed (or pitch) of sound.  1 is default, 2 is octave higher, 0.5 is octave lower, can't have 0.
      Idea here is to apply a doppler affect.  Need positions and velocities"""
    pass


def play_sound(sound_enabled, *args, **kwargs):
    if sound_enabled:
        return arcade.play_sound(*args, **kwargs)
    return None


