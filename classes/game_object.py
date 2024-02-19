from __future__ import annotations
import arcade
import math
from constants import SCALING, SPACE_START, SPACE_END
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from classes.world import World


class GameObject(arcade.Sprite):
    def __init__(self,
                 scene: arcade.Scene,
                 world: World,
                 filename: str,
                 mass: int,
                 scale: float,
                 velocity_x: float = 0,
                 velocity_y: float = 0,
                 center_x: int = 0,
                 center_y: int = 0,
                 on_ground: bool = False,
                 angle: int = 0,  # degrees
                 in_space: bool = False,
                 above_space: bool = False,
                 explodes: bool = True,
                 owner=None,
                 ):
        super().__init__(filename=filename, scale=scale * SCALING, angle=angle)
        self.scene = scene
        self.shield = None
        self.disabled_shield = None
        self.engine = None
        self.explosion = None
        self.world: World = world
        self.mass = mass
        self.center_x = center_x
        self.center_y = center_y
        # Don't like the Sprite.velocity attribute, since it's obvious delta_time can vary,
        # so it's not really a velocity - it's a change in position
        self.velocity_x = velocity_x
        self.velocity_y = velocity_y
        self.change_x = int(self.velocity_x * (1/60))  # pixels per second!
        self.change_y = int(self.velocity_y * (1/60))  #
        # Gravity only applies when we're not "in space"!
        self.in_space = in_space
        self.above_space = above_space
        self.on_ground = on_ground
        self.dead = False
        self.collided = False
        self.explodes = explodes
        self.owner = owner

    def on_update(self, delta_time: float = 1 / 60):
        # Are we in space or not?
        self.in_space = True if self.center_y >= SPACE_START else False
        self.above_space = True if self.center_y >= SPACE_END else False
        # Calculate current velocity from auto-maintained self.change_XXX variables and delta time
        self.velocity_x = self.change_x / delta_time  # pixels per second!
        self.velocity_y = self.change_y / delta_time
        # Calculate the force being applied
        force_y = self.determine_force_y(0)
        force_x = self.determine_force_x(0)

        # Calculate changes in coordinates due to force
        # s = ut + (0.5)at^2
        self.change_x = self.velocity_x * delta_time + 0.5 * (force_x / self.mass) * (delta_time ** 2)
        self.change_y = self.velocity_y * delta_time + 0.5 * (force_y / self.mass) * (delta_time ** 2)

        self.center_x += self.change_x
        self.center_y += self.change_y

    def explode(self):
        # Explosions are automatically added to the scene
        from classes.explosion import Explosion
        self.explosion = Explosion(scene=self.scene,
                                   world=self.world,
                                   mass=self.mass,
                                   scale=self.scale,
                                   radius_initial=int(self.height) // 2,
                                   radius_final=int(self.height) * 4,
                                   lifetime=2,  # seconds
                                   force=20,
                                   velocity_x=self.velocity_x,
                                   velocity_y=self.velocity_y,
                                   center_x=int(self.center_x),
                                   center_y=int(self.center_y),
                                   owner=self)

    def determine_force_x(self, force_x):
        # Force due to engine
        if self.engine is not None and self.engine.activated:
            force_x -= self.engine.force * math.sin(self.radians)
        # Force due to friction with the ground
        # Only really applies to explosions, since everything explodes on contact with the ground
        if self.on_ground and abs(self.velocity_x) > 0:
            friction = self.mass * self.world.gravity * self.world.friction_coefficient
            if self.velocity_x > 0:
                force_x -= friction
            else:
                force_x += friction
        return force_x

    def determine_force_y(self, force_y):
        if not self.in_space:
            # When not in the allowed(!) region of space, there's the world's gravity ...
            force_y -= self.mass * self.world.gravity
        # Force due to engine
        if self.engine is not None and self.engine.activated:
            force_y += self.engine.force * math.cos(self.radians)
        return force_y

    def die(self):
        self.dead = True
        for s in [self, self.shield, self.engine, self.disabled_shield]:
            if s is not None:
                s.remove_from_sprite_lists()
        if self.explodes:
            self.explode()
