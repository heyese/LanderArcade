from __future__ import annotations
import arcade
from constants import SCALING, WORLD_WIDTH
import random
import itertools
from classes.game_object import GameObject
from classes.missile import Missile
import collisions
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from classes.world import World


class MissileLauncher(GameObject):
    def __init__(self, scene: arcade.Scene, camera: arcade.Camera, world: World, missile_interval: int = 15):
        super().__init__(scene=scene,
                         camera=camera,
                         world=world,
                         filename="images/missile_launcher.png",
                         mass=300,
                         scale=0.3 * SCALING,
                         )
        if collisions.place_on_world(self, world, scene):
            # If we can't place the object on the world, we never add it to a sprite list.
            # It's just forgotten about
            self.scene.add_sprite("Ground Enemies", self)
        self.missile_interval = missile_interval
        self.current_interval = random.randint(0, missile_interval)

    def on_update(self, delta_time: float = 1 / 60):
        self.current_interval -= delta_time
        if self.current_interval <= 0:
            self.fire_missile()
            self.current_interval = self.missile_interval

    def fire_missile(self):
        missile = Missile(scene=self.scene, world=self.world, camera=self.camera)
        missile.center_x = self.center_x
        missile.center_y = self.top + missile.height
        missile.change_y = 160 * (1/60)
