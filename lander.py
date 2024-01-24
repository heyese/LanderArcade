import arcade
import math
from constants import SCALING
from shield import Shield
from engine import Engine
from world import World

class Lander(arcade.Sprite):
    def __init__(self, world: World):
        super().__init__(filename="images/lander.png", scale=0.2 * SCALING)
        self.shield = Shield(self)
        self.engine = Engine(self)
        self.world = world
        self.mass = 20
        # Don't like the Sprite.velocity attribute, since it's obvious delta_time can vary,
        # so it's not really a velocity - it's a change in position
        self.velocity_x = 0
        self.velocity_y = 0

    def on_update(self, delta_time: float = 1 / 60):
        self.velocity_x = self.change_x / delta_time  # pixels per second!
        self.velocity_y = self.change_y / delta_time
        force_y = - self.mass * self.world.gravity
        force_x = 0
        if self.engine.activated:
            force_y += self.engine.force * math.cos(self.radians)
            force_x -= self.engine.force * math.sin(self.radians)

        # s = ut + (0.5)at^2
        self.change_x = self.velocity_x * delta_time + 0.5 * (force_x / self.mass) * (delta_time ** 2)
        self.change_y = self.velocity_y * delta_time + 0.5 * (force_y / self.mass) * (delta_time ** 2)

        self.center_x += self.change_x
        self.center_y += self.change_y