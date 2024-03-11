from __future__ import annotations
import arcade
from constants import SCALING, WORLD_WIDTH
import random
import itertools
from classes.game_object import GameObject
from classes.missile import Missile
from classes.shield import Shield

import collisions
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from classes.world import World


class MissileLauncher(GameObject):
    def __init__(self, scene: arcade.Scene, camera: arcade.Camera, world: World, missile_interval: int = 15,
                 scale: float = 0.3 * SCALING, mass: int = 300, shield: bool = True):
        super().__init__(scene=scene,
                         camera=camera,
                         world=world,
                         filename="images/missile_launcher.png",
                         mass=mass,
                         scale=scale,
                         )

        self.missile_interval = missile_interval
        self.current_interval = random.randint(0, missile_interval)
        if shield:
            # Effectively infinite shield
            self.shield = Shield(scene=scene, owner=self, charge=999999, sound_enabled=True)
            self.shield_disabled_for_missile_fire_interval = max(missile_interval // 5, 2)
        else:
            self.shield = None
        if collisions.place_on_world(self, world, scene):
            # If we can't place the object on the world, we never add it to a sprite list.
            # It's just forgotten about
            self.scene.add_sprite("Ground Enemies", self)
        if shield:
            self.shield.activate()



    def on_update(self, delta_time: float = 1 / 60):
        self.current_interval -= delta_time
        # If there's a shield, we switch it off before firing and back on again afterwards
        if (self.shield is not None
                and self.current_interval <= self.shield_disabled_for_missile_fire_interval
                and self.shield.activated):
            self.shield.deactivate()
        if self.current_interval <= 0:
            self.fire_missile()
            self.current_interval = self.missile_interval
        if (self.shield is not None
                and self.current_interval <= self.missile_interval - self.shield_disabled_for_missile_fire_interval
                and not self.shield.activated):
            self.shield.activate()

    def fire_missile(self):
        missile = Missile(scene=self.scene, world=self.world, camera=self.camera,
                          )
        missile.center_x = self.center_x
        missile.center_y = self.top + missile.height
        missile.change_y = 160 * (1/60)


class SuperMissileLauncher(MissileLauncher):
    # Would like a different picture for the super missile launcher, and for it's missiles
    # I'd quite like it to activate shields in between firing missiles ...

    def __init__(self, scene: arcade.Scene, camera: arcade.Camera, world: World, missile_interval: int = 15,
                 scale: float = 0.5 * SCALING, mass: int = 600):
        super().__init__(scene=scene,
                         camera=camera,
                         world=world,
                         mass=mass,
                         scale=scale,
                         missile_interval=missile_interval,
                         )

    def fire_missile(self):
        missile = Missile(scene=self.scene, world=self.world, camera=self.camera,
                          mass=50,
                          scale=0.4 * SCALING,
                          # Engine related
                          engine_fuel=60,
                          engine_force=12000,
                          engine_scale=0.5 * SCALING,
                          engine_max_volume=0.4,
                          # Explosion related
                          explosion_final_radius_multiplier=8,
                          explosion_force=6000,
                          explosion_lifetime=4
                          )
        missile.center_x = self.center_x
        missile.center_y = self.top + missile.height
        missile.change_y = 160 * (1/60)
