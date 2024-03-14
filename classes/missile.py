from __future__ import annotations
import arcade
import constants
from classes.game_object import GameObject
from classes.engine import Engine
from pathlib import Path
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from classes.world import World
    from classes.lander import Lander


class Missile(GameObject):
    def __init__(self, scene: arcade.Scene, world: World, camera: arcade.Camera,
                 mass: int = 30, scale: float = 0.3 * constants.SCALING,
                 engine_fuel: int = 20,
                 engine_force: int = 6000,
                 engine_scale: float = 0.3 * constants.SCALING,
                 engine_max_volume: float = 0.3,
                 filename: str = "images/missile.png",
                 explosion_initial_radius_multiplier: float = 0.5,
                 explosion_final_radius_multiplier: float = 4,
                 explosion_lifetime: float = 2,  # seconds
                 explosion_force: int = 4000):
        super().__init__(scene=scene,
                         world=world,
                         camera=camera,
                         filename=filename,
                         mass=mass,
                         scale=scale,

                         # Explosion related
                         explosion_initial_radius_multiplier=explosion_initial_radius_multiplier,
                         explosion_final_radius_multiplier=explosion_final_radius_multiplier,
                         explosion_force=explosion_force,
                         explosion_lifetime=explosion_lifetime
                         )
        self.scene.add_sprite("Missiles", self)
        # Engine permanently on
        self.engine = Engine(scene=scene,
                             owner=self,
                             fuel=engine_fuel,
                             force=engine_force,
                             scale=engine_scale,
                             sound_enabled=True,
                             engine_activated_sound=constants.SOUNDS['sounds/engine.mp3'],
                             max_volume=engine_max_volume)
        self.engine.engine_owner_offset = int(1.4 * self.height)

    def on_update(self, delta_time: float = 1 / 60):
        super().on_update(delta_time=delta_time)
        if self.engine.activated:
            # I want the missile to take the shortest route to the lander - and that might
            # involve a world wrap.
            if lander_sprite_list := self.scene.name_mapping.get("Lander"):
                lander: Lander = lander_sprite_list[0]
                points = [lander.position,
                          (lander.position[0] - (constants.WORLD_WIDTH - 2 * self.world.camera_width), lander.position[1]),
                          (lander.position[0] + (constants.WORLD_WIDTH - 2 * self.world.camera_width), lander.position[1])]
                point = sorted(points, key=lambda p: arcade.get_distance(*self.position, *p))[0]
                self.face_point(point)
        else:
            self.engine.activate()
