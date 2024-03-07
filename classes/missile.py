from __future__ import annotations
import arcade
from constants import SCALING, WORLD_WIDTH
from classes.game_object import GameObject
from classes.engine import Engine
from pathlib import Path
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from classes.world import World
    from classes.lander import Lander


class Missile(GameObject):
    def __init__(self, scene: arcade.Scene, world: World, camera: arcade.Camera):
        super().__init__(scene=scene,
                         world=world,
                         camera=camera,
                         filename="images/missile.png",
                         mass=30,
                         scale=0.3 * SCALING,
                         )
        self.scene.add_sprite("Missiles", self)
        # Engine permanently on
        self.engine = Engine(scene=scene, owner=self, fuel=20, force=6000, scale=0.3, sound_enabled=True,
                             engine_activated_sound=arcade.load_sound(Path('sounds/engine.mp3')),
                             max_volume=0.3)
        self.engine.engine_owner_offset = int(1.4 * self.height)

    def on_update(self, delta_time: float = 1 / 60):
        super().on_update(delta_time=delta_time)
        if self.engine.activated:
            # I want the missile to take the shortest route to the lander - and that might
            # involve a world wrap.
            if lander_sprite_list := self.scene.name_mapping.get("Lander"):
                lander: Lander = lander_sprite_list[0]
                points = [lander.position,
                          (lander.position[0] - (WORLD_WIDTH - 2 * self.world.camera_width), lander.position[1]),
                          (lander.position[0] + (WORLD_WIDTH - 2 * self.world.camera_width), lander.position[1])]
                point = sorted(points, key=lambda p: arcade.get_distance(*self.position, *p))[0]
                self.face_point(point)
        else:
            self.engine.activate()
