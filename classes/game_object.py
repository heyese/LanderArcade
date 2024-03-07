from __future__ import annotations
import arcade
import math
import sounds
from constants import SCALING, SPACE_START, SPACE_END
from typing import TYPE_CHECKING
import collisions
if TYPE_CHECKING:
    from classes.world import World
    from classes.explosion import Explosion


class GameObject(arcade.Sprite):
    def __init__(self,
                 scene: arcade.Scene,
                 world: World,
                 camera: arcade.Camera,
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
                 sound_enabled: bool = False
                 ):
        super().__init__(filename=filename, scale=scale * SCALING, angle=angle)
        self.scene = scene
        self.camera = camera
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
        force_x, force_y = self.explosion_force()
        force_y += self.determine_force_y(force_y)
        force_x += self.determine_force_x(force_x)
        # Force due to explosions

        # Calculate changes in coordinates due to force
        # s = ut + (0.5)at^2
        self.change_x = self.velocity_x * delta_time + 0.5 * (force_x / self.mass) * (delta_time ** 2)
        self.change_y = self.velocity_y * delta_time + 0.5 * (force_y / self.mass) * (delta_time ** 2)

        self.center_x += self.change_x
        self.center_y += self.change_y

    def explosion_force(self):
        # Force due to explosions - not applied to ground objects or explosions themselves
        if self.on_ground or not collisions.is_sprite_in_camera_view(sprite=self, camera=self.camera) or self.__class__.__name__ == "Explosion":
            # Don't go to the trouble of applying explosion forces to sprites that are off screen
            return 0, 0

        force_x, force_y = 0, 0
        # Explosions change size, meaning their hit box becomes inaccurate, and I'm not
        # immediately sure how to fix that.  So will treat them as circles and use the radius and make my own check
        for explosion in self.scene["Explosions"]:
            explosion: Explosion
            if collisions.modulus((self.center_x - explosion.center_x, self.center_y - explosion.center_y)) < explosion.radius:
                # Direction of force is along the vector from the explosion to the game object.
                if (explosion.center_x - self.center_x) == 0 and (explosion.center_y - self.center_y == 0):
                    continue
                unit_vector = collisions.unit_vector_from_pos1_to_pos2((explosion.center_x, explosion.center_y), (self.center_x, self.center_y))
                angle = math.atan2(unit_vector[1], unit_vector[0])
                force_x += explosion.force * math.cos(angle)
                force_y += explosion.force * math.sin(angle)
        return force_x, force_y

    def explode(self):
        # Explosions are automatically added to the scene
        from classes.explosion import Explosion
        self.explosion = Explosion(scene=self.scene,
                                   world=self.world,
                                   camera=self.camera,
                                   mass=self.mass,
                                   scale=self.scale,
                                   radius_initial=int(self.height) // 2,
                                   radius_final=int(self.height) * 4,
                                   lifetime=2,  # seconds
                                   # Force here is what's applied to airborne objects that are
                                   # within the explosion (and presumably shielded!).
                                   # Say gravity is 100, lander mass is 20, so gravitational force
                                   # is f = ma -> 2000.
                                   # So trying to get a feel for what the right value should be,
                                   # but 4000 is double the kind of average gravitational pull
                                   force=4000,  # was 20
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
