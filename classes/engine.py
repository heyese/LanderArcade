from __future__ import annotations
import arcade
import math
from constants import SCALING
from pathlib import Path
import sounds
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from classes.game_object import GameObject


class Engine(arcade.Sprite):
    def __init__(self,
                 scene: arcade.Scene,
                 owner: GameObject,
                 fuel: int = 100,
                 force: int = 5000,
                 scale: float = 0.3,
                 engine_owner_offset: int = None,
                 sound_enabled: bool = False):
        super().__init__()
        self.scene = scene
        self.textures = [arcade.load_texture("images/thrust_1.png"),
                         arcade.load_texture("images/thrust_2.png")]
        self.texture = self.textures[0]
        self.owner = owner  # This is the object whose engine this is
        self.visible = False
        # Actual engine attributes (as opposed to sprite attributes)
        self.activated = False
        self.force = force
        self.fuel = fuel
        self.initial_fuel = fuel
        self.scale = scale * SCALING
        self.burn_rate = 1
        self._boosted = False
        self.engine_owner_offset = engine_owner_offset if engine_owner_offset is not None else self.owner.height
        self.scene.add_sprite('Engines', self)

        # Engine sounds
        self.sound_enabled = sound_enabled
        self.engine_activated_sound = arcade.load_sound(Path('sounds/engine.mp3'))
        self.standard_engine_volume = 0.5
        self.boosted_engine_volume = 1
        self.current_engine_volume = self.standard_engine_volume
        self.media_player = None

    def refuel(self):
        self.fuel = self.initial_fuel

    @property
    def boosted(self):
        return self._boosted

    @boosted.setter
    def boosted(self, value: bool):
        self._boosted = value
        if value is True:
            self.burn_rate *= 2
            self.scale *= 1.5
            self.force *= 2
        else:
            self.burn_rate /= 2
            self.scale /= 1.5
            self.force /= 2

    def activate(self):
        if self.fuel:
            self.visible = True
            self.activated = True
            # Are we trying to take off after having landed?
            # Want to ensure we don't just immediately land again
            if self.owner.__class__.__name__ == ('Lander'):
                from classes.lander import Lander
                lander: Lander = self.owner
                if lander.landed:
                    lander.landed = False
                    # Tiny bit of a start so we don't stay in contact with the landing pad
                    # Also requires user to thrust fairly straight upwards, which I think is intuitive.
                    lander.center_y += 5

    def deactivate(self):
        self.visible = False
        self.activated = False

    def boost(self, on: bool):
        if on is True:
            if self.fuel and not self.boosted:
                self.boosted = True
                self.current_engine_volume = self.boosted_engine_volume
        else:
            if self.boosted:
                self.boosted = False
                self.current_engine_volume = self.standard_engine_volume
        # Volume of the engine changes when we engage / disengage the boost
        if self.media_player and self.engine_activated_sound.is_playing(self.media_player):
            self.engine_activated_sound.set_volume(self.current_engine_volume, self.media_player)

    def on_update(self, delta_time: float = 1 / 60):
        # Stay centred and oriented on the owner
        self.center_x = self.owner.center_x + self.engine_owner_offset * math.sin(self.owner.radians)
        self.center_y = self.owner.center_y - self.engine_owner_offset * math.cos(self.owner.radians)
        self.angle = self.owner.angle
        # Flicker the texture used - doing this based on the decimal part of the remaining fuel value
        self.texture = self.textures[int((self.fuel - int(self.fuel)) * 10) % 2]
        # If activated, use up some fuel
        if self.activated:
            self.fuel = max(self.fuel - self.burn_rate * delta_time, 0)
            # We don't play a sound WHEN the engine in activated specifically, as it plays continuously, so it's here
            if (not self.media_player
                    or not self.engine_activated_sound.is_playing(self.media_player)
                    # Line below is so it repeats without a gap
                    or self.engine_activated_sound.get_stream_position(self.media_player) > 0.78):
                self.media_player = sounds.play_sound(self.sound_enabled,
                                                      self.engine_activated_sound,
                                                      volume=self.current_engine_volume * sounds.get_volume_multiplier(
                                                          self.position),
                                                      pan=sounds.get_pan(self.position),
                                                      speed=sounds.get_speed(self.position, (
                                                          self.owner.velocity_x, self.owner.velocity_y)))

            if self.fuel == 0:
                self.deactivate()
        elif self.media_player and self.engine_activated_sound.is_playing(self.media_player):
            self.engine_activated_sound.stop(self.media_player)
