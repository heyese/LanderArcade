
# I like the idea of having a pad that "opens up" - ie. 3 rectangles, the middle one which is flat that you
# actually land on, and the other two both at an angle so as to cover the main pad up.
#
#                /  \     -->   \    /
#                ----            ----
# Main landing pad colour can reflect land-possibility-status (ie. green if slow enough and not over edges, red otherwise)
# Contact with the side panels would blow the ship up

# Not figured out how to do all that yet, so for now, lets just do a landing pad

import arcade
import random
import math
from lander import Lander
from world import World


class LandingPad(arcade.SpriteSolidColor):
    def __init__(self, lander: Lander, world: World):
        super().__init__(width=int(4 * lander.width), height=int(0.3 * lander.width), color=arcade.color.WHITE_SMOKE)
        self.disabled_color = arcade.color.WHITE_SMOKE
        self.lander = lander
        self.world = world
        self.unsafe_to_land_color = arcade.color.RED
        self.safe_to_land_color = arcade.color.GO_GREEN
        self.activated = False
        self.activated_timer: float = 0
        self.flicker_rate: int = 10  # Colour changes per second when lander is close
        self.safe_landing_speed = 50
        self._safe_to_land = False  # Property
        # Put the landing pad onto the world ...
        self.place_landing_pad_on_world()

    @property
    def safe_to_land(self):
        return self._safe_to_land

    @safe_to_land.setter
    def safe_to_land(self, value: bool):
        self._safe_to_land = value
        self.color = self.safe_to_land_color if value else self.unsafe_to_land_color

    def on_update(self, delta_time: float = 1 / 60):
        # Landing pad is automatically activated when the lander is close enough
        if arcade.sprite.get_distance_between_sprites(self, self.lander) < self.width:
            if not self.activated:
                self.activated = True
            self.activated_timer += delta_time
        elif self.activated is True:
            self.activated = False
            self.activated_timer = 0
            self.color = self.disabled_color

        # When activated, the landing pad's colour is determined by whether it's safe to land
        # ie. is the lander fully over the pad, is it going slowly enough, and is it not too tilted
        if self.activated:
            if (self.lander.left < self.left
                    or self.lander.right > self.right
                    or self.lander.velocity_y ** 2 + self.lander.velocity_x ** 2 > self.safe_landing_speed ** 2
                    or abs(self.lander.angle) > self.lander.max_landing_angle):  # Goes from -180 to +180 degress.
                self.safe_to_land = False
            else:
                self.safe_to_land = True

    def place_landing_pad_on_world(self):
        # So I need to find a flat space wide enough on the world surface for the pad
        # List all rectangles with large enough width and then pick one at random?

        # Currently I'm assuming it is possible to find a location - I should make sure it is!

        for rect in self.world.terrain:
            rect: arcade.SpriteSolidColor
            wide_enough_rectangles = [r for r in self.world.terrain if r.width >= self.width]
            chosen_rect = wide_enough_rectangles[random.randrange(len(wide_enough_rectangles))]
            self.center_x = chosen_rect.center_x
            self.bottom = chosen_rect.top




