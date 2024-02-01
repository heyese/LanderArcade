import arcade
import math
from constants import SCALING, SPACE_END
from classes.world import World
from classes.mobile_object import MobileObject


class Missile(MobileObject):
    def __init__(self, scene: arcade.Scene, world: World):
        super().__init__(scene=scene,
                         world=world,
                         filename="images/missile.png",
                         has_engine=True,
                         has_shield=False,
                         mass=10,
                         scale=0.2 * SCALING,
                         )
        # Engine permanently on
        self.engine.engine_owner_offset = int(1.4 * self.height)
        self.engine.fuel = 10

    def on_update(self, delta_time: float = 1 / 60):
        super().on_update(delta_time=delta_time)
        if lander_sprite_list := self.scene.name_mapping.get("Lander"):
            self.face_point(lander_sprite_list[0].position)
        if not self.engine.activated:
            self.engine.activate()
