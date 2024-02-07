import arcade
from constants import SCALING
from classes.world import World
from classes.game_object import GameObject
from classes.engine import Engine


class Missile(GameObject):
    def __init__(self, scene: arcade.Scene, world: World):
        super().__init__(scene=scene,
                         world=world,
                         filename="images/missile.png",
                         mass=10,
                         scale=0.2 * SCALING,
                         )
        self.scene.add_sprite("Missiles", self)
        # Engine permanently on
        self.engine = Engine(owner=self, fuel=100)
        self.scene.add_sprite('Engines', self.engine)
        self.engine.engine_owner_offset = int(1.4 * self.height)

    def on_update(self, delta_time: float = 1 / 60):
        super().on_update(delta_time=delta_time)
        if self.engine.activated:
            if lander_sprite_list := self.scene.name_mapping.get("Lander"):
                self.face_point(lander_sprite_list[0].position)
        else:
            self.engine.activate()
