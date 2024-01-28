import random

import arcade
from lander import Lander
from world import World
from landing_pad import LandingPad
from constants import BACKGROUND_COLOR
from views.next_level import NextLevelView
from views.menu import MenuView

class GameView(arcade.View):

    def __init__(self, level: int = 1):
        """Initialize the game"""
        super().__init__()

        self.game_camera = arcade.Camera()
        self.overlay_camera = arcade.Camera()
        self.scene = None
        self.lander = None
        self.world = None
        self.landing_pad = None
        self.level = level

    def setup(self, level: int = 1):
        """Get the game ready to play"""

        # Set the background color

        arcade.set_background_color(BACKGROUND_COLOR)
        # Want sky to fade in to space, with fully space from two thirds the way up
        # https://api.arcade.academy/en/stable/examples/gradients.html#gradients

        self.level = level  # Ultimately want to use this to develop the game in later levels
        self.world = World()
        self.lander = Lander(world=self.world)
        self.landing_pad = LandingPad(lander=self.lander, world=self.world)
        self.scene = arcade.Scene()

        # The world's terrain spritelist - these are the rectangles making up the ground, which I need to be able
        # to detect if I've hit
        self.scene.add_sprite_list("Terrain", use_spatial_hash=True, sprite_list=self.world.terrain)
        self.scene.add_sprite("Terrain", self.landing_pad)
        # Starting location of the Lander
        self.lander.center_y = self.window.height - self.lander.height
        self.lander.center_x = self.window.width / 2
        self.lander.change_x = random.randint(-30, 30) / 60
        self.lander.change_y = -random.randint(10, 30) / 60

        # The lander spritelist - ship, engine and shield
        self.scene.add_sprite_list("Lander")
        for i in (self.lander, self.lander.engine, self.lander.shield):
            self.scene.add_sprite("Lander", i)

    def on_update(self, delta_time: float):
        self.scene.on_update()
        if self.lander.mouse_location is not None:
            self.lander.face_point(self.lander.mouse_location)
            self.lander.engine.angle = self.lander.angle
        # Check to see if Lander has collided with the ground
        ground_collision = arcade.check_for_collision_with_lists(self.lander,[self.scene["Terrain"]])
        if ground_collision:
            # Have we landed?
            if ground_collision[0] == self.landing_pad and self.landing_pad.safe_to_land:
                self.window.show_view(NextLevelView(self.level))
                return
            # We've blown up
            if "Lander" in self.scene.name_mapping:
                self.scene.remove_sprite_list_by_name("Lander")

    def on_mouse_press(self, x, y, button, modifiers):
        self.lander.engine.angle = self.lander.angle
        if button == arcade.MOUSE_BUTTON_RIGHT:
            self.lander.shield.activate()
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.lander.engine.activate()

    def on_key_press(self, symbol, modifiers):
        if modifiers & arcade.key.MOD_SHIFT:
            self.lander.engine.boost(True)
        if symbol == arcade.key.R:
            # Restart
            self.setup()
        if symbol == arcade.key.ESCAPE:
            # pass self, the current view, so we can return to it (ie. when we unpause)
            menu = MenuView(game_view=self)
            self.window.show_view(menu)

    def on_key_release(self, symbol, modifiers):
        if not modifiers & arcade.key.MOD_SHIFT:
            self.lander.engine.boost(False)

    def on_mouse_release(self, x, y, button, modifiers):
        self.lander.engine.angle = self.lander.angle
        if button == arcade.MOUSE_BUTTON_RIGHT:
            self.lander.shield.deactivate()
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.lander.engine.deactivate()

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        # angle Lander at the mouse
        self.lander.mouse_location = (x, y)

    def on_draw(self):
        """Draw all game objects"""
        arcade.start_render()
        # Draw the game objects
        self.game_camera.use()
        # Draw game non-sprites
        self.world.background_shapes.draw()  # This is not a sprite, so not covered by scene.draw()
        if self.landing_pad.activated:
            self.lander.draw_landing_angle_guide()
        # Draw game sprites
        self.scene.draw()

        # Draw the overlay - fuel, shield, etc.
        self.overlay_camera.use()
        arcade.draw_text(f"Level: {self.level}  Shield: {int(self.lander.shield.power)}  Fuel: {int(self.lander.engine.fuel)}  Lander angle: {self.lander.angle:.1f}  Gravity: {self.world.gravity}", 10, 30, arcade.color.BANANA_YELLOW, 20)

