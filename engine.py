import arcade
import math
from constants import SCALING


class Engine(arcade.Sprite):
    def __init__(self, owner: arcade.Sprite):
        super().__init__(scale=0.3 * SCALING)
        self.textures = [arcade.load_texture("images/thrust_1.png"),
                         arcade.load_texture("images/thrust_2.png")]
        self.texture = self.textures[0]
        self.owner = owner  # This is the object whose engine this is
        self.visible = False
        # Actual engine attributes (as opposed to sprite attributes)
        self.activated = False
        self.force = 5000
        self.fuel = 100

    def activate(self):
        if self.fuel:
            self.visible = True
            self.activated = True

    def deactivate(self):
        self.visible = False
        self.activated = False

    def on_update(self, delta_time: float = 1 / 60):
        # Stay centred on the lander
        self.center_x = self.owner.center_x + self.owner.height * math.sin(self.owner.radians)
        self.center_y = self.owner.center_y - self.owner.height * math.cos(self.owner.radians)
        # Flicker the texture used - doing this based on the decimal part of the remaining fuel value
        self.texture = self.textures[int((self.fuel - int(self.fuel)) * 10) % 2]
        # If activated, use up some power
        if self.activated:
            self.fuel = max(self.fuel - delta_time, 0)
            if self.fuel == 0:
                self.deactivate()