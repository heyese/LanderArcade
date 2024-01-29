import random

import arcade
from lander import Lander
from world import World
from landing_pad import LandingPad
from constants import BACKGROUND_COLOR, WORLD_WIDTH
from views.next_level import NextLevelView
from views.menu import MenuView
from pyglet.math import Vec2


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

        # Want a mini-map: https://api.arcade.academy/en/latest/advanced/texture_atlas.html
        # Want the wold to be larger than the screen
        # Have a camera shake on impact  (arcade.camera.shake)

        self.level = level  # Ultimately want to use this to develop the game in later levels
        self.world = World(camera_width=self.game_camera.viewport_width, camera_height=self.game_camera.viewport_height)
        self.lander = Lander(world=self.world)
        self.landing_pad = LandingPad(lander=self.lander, world=self.world)
        self.scene = arcade.Scene()

        # The world's terrain spritelist - these are the rectangles making up the ground, which I need to be able
        # to detect if I've hit
        self.scene.add_sprite_list("Terrain Centre", use_spatial_hash=True, sprite_list=self.world.terrain_centre)
        self.scene.add_sprite_list("Terrain Edge", use_spatial_hash=True, sprite_list=self.world.terrain_edge)
        self.scene.add_sprite("Terrain Centre", self.landing_pad)
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
            self.lander.face_point((self.lander.mouse_location + self.game_camera.position))
            self.lander.engine.angle = self.lander.angle
        # Check to see if Lander has collided with the ground
        ground_collision = arcade.check_for_collision_with_lists(self.lander, [self.scene["Terrain Centre"],
                                                                               self.scene["Terrain Edge"]])
        if ground_collision:
            # Have we landed?
            if ground_collision[0] == self.landing_pad and self.landing_pad.safe_to_land:
                self.window.show_view(NextLevelView(self.level))
                return
            # We've blown up
            if "Lander" in self.scene.name_mapping:
                self.scene.remove_sprite_list_by_name("Lander")

        # If the Lander flies off the edge of the world, I want to wrap it around instantly, so the user doesn't notice.
        # I have crafted the World so that the first two window.widths are the same as the last two.
        # So I pull off this trick by never letting the user get closer than 1 window.width to the edge of the world
        # - when this boundary is crossed, the user is flipped to the other side (along with all the sprites!).
        world_wrap_distance = WORLD_WIDTH - 2 * self.game_camera.viewport_width
        world_wrapped = False
        if self.lander.center_x >= WORLD_WIDTH - self.game_camera.viewport_width:
            camera_x = self.game_camera.position[0] - world_wrap_distance
            self.lander.center_x -= world_wrap_distance
            world_wrapped = True
        elif self.lander.center_x < self.game_camera.viewport_width:
            camera_x = self.game_camera.position[0] + world_wrap_distance
            self.lander.center_x += world_wrap_distance
            world_wrapped = True
        if world_wrapped:
            # If we've gone off the edge of the world, we immediately move the camera so the user doesn't notice
            camera_position = Vec2(camera_x, self.game_camera.position[1])
            self.game_camera.move_to(camera_position, 1)
        else:
            # Otherwise we gently pan the camera around
            self.pan_camera_to_user(panning_fraction=0.04)

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
        self.lander.mouse_location = Vec2(x, y)

    def pan_camera_to_user(self, panning_fraction: float = 1.0):
        """
        Manage Scrolling
        :param panning_fraction: Number from 0 to 1. Higher the number, faster we
                                 pan the camera to the user.
        """

        # This spot would center on the user
        camera_x0 = self.lander.center_x - (self.game_camera.viewport_width / 2)
        camera_y0 = self.lander.center_y - (self.game_camera.viewport_height / 2)

        if camera_y0 < 0:
            camera_y0 = 0
        user_centered = Vec2(camera_x0, camera_y0)

        self.game_camera.move_to(user_centered, panning_fraction)

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
        arcade.draw_text(f"Level: {self.level}  Pos: {self.lander.position[0]:.2f}, {self.lander.position[1]:.2f},  Shield: {int(self.lander.shield.power)}  Fuel: {int(self.lander.engine.fuel)}  Lander angle: {self.lander.angle:.1f}  Gravity: {self.world.gravity}", 10, 30, arcade.color.BANANA_YELLOW, 20)

