import arcade
import math
from constants import SCALING, SPACE_START, SPACE_END
from classes.shield import Shield
from classes.engine import Engine
from classes.world import World
from views.next_level import NextLevelView


class Aircraft(arcade.Sprite):
    def __init__(self,
                 scene: arcade.Scene,
                 world: World,
                 filename: str,
                 mass: int,
                 scale: float):
        super().__init__(filename=filename, scale=scale * SCALING)
        self.scene = scene
        self.shield: Shield = Shield(self)
        self.engine: Engine = Engine(self)
        self.world: World = world
        self.mass = mass
        # Don't like the Sprite.velocity attribute, since it's obvious delta_time can vary,
        # so it's not really a velocity - it's a change in position
        self.velocity_x: float = 0
        self.velocity_y: float = 0
        # Gravity only applies when we're not "in space"!
        self.in_space: bool | None = None
        # Gravity applies pretty heavily if someone tries to fly off into space
        self.above_space: bool | None = None

    def on_update(self, delta_time: float = 1 / 60):
        # Are we in space or not?
        self.in_space = True if self.center_y >= SPACE_START else False
        self.above_space = True if self.center_y >= SPACE_END else False
        # Calculate current velocity from auto-maintained self.change_XXX variables and delta time
        self.velocity_x = self.change_x / delta_time  # pixels per second!
        self.velocity_y = self.change_y / delta_time
        # Calculate the force being applied to the aircraft
        force_y = self.determine_force_y(0)
        force_x = self.determine_force_x(0)

        # s = ut + (0.5)at^2
        self.change_x = self.velocity_x * delta_time + 0.5 * (force_x / self.mass) * (delta_time ** 2)
        self.change_y = self.velocity_y * delta_time + 0.5 * (force_y / self.mass) * (delta_time ** 2)

        self.center_x += self.change_x
        self.center_y += self.change_y

        # Check for collisions
        self.check_for_collision()

    def check_for_collision(self):
        # If the aircraft collides with anything, kill the sprite and create an explosion
        # Check to see if Lander has collided with the ground
        ground_collision = arcade.check_for_collision_with_lists(self, [self.scene["Terrain Centre"],
                                                                        self.scene["Terrain Edge"]])
        if ground_collision:
            if "Lander" in self.scene.name_mapping:
                self.scene.remove_sprite_list_by_name("Lander")

    def determine_force_x(self, force_x):
        # Force due to engine
        if self.engine.activated:
            force_x -= self.engine.force * math.sin(self.radians)
        return force_x

    def determine_force_y(self, force_y):
        # Force due to engine
        if self.engine.activated:
            force_y += self.engine.force * math.cos(self.radians)
        return force_y


class Lander(Aircraft):
    def __init__(self, scene: arcade.Scene, world: World):
        super().__init__(scene=scene,
                         world=world,
                         filename="images/lander.png",
                         mass=20,
                         scale=0.2)

        # Gravity only applies when we're not "in space"!
        self.in_space: bool = True
        # Gravity applies pretty heavily if someone tries to fly off into space
        self.above_space: bool = False
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
            elif "Lander" in self.scene.name_mapping:
                self.scene.remove_sprite_list_by_name("Lander")

    def determine_force_y(self, force_y):
        if self.above_space:
            # If someone tries to fly off into deep space, bring them back before they get lost ...
            force_y -= self.mass * 5 * (self.center_y - SPACE_END)
        if not self.in_space:
            # When not in the allowed(!) region of space, there's the world's gravity ...
            force_y -= self.mass * self.world.gravity
        # force due to engine
        if self.engine.activated:
            force_y += self.engine.force * math.cos(self.radians)
        return force_y

    def draw_landing_angle_guide(self):
        length = (6 * self.height)
        y = self.center_y + length * math.cos(self.max_landing_angle * math.pi / 180)
        x_left = self.center_x - length * math.sin(self.max_landing_angle * math.pi / 180)
        x_right = self.center_x + length * math.sin(self.max_landing_angle * math.pi / 180)
        arcade.draw_polygon_filled(point_list=[(x_left, y), (self.center_x, self.center_y), (x_right, y)], color=(*arcade.color.WHITE_SMOKE, 20))


