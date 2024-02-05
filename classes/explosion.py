

import arcade
from classes.mobile_object import MobileObject
from classes.world import World
from constants import SCALING
from typing import List
import random

# How on earth are explosions going to work ... ?
# Explosions will exert a force on mobile objects they come into contact with,
# but I don't think those objects will exert a force on them ...
# I think this means that their trajectory is completely determined by initial conditions and gravity?
# They can't go through the ground - when they hit the ground, they should be subject to friction to slow them down.
# On contact, they will cause objects that can explode to explode (unless a force field is activated)
# They won't exert a force on other explosions ... I don't think this really makes sense
# They are always drawn behind anything using a force-field
# Properties would be:
#    initial size
#    final size
#    rate of increase of size (or maybe simply to just call this lifetime - measure in seconds)
#    force (that's applied to shielded mobile objects)
#    initial velocity - I *think* I want explosions to move

# Not sure what happens to a shielded object that is initially hit - technically this
# is before the existence of an explosion, but should be considered.  If a missile
# hits a shielded craft at speed and the explosion flies on, it might even push the ship
# backwards.  There should be a significant transfer of energy on impact
# But then might the object fly away faster than the explosion increases in size?  Does this matter?


class Explosion(MobileObject):
    def __init__(self,
                 scene: arcade.Scene,
                 world: World,
                 mass: int,
                 scale: float,
                 radius_initial: int,
                 radius_final: int,
                 lifetime: float,  # seconds
                 force: float,  # exerted on mobile objects in contact
                 velocity_x: float,
                 velocity_y: float,
                 center_x: int,
                 center_y: int):
        files = [
            "images/explosion_1.png",
            "images/explosion_2.png",
            "images/explosion_3.png",
            "images/explosion_4.png",
        ]
        file = random.choice(files)
        super().__init__(filename=file,
                         scale=scale * SCALING,
                         world=world,

                         mass=mass,
                         scene=scene,
                         center_x=center_x,
                         center_y=center_y,
                         velocity_x=velocity_x,
                         velocity_y=velocity_y,
                         angle=random.randint(1, 360))

        self.velocity_x_initial = velocity_x
        self._radius = radius_initial
        self.height = 2 * radius_initial
        self.width = 2 * radius_initial
        self.radius_initial = radius_initial
        self.radius_final = radius_final
        self.lifetime = lifetime  # Explosion lifetime in seconds.  Used to scale it from radius_initial to radius_final.
        self.force = force
        self.scene.add_sprite(name="Explosions", sprite=self)
        self.timer = 0
        self.rotation_rate = random.randint(1, 180)  # degrees per second

    @property
    def radius(self) -> float:
        return self._radius

    @radius.setter
    def radius(self, new_radius: float):
        self._radius = new_radius
        self.height = 2 * new_radius
        self.width = 2 * new_radius

    def on_update(self, delta_time: float = 1 / 60):
        super().on_update(delta_time=delta_time)
        self.timer += delta_time
        # We start off spinning but, as friction reduces the horizontal speed of the explosion to zero, we stop rotating
        self.angle += 0 if not self.velocity_x_initial else delta_time * self.rotation_rate * abs(self.velocity_x/self.velocity_x_initial)
        self.radius = self.radius_initial + (self.timer / self.lifetime) * (self.radius_final - self.radius_initial)
        if self.timer > self.lifetime:
            self.remove_from_sprite_lists()

    def check_for_collision(self):
        # I am going to let other objects worry about whether they've collided with an explosion.
        # All the explosion needs to worry about is its interaction with the ground
        # And here, I'm only considering the centre of the explosion

        # So I want the three ground rects - directly underneath, and left and right
        # Since rects are in order from left to right, this shouldn't be hard
        r1, r2, r3 = None, None, None
        for r in [*self.world.terrain_left_edge, *self.world.terrain_centre, *self.world.terrain_right_edge]:
            r1, r2, r3 = r2, r3, r
            if not r1:
                continue
            if r1.right <= self.center_x <= r3.left:
                break

        if self.center_y <= r2.top:
            self.change_y = 0
            self.on_ground = True
        else:
            self.on_ground = False
        if ((self.center_x + self.change_x <= r1.right and r1.top > self.center_y) or
                (self.center_x + self.change_x >= r3.left and r3.top > self.center_y)):
            self.change_x = 0
