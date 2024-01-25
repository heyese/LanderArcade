
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
        super().__init__(width=int(2 * lander.width), height=int(0.3 * lander.width), color=arcade.color.WHITE_SMOKE)
        self.disabled_color = arcade.color.WHITE_SMOKE
        self.lander = lander
        self.world = world
        self.danger_colors = [arcade.color.RED, self.disabled_color]
        self.safe_to_land_colors = [arcade.color.GO_GREEN, self.disabled_color]
        self.activated = False
        self.activated_timer: float = 0
        self.flicker_rate: int = 3  # Colour changes per second when lander is close
        # Put the landing pad onto the world ...
        self.place_landing_pad_on_world()

    def on_update(self, delta_time: float = 1 / 60):
        # I'd like it to flash when the lander is near
        if arcade.sprite.get_distance_between_sprites(self, self.lander) < self.width:
            if not self.activated:
                self.activated = True
            self.activated_timer += delta_time
        elif self.activated is True:
            self.activated = False
            self.activated_timer = 0
            self.color = self.disabled_color

        # Determine the colour by the timer and the flicker rate
        if self.activated:
            colors_index = math.floor((self.activated_timer * self.flicker_rate)) % len(self.safe_to_land_colors)
            self.color = self.safe_to_land_colors[colors_index]

    def place_landing_pad_on_world(self):
        # So I need to find a flat space wide enough on the world surface for the pad
        # List all rectangles with large enough width and then pick one at random?
        for rect in self.world.terrain:
            rect: arcade.SpriteSolidColor
            wide_enough_rectangles = [r for r in self.world.terrain if r.width >= self.width]
            chosen_rect = wide_enough_rectangles[random.randrange(len(wide_enough_rectangles))]
            self.center_x = chosen_rect.center_x
            self.bottom = chosen_rect.top