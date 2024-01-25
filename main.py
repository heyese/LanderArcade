import arcade
from lander import Lander
from world import World
from landing_pad import LandingPad
#  Views for instructions, game over, etc. https://api.arcade.academy/en/stable/tutorials/views/index.html
#  Camera for GUI overlay: https://api.arcade.academy/en/stable/examples/sprite_move_scrolling.html#sprite-move-scrolling
#  Scene - useful for ordering when sprites get drawn
from constants import WORLD_WIDTH, WORLD_HEIGHT, BACKGROUND_COLOR


class PauseView(arcade.View):
    def __init__(self, game_view):
        super().__init__()
        self.game_view = game_view

    def on_draw(self):
        # Show tip to return or reset
        arcade.draw_ellipse_filled(center_x=WORLD_WIDTH / 2,
                                   center_y=WORLD_HEIGHT / 2,
                                   width=WORLD_WIDTH / 4,
                                   height=WORLD_HEIGHT / 5,
                                   color=arcade.color.BLACK_BEAN)
        arcade.draw_text("Press Esc. to return",
                         WORLD_WIDTH / 2,
                         WORLD_HEIGHT / 2,
                         arcade.color.DUTCH_WHITE,
                         font_size=30,
                         anchor_x="center")

    def on_key_press(self, key, _modifiers):
        if key == arcade.key.ESCAPE:   # resume game
            self.window.show_view(self.game_view)


class NextLevelView(arcade.View):
    def __init__(self, level: int):
        super().__init__()
        self.next_level = level + 1

    def on_draw(self):
        # Show tip to return or reset
        arcade.draw_ellipse_filled(center_x=WORLD_WIDTH / 2,
                                   center_y=WORLD_HEIGHT / 2,
                                   width=WORLD_WIDTH / 4,
                                   height=WORLD_HEIGHT / 5,
                                   color=arcade.color.BLACK_BEAN)
        arcade.draw_text(f"Level {self.next_level}",
                         WORLD_WIDTH / 2,
                         WORLD_HEIGHT / 2,
                         arcade.color.DUTCH_WHITE,
                         font_size=30,
                         anchor_x="center")
        arcade.draw_text("Hit enter to continue ...",
                         WORLD_WIDTH / 2,
                         WORLD_HEIGHT / 2 - 30,
                         arcade.color.DUTCH_WHITE,
                         font_size=20,
                         anchor_x="center")

    def on_key_press(self, key, _modifiers):
        if key == arcade.key.ENTER:
            game_view = GameView(level=self.next_level)
            game_view.setup()
            window.show_view(game_view)


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

    def setup(self):
        """Get the game ready to play"""

        # Set the background color

        arcade.set_background_color(BACKGROUND_COLOR)
        # Want sky to fade in to space, with fully space from two thirds the way up
        # https://api.arcade.academy/en/stable/examples/gradients.html#gradients

        self.world = World()
        self.lander = Lander(world=self.world)
        self.landing_pad = LandingPad(lander=self.lander, world=self.world)
        self.scene = arcade.Scene()

        # The world's terrain spritelist - these are the rectangles making up the ground, which I need to be able
        # to detect if I've hit
        self.scene.add_sprite_list("Terrain", use_spatial_hash=True, sprite_list=self.world.terrain)
        self.scene.add_sprite("Terrain", self.landing_pad)
        # Setup the player
        self.lander.center_y = self.window.height / 2
        self.lander.center_x = self.window.width / 2

        # The lander spritelist - ship, engine and shield
        self.scene.add_sprite_list("Lander")
        for i in (self.lander, self.lander.engine, self.lander.shield):
            self.scene.add_sprite("Lander", i)

    def on_update(self, delta_time: float):
        self.scene.on_update()
        # Check to see if Lander has collided with the ground
        ground_collision = arcade.check_for_collision_with_lists(self.lander,[self.scene["Terrain"]])
        if ground_collision:
            # Have we landed?
            if ground_collision[0] == self.landing_pad and self.landing_pad.safe_to_land:
                window.show_view(NextLevelView(self.level))
                return
            # We've blown up
            if "Lander" in self.scene.name_mapping:
                self.scene.remove_sprite_list_by_name("Lander")

    def on_mouse_press(self, x, y, button, modifiers):
        self.lander.face_point((x, y))
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
            # pass self, the current view, to preserve this view's state
            pause = PauseView(self)
            self.window.show_view(pause)

    def on_key_release(self, symbol, modifiers):
        if not modifiers & arcade.key.MOD_SHIFT:
            self.lander.engine.boost(False)

    def on_mouse_release(self, x, y, button, modifiers):
        self.lander.face_point((x, y))
        self.lander.engine.angle = self.lander.angle
        if button == arcade.MOUSE_BUTTON_RIGHT:
            self.lander.shield.deactivate()
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.lander.engine.deactivate()

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        # angle Lander at the mouse
        self.lander.face_point((x, y))
        self.lander.engine.angle = self.lander.angle

    def on_draw(self):
        """Draw all game objects"""
        arcade.start_render()
        # Draw the game objects
        self.game_camera.use()
        self.world.background_shapes.draw()  # This is not a sprite, so not covered by scene.draw()
        self.scene.draw()

        # Draw the overlay - fuel, shield, etc.
        self.overlay_camera.use()
        arcade.draw_text(f"Level: {self.level}  Shield: {int(self.lander.shield.power)}  Fuel: {int(self.lander.engine.fuel)}  Lander angle: {self.lander.angle:.1f}  Gravity: {self.world.gravity}", 10, 30, arcade.color.BANANA_YELLOW, 20)


class ResizableWindow(arcade.Window):
    def on_resize(self, width, height):
        """https://api.arcade.academy/en/latest/examples/resizable_window.html"""
        super().on_resize(width, height)


if __name__ == "__main__":
    window = ResizableWindow(title="Lander Arcade", width=WORLD_WIDTH, height=WORLD_HEIGHT, resizable=True)
    game_view = GameView()
    game_view.setup()
    window.show_view(game_view)
    arcade.run()
