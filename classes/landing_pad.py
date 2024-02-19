from __future__ import annotations
import arcade
import random
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from classes.lander import Lander
    from classes.world import World


# I like the idea of having a pad that "opens up" - ie. 3 rectangles, the middle one which is flat that you
# actually land on, and the other two both at an angle so as to cover the main pad up.
#
#                /  \     -->   \    /
#                ----            ----
# Main landing pad colour can reflect land-possibility-status (ie. green if slow enough and not over edges, red otherwise)
# Contact with the side panels would blow the ship up

# Not figured out how to do all that yet, so for now, lets just do a landing pad


class LandingPad(arcade.SpriteSolidColor):
    def __init__(self, scene: arcade.Scene, lander: Lander, world: World, width: int, height: int):
        super().__init__(width=width, height=height, color=arcade.color.WHITE_SMOKE)
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
        self.scene = scene
        self.scene.add_sprite("Landing Pad", self)
        self.place_landing_pad_on_world()
        # LandingPad has effectively infinite shield
        # but disabling shield for now - bit complicated to implement, and want the game to evolve a bit first
        #self.shield = Shield(scene=self.scene, owner=self, radius=int(1.5*self.width), power=999)
        #self.shield_sensor = arcade.SpriteCircle(radius=int(4*self.width), color=(0, 0, 0, 200))
        #self.shield_sensor.center_x, self.shield_sensor.center_y = self.center_x, self.center_y
        self.mass = 999  # Effectively, infinitely heavy
        self.velocity_x, self.velocity_y = 0, 0
        self.on_ground = True

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

        # LandingPad has an infinite shield that should auto-activate before anything gets within range
        # Lander can fly in and out of this without problems
        # We use the shield_sensor to know if we need to switch the shield on or off
        # collision = arcade.check_for_collision_with_lists(self.shield_sensor,
        #                                                   [self.scene['Missiles'],
        #                                                    self.scene['Air Enemies'],
        #                                                    self.scene['Explosions']])
        # if collision:
        #     self.shield.activate()
        # else:
        #     self.shield.deactivate()


    def place_landing_pad_on_world(self):
        # So I need to find a flat space wide enough on the world surface for the pad and it's shield
        # List all rectangles with large enough width and then pick one at random?

        wide_enough_rectangles = [r for r in self.world.terrain_centre
                                  if r.width >= self.width
                                  and not arcade.check_for_collision_with_lists(self, [self.scene['Ground Enemies'],
                                                                                       self.scene['Landing Pad']])]
        chosen_rect = wide_enough_rectangles[random.randrange(len(wide_enough_rectangles))]
        self.center_x = chosen_rect.center_x
        self.bottom = chosen_rect.top
