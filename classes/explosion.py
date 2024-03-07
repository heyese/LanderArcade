from __future__ import annotations

import math
import arcade
import random
from classes.game_object import GameObject
from constants import SCALING
import sounds
from typing import TYPE_CHECKING
from pathlib import Path
if TYPE_CHECKING:
    from classes.world import World

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

EXPLOSION_SOUNDS = [arcade.load_sound(Path(bounce_sound)) for bounce_sound in Path('sounds').glob('explosion_*.mp3')]


class Explosion(GameObject):
    def __init__(self,
                 scene: arcade.Scene,
                 world: World,
                 camera: arcade.Camera,
                 mass: int,
                 scale: float,
                 radius_initial: int,
                 radius_final: int,
                 lifetime: float,  # seconds
                 force: float,  # exerted on mobile objects in contact
                 velocity_x: float,
                 velocity_y: float,
                 center_x: int,
                 center_y: int,
                 owner: GameObject):
        files = [
            "images/explosion_1.png",
            "images/explosion_2.png",
            "images/explosion_3.png",
            "images/explosion_4.png",
        ]
        file = random.choice(files)
        super().__init__(filename=file,
                         scale=scale * SCALING,
                         camera=camera,
                         world=world,
                         explodes=False,
                         mass=mass,
                         scene=scene,
                         center_x=center_x,
                         center_y=center_y,
                         velocity_x=velocity_x,
                         velocity_y=velocity_y,
                         angle=random.randint(1, 360),
                         owner=owner)

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
        self.root_2 = math.sqrt(2)

        # Sound related
        self.explosion_sound = random.choice(EXPLOSION_SOUNDS)

    @property
    def radius(self) -> float:
        return self._radius

    @radius.setter
    def radius(self, new_radius: float):
        self._radius = new_radius
        self.height = 2 * new_radius
        self.width = 2 * new_radius
        # self.top = self.center_y + new_radius
        # self.bottom = self.center_y - new_radius
        # self.left = self.center_x - new_radius
        # self.right = self.change_x + new_radius

    def on_update(self, delta_time: float = 1 / 60):
        super().on_update(delta_time=delta_time)
        self.timer += delta_time
        self.sound_timer += delta_time

        sounds.play_or_update_sound(delta_time=delta_time, sound=self.explosion_sound, obj=self)

        # We start off spinning but, as friction reduces the horizontal speed of the explosion to zero, we stop rotating
        self.angle += 0 if not self.velocity_x_initial else delta_time * self.rotation_rate * abs(self.velocity_x/self.velocity_x_initial)
        self.radius = self.radius_initial + (self.timer / self.lifetime) * (self.radius_final - self.radius_initial)

        # https://api.arcade.academy/en/stable/api/sprites.html#arcade.Sprite.set_hit_box
        # As the explosion grows, I need to adjust its hit box so collisions remain accurate
        # We imagine the explosion is at (0, 0).  So basically, I'm specifying points on a circle here

        points = [[self.radius, 0],
                  [self.radius / self.root_2, -self.radius / self.root_2],
                  [0, -self.radius],
                  [-self.radius / self.root_2, -self.radius / self.root_2],
                  [-self.radius, 0],
                  [-self.radius / self.root_2, self.radius / self.root_2],
                  [0, self.radius],
                  [self.radius / self.root_2, self.radius / self.root_2]]
        # Hit box ASSUMES THE SCALE IS 1.0!!
        scaled_points = [[int(a / self.scale), int(b / self.scale)] for a, b in points]
        self.hit_box = scaled_points
        if self.timer > self.lifetime:
            self.remove_from_sprite_lists()
