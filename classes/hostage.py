import arcade
import itertools
from constants import SCALING
from classes.world import World
from classes.game_object import GameObject
from classes.shield import Shield
from classes.lander import Lander
import random


class Hostage(GameObject):
    def __init__(self, scene: arcade.Scene, world: World, lander: Lander):
        super().__init__(scene=scene,
                         world=world,
                         filename="images/hostage.png",
                         mass=20,
                         scale=0.1 * SCALING,
                         explodes=False,
                         on_ground=True,
                         )
        self.scene.add_sprite("Hostages", self)
        self.lander = lander
        self.engine = None
        self.shield = Shield(scene=scene, owner=self, charge=9999)  # Effectively infinite
        self.disabled_shield = None
        self.rescued: bool = False
        self.shield.activate()  # Hostage shield is permanently activated
        self.place_on_world()

    def on_update(self, delta_time: float = 1 / 60):
        pass

    def place_on_world(self):
        wide_enough_rectangles = [r for r in itertools.chain(self.world.terrain_left_edge,
                                                             self.world.terrain_centre)
                                  # Want the lander to be able to get close!
                                  if r.width >= 1.5 * self.lander.shield.width]
        random.shuffle(wide_enough_rectangles)
        placed = False
        for chosen_rect in wide_enough_rectangles:
            collides = False
            for sprite_list in [self.scene[name] for name in ('Landing Pad', 'Ground Enemies', 'Hostages', 'Shields')]:
                if arcade.get_sprites_at_point((chosen_rect.center_x, chosen_rect.top + int(self.height / 2)), sprite_list):
                    collides = True
            if collides is False:
                self.center_x = chosen_rect.center_x
                self.bottom = chosen_rect.top
                placed = True
                break
        if placed is False:
            # No space for this missile launcher, so we don't create it
            self.remove_from_sprite_lists()
