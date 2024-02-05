import arcade
import math
from constants import SCALING, SPACE_END
from classes.world import World
from classes.mobile_object import MobileObject
from classes.shield import Shield
from classes.engine import Engine

class Lander(MobileObject):
    def __init__(self, scene: arcade.Scene, world: World):
        super().__init__(scene=scene,
                         world=world,
                         filename="images/lander.png",
                         mass=20,
                         scale=0.2 * SCALING
                         )
        self.engine = Engine(owner=self)
        self.shield = Shield(owner=self)
        self.max_landing_angle = 20
        self.mouse_location = None  # Set by Game view.  Want Lander to face mouse on every update
        self.landed: bool = False

    def on_update(self, delta_time: float = 1 / 60):
        super().on_update(delta_time=delta_time)

        landing_pad = self.scene.get_sprite_list(name="Landing Pad")[0]
        landing_pad_collision = arcade.check_for_collision(self, landing_pad)
        if landing_pad_collision:
            if landing_pad.safe_to_land:
                self.landed = True
            # We've blown up
            elif self.dead is False:
                self.dead = True
                self.scene.remove_sprite_list_by_name("Lander")
                self.explode()

    def determine_force_y(self, force_y):
        force_y = super().determine_force_y(force_y)
        if self.above_space:
            # If someone tries to fly off into deep space, bring them back before they get lost ...
            force_y -= self.mass * 5 * (self.center_y - SPACE_END)
        return force_y

    def draw_landing_angle_guide(self):
        length = (6 * self.height)
        y = self.center_y + length * math.cos(self.max_landing_angle * math.pi / 180)
        x_left = self.center_x - length * math.sin(self.max_landing_angle * math.pi / 180)
        x_right = self.center_x + length * math.sin(self.max_landing_angle * math.pi / 180)
        arcade.draw_polygon_filled(point_list=[(x_left, y), (self.center_x, self.center_y), (x_right, y)], color=(*arcade.color.WHITE_SMOKE, 20))


