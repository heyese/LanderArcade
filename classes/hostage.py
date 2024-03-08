from __future__ import annotations
import arcade
import itertools
from constants import SCALING
import random
from classes.game_object import GameObject
from classes.shield import Shield
import collisions
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from classes.world import World
    from classes.lander import Lander


class Hostage(GameObject):
    def __init__(self, scene: arcade.Scene, world: World, camera: arcade.Camera, lander: Lander):
        super().__init__(scene=scene,
                         world=world,
                         camera=camera,
                         filename="images/hostage.png",
                         mass=20,
                         scale=0.1 * SCALING,
                         explodes=False,
                         on_ground=True,
                         )
        self.lander = lander
        self.engine = None
        self.being_rescued: bool = False
        self.rescue_distance = 6 * self.lander.height
        self.rescue_timer = 5  # seconds
        self._current_timer = self.rescue_timer
        self.shield = Shield(scene=scene, owner=self, charge=9999)  # Effectively infinite
        self.disabled_shield = None
        if collisions.place_on_world(self, world, scene):
            # If we can't place the object on the world, we never add it to a sprite list.
            # It's just forgotten about
            # When playing, shield position is handled automatically, but we update it here so
            # that we can take account of it when placing further ground elements
            self.shield.position = self.position
            self.scene.add_sprite("Hostages", self)
            self.shield.activate()  # Hostage shield is permanently activated

    def on_update(self, delta_time: float = 1 / 60):
        if self.being_rescued:
            self._current_timer -= delta_time
            if self._current_timer <= 0:
                # Hostage has been rescued!
                self.remove_from_sprite_lists()
                self.shield.remove_from_sprite_lists()
                self.lander.hostage_rescued(self)
        else:
            self._current_timer = self.rescue_timer
