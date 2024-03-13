from __future__ import annotations

import arcade
import math
from pathlib import Path
import constants
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
                 lifetime: float = 4):
        self.scene = scene
        self.owner = owner
        self.initial_radius = int(initial_radius or owner.width)
        self.final_radius = int(final_radius or 12 * owner.width)
        self.radius = self.initial_radius
        self.disable_time = 5  # seconds
        # Initially draw the sprite at the final size, to get a good definition
        super().__init__(radius=self.final_radius, color=(*arcade.color.ATOMIC_TANGERINE, 100))
        self.width = self.radius * 2
        self.height = self.radius * 2
        self.lifetime = lifetime
        self.timer = lifetime
        self.center_x = owner.center_x
        self.center_y = owner.center_y
        self.scene.add_sprite('EMPs', self)
        self.sound = arcade.load_sound(Path('sounds/emp.mp3'))
        sound_speed = self.sound.get_length() / self.lifetime
        arcade.play_sound(sound=self.sound, speed=sound_speed, volume=1.5)
        self.root_2 = math.sqrt(2)

    def on_update(self, delta_time: float = 1 / 60):

        self.timer -= delta_time
        if self.timer <= 0:
            self.remove_from_sprite_lists()
            return
        self.center_x = self.owner.center_x
        self.center_y = self.owner.center_y
        # These don't actually make a difference - just so we can reference them in functions
        self.radius = ((self.lifetime - self.timer) / self.lifetime) * (self.final_radius - self.initial_radius) + self.initial_radius
        self.width = self.radius * 2
        self.height = self.radius * 2

        # Since we're changing the size of the sprite, it helps to manually adjust the hit box
        points = [[self.radius, 0],
                  [self.radius / self.root_2, -self.radius / self.root_2],
                  [0, -self.radius],
                  [-self.radius / self.root_2, -self.radius / self.root_2],
                  [-self.radius, 0],
                  [-self.radius / self.root_2, self.radius / self.root_2],
                  [0, self.radius],
                  [self.radius / self.root_2, self.radius / self.root_2]]
        # Hit box ASSUMES THE SCALE IS 1.0!!
        scaled_points = [[int(a), int(b)] for a, b in points]
        self.hit_box = scaled_points

        self.EMP_collisions()

    def EMP_collisions(self):
        emp_collision_spritelists = [self.scene[name] for name in constants.EMP_COLLISION_SPRITELISTS]
        collisions = arcade.check_for_collision_with_lists(self, emp_collision_spritelists)
        # Not sure whether it makes more sense to use the built in collision checking, or whether I should
        # simply use the fact that I know the centre and radius of the circle!
        for collision in collisions:
            if collision in self.scene["Shields"]:
                shield: Shield = collision
                if shield.activated:
                    # EMP disables this shield!!
                    shield.disable_for(self.disable_time)