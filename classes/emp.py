from __future__ import annotations

import arcade
import math
import constants
from classes.engine import Engine
from classes.shield import Shield
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from classes.game_object import GameObject


class EMP(arcade.SpriteCircle):
    """An EMP pulse disables any activated shields and engines it touches"""
    def __init__(self, *, scene: arcade.Scene,
                 owner: GameObject,
                 initial_radius: int | None = None,
                 final_radius: int | None = None,
                 lifetime: float = 3):
        self.scene = scene
        self.owner = owner
        self.initial_radius = int(initial_radius or owner.width)
        self.final_radius = int(final_radius or 18 * owner.width)
        self.radius = self.initial_radius
        self.disable_time = 10  # seconds
        # Initially draw the sprite at the final size, to get a good definition
        super().__init__(radius=self.final_radius, color=(*arcade.color.ATOMIC_TANGERINE, 100))
        self.width = self.radius * 2
        self.height = self.radius * 2
        self.lifetime = lifetime
        self.timer = lifetime
        self.center_x = owner.center_x
        self.center_y = owner.center_y
        self.scene.add_sprite('EMPs', self)
        self.sound = constants.SOUNDS['sounds/emp.mp3']
        sound_speed = self.sound.get_length() / self.lifetime
        self.sound_player = arcade.play_sound(sound=self.sound, speed=sound_speed, volume=2)
        self.media_player_references = ['sound_player']
        self.root_2 = math.sqrt(2)

        # Another sprite, which shows the inner part of the EMP, within which it is safe to use engines / shields again
        self.inner_circle = arcade.SpriteCircle(radius=self.final_radius, color=(*arcade.color.AUROMETALSAURUS, 50))
        self.inner_circle.center_x = owner.center_x
        self.inner_circle.center_y = owner.center_y
        self.inner_circle_radius = 10  # Don't initialise with radius = 0!
        self.inner_circle.width = self.initial_radius * 2
        self.inner_circle.height = self.initial_radius * 2

    def on_update(self, delta_time: float = 1 / 60):

        self.timer -= delta_time
        if self.timer <= 0:
            self.inner_circle.remove_from_sprite_lists()
            self.remove_from_sprite_lists()
            return
        self.center_x = self.owner.center_x
        self.center_y = self.owner.center_y
        # These don't actually make a difference - just so we can reference them in functions
        self.radius = ((self.lifetime - self.timer) / self.lifetime) * (self.final_radius - self.initial_radius) + self.initial_radius
        self.width = self.radius * 2
        self.height = self.radius * 2
        if self.radius - 2 * self.initial_radius > 0:
            if self.inner_circle not in self.scene['EMPs']:
                self.scene.add_sprite('EMPs', self.inner_circle)
            self.inner_circle.center_x = self.owner.center_x
            self.inner_circle.center_y = self.owner.center_y
            self.inner_circle_radius = int(self.radius - 2 * self.initial_radius)
            self.inner_circle.width = self.inner_circle_radius * 2
            self.inner_circle.height = self.inner_circle_radius * 2
        # Even though we're changing the size of the sprite, I'm not manipulating the hit box because I simply
        # calculate collisions with the EMP blast directly

        self.EMP_collisions()

    def EMP_collisions(self):
        emp_collision_spritelists = [self.scene[name] for name in constants.EMP_COLLISION_SPRITELISTS]
        for obj in [o for sprite_list in emp_collision_spritelists for o in sprite_list]:
            distance = arcade.get_distance_between_sprites(self, obj)
            # I imagine the EMP as a wave going outwards.  Might add some animation at some point.
            # I kind of show that in the animation - there's like an outer wave in the expanding circle.
            # For the user of the weapon, when they see they are in the inner part (which is almost immediately),
            # it's safe for them to reactivate their shield and engine
            if (self.inner_circle_radius < distance < self.radius  # Like a wave going outward
                    # This catches the person firing the EMP if they are using their shield or engine when they actually fire it
                    or distance < self.radius < 2 * self.initial_radius):
                if obj in self.scene["Shields"]:
                    shield: Shield = obj
                    if shield.activated and shield.owner not in self.scene["Hostages"]:
                        # EMP disables this shield!!
                        # I've not thought about hostages yet ... maybe their shields get disabled and then they're
                        # vulnerable?  For now, they are let off the hook and their shields keep working!
                        shield: Shield = obj
                        shield.disable_for(self.disable_time)
                if obj in self.scene["Engines"]:
                    engine: Engine = obj
                    if engine.activated:
                        engine.disable_for(self.disable_time)
