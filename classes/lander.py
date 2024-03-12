from __future__ import annotations
import arcade
import math
import sounds
from constants import SCALING, SPACE_END
import collisions
from pathlib import Path
from classes.game_object import GameObject
from classes.engine import Engine
from classes.shield import Shield, DisabledShield
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from classes.world import World


class Lander(GameObject):
    def __init__(self, scene: arcade.Scene, camera: arcade.Camera, world: World, fuel=100, shield_charge=100):
        super().__init__(scene=scene,
                         world=world,
                         filename="images/lander.png",
                         mass=20,
                         scale=0.2 * SCALING,
                         camera=camera
                         )
        self.scene.add_sprite("Lander", self)
        self.engine = Engine(scene=scene, owner=self, fuel=fuel, sound_enabled=True)
        self.shield = Shield(scene=scene, owner=self, charge=shield_charge, sound_enabled=True)
        self.max_landing_angle = 20
        self.mouse_location = None  # Set by Game view.  Want Lander to face mouse on every update
        self._landed: bool = False
        self.trying_to_activate_shield = False
        self._hostages_being_rescued = set()
        self._tractor_beam_timer: float = 0

        # Sound related
        self.sound_enabled = True
        self.teleport_complete = arcade.load_sound(Path('sounds/teleport_complete.mp3'))
        self.teleport_complete_player = None
        self.teleport_ongoing = arcade.load_sound(Path('sounds/teleport_ongoing.mp3'))
        self.teleport_ongoing_player = None
        self.recharged = arcade.load_sound(Path('sounds/recharged.mp3'))
        self.recharged_player = None
        self.max_volume = 0.4
        # I have a timer so I can control how long sounds play for before I adjust their attributes
        self.sound_timer = 0
        # Num seconds after which sound attributes are updated.  If I do this every frame, sound is crackly and it doesn't work well.
        self.sound_attributes_update_interval = 10  # Not really needed

    @property
    def landed(self):
        return self._landed

    @landed.setter
    def landed(self, value: bool):
        self._landed = value
        if value:
            # Refill fuel and recharge shield
            self.engine.deactivate()
            self.engine.refuel()
            self.shield.recharge()
            self.change_x = 0
            self.change_y = 0
            self.angle = 0
            self.bottom = self.scene['Landing Pad'].sprite_list[0].top
            # Don't play recharged sound when the level is completed
            if self.scene["Hostages"]:
                self.recharged_player = arcade.play_sound(sound=self.recharged, volume=self.max_volume)

    def on_update(self, delta_time: float = 1 / 60):
        super().on_update(delta_time=delta_time)
        # Create list of the rescuers we are currently rescuing
        if not self.dead:
            for hostage in self.scene["Hostages"]:
                distance_to_hostage = collisions.modulus((hostage.center_x - self.center_x, hostage.center_y - self.center_y))
                if distance_to_hostage <= hostage.rescue_distance:
                    hostage.being_rescued = True
                    self._hostages_being_rescued.add(hostage)
                elif hostage.being_rescued:
                    hostage.being_rescued = False
                    self._hostages_being_rescued.remove(hostage)

        # If we're still rescuing anyone - animate the tractor beam!
        if self._hostages_being_rescued:
            self._tractor_beam_timer += delta_time
            self.teleport_ongoing_player = sounds.play_or_update_sound(sound=self.teleport_ongoing,
                                                                       player=self.teleport_ongoing_player,
                                                                       delta_time=delta_time,
                                                                       loop=True,
                                                                       obj=self)
        else:
            self._tractor_beam_timer = 0
            self.teleport_ongoing_player and self.teleport_ongoing.stop(self.teleport_ongoing_player)
            self.teleport_ongoing_player = None

    def hostage_rescued(self, hostage):
        self._hostages_being_rescued.remove(hostage)
        self.teleport_ongoing_player and self.teleport_ongoing.stop(self.teleport_ongoing_player)
        self.teleport_complete_player = arcade.play_sound(sound=self.teleport_complete, volume=self.max_volume)

    def determine_force_y(self, force_y):
        force_y = super().determine_force_y(force_y)
        if self.above_space and self.change_y > 0:
            # We want to stop people flying off into deep space, but I don't want to fling them wildly
            # back at the ground.  So we only apply the force while we're gaining altitude
            force_y -= self.mass * 5 * (self.center_y - SPACE_END)
        return force_y

    def draw_landing_angle_guide(self):
        length = (6 * self.height)
        y = self.center_y + length * math.cos(self.max_landing_angle * math.pi / 180)
        x_left = self.center_x - length * math.sin(self.max_landing_angle * math.pi / 180)
        x_right = self.center_x + length * math.sin(self.max_landing_angle * math.pi / 180)
        arcade.draw_polygon_filled(point_list=[(x_left, y), (self.center_x, self.center_y), (x_right, y)], color=(*arcade.color.WHITE_SMOKE, 20))

    def draw_tractor_bream(self):
        # When we're rescuing hostages, we're using the tractor beam!
        period = 1  # seconds
        alpha_range = (20, 150)
        if self._tractor_beam_timer:
            alpha = int(sum(alpha_range) / 2 + math.sin(self._tractor_beam_timer * 2 * math.pi / period) * (alpha_range[1] - alpha_range[0]) / 2)
            for hostage in self._hostages_being_rescued:
                points = [(self.center_x, self.center_y), (hostage.left - hostage.width, hostage.bottom), (hostage.right + hostage.width, hostage.bottom)]
                arcade.draw_polygon_filled(point_list=points, color=(*arcade.color.RUBY_RED, alpha))

    def die(self):
        super().die()
        for hostage in self._hostages_being_rescued:
            hostage.being_rescued = False
        self._hostages_being_rescued = set()
