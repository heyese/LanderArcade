from xml.dom.minidom import Entity

import arcade
from constants import SCALING, WORLD_WIDTH
from classes.world import World
from classes.game_object import GameObject
from classes.missile import Missile
import random
import itertools
from classes.engine import Engine
from classes.lander import Lander


class MissileLauncher(GameObject):
    def __init__(self, scene: arcade.Scene, world: World, missile_interval: int = 100):
        super().__init__(scene=scene,
                         world=world,
                         filename="images/missile_launcher.png",
                         mass=300,
                         scale=0.3 * SCALING,
                         )
        self.scene.add_sprite("Ground Enemies", self)
        self.place_on_world()
        self.missile_interval = missile_interval
        self.current_interval = missile_interval

    def on_update(self, delta_time: float = 1 / 60):
        self.current_interval -= delta_time
        if self.current_interval <= 0:
            self.fire_missile()
            self.current_interval = self.missile_interval


    def place_on_world(self):
        # So I need to find a flat space wide enough on the world surface for the pad and it's shield
        # List all rectangles with large enough width and then pick one at random?

        wide_enough_rectangles = [r for r in itertools.chain(self.world.terrain_left_edge, self.world.terrain_centre)
                                  if r.width >= self.width]
        random.shuffle(wide_enough_rectangles)
        placed_missile_launcher = False
        for chosen_rect in wide_enough_rectangles:
            collides = False
            for sprite_list in [self.scene[name] for name in ('Landing Pad', 'Ground Enemies')]:
                if arcade.get_sprites_at_point((chosen_rect.center_x, chosen_rect.top + int(self.height / 2)), sprite_list):
                    collides = True
            if collides is False:
                self.center_x = chosen_rect.center_x
                self.bottom = chosen_rect.top
                placed_missile_launcher = True
                break
        if placed_missile_launcher is False:
            # No space for this missile launcher, so we don't create it
            self.remove_from_sprite_lists()

    def fire_missile(self):
        missile = Missile(scene=self.scene, world=self.world)
        missile.center_x = self.center_x
        missile.center_y = self.top + missile.height
        missile.change_y = 160 * (1/60)