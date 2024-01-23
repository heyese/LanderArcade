import math

#  Views for instructions, game over, etc. https://api.arcade.academy/en/stable/tutorials/views/index.html
#  Camera for GUI overlay: https://api.arcade.academy/en/stable/examples/sprite_move_scrolling.html#sprite-move-scrolling
#  Scene - useful for ordering when sprites get drawn

# Imports
import arcade

# Constants
SCREEN_TITLE = "Lander Arcade"
SCALING = 1.0


class Lander(arcade.Sprite):
    def __init__(self):
        super().__init__(filename="images/lander.png", scale=0.2 * SCALING)
        self.shield = Shield(self)
        self.engine = Engine(self)

    def on_update(self, delta_time: float = 1 / 60):
        if self.engine.activated:
            self.change_x = self.change_x - .1 * math.sin(self.radians)
            self.change_y = self.change_y + .1 * math.cos(self.radians)
        self.center_x += self.change_x
        self.center_y += self.change_y


class Engine(arcade.Sprite):
    def __init__(self, lander: Lander):
        super().__init__(scale=0.3 * SCALING)
        self.textures = [arcade.load_texture("images/thrust_1.png"),
                    arcade.load_texture("images/thrust_2.png")]
        self.texture = self.textures[0]
        self.lander = lander
        self.visible = False
        self.fuel: int = 10
        self.activated = False

    def activate(self):
        if self.fuel:
            self.visible = True
            self.activated = True

    def deactivate(self):
        self.visible = False
        self.activated = False

    def on_update(self, delta_time: float = 1 / 60):
        # Stay centred on the lander
        self.center_x = self.lander.center_x - self.lander.height * math.sin(-self.lander.radians)
        self.center_y = self.lander.center_y - self.lander.height * math.cos(self.lander.radians)
        # Flicker the texture used - doing this based on the decimal part of the remaining fuel value
        self.texture = self.textures[int((self.fuel - int(self.fuel)) * 10) % 2]
        # If activated, use up some power
        if self.activated:
            self.fuel = max(self.fuel - delta_time, 0)
            if self.fuel == 0:
                self.deactivate()


class Shield(arcade.SpriteCircle):
    """The lander shield - a sprite that stays centred on the lander and can be activated / deactivated"""
    def __init__(self, lander: Lander):
        super().__init__(radius=int(lander.height * 2), color=arcade.color.AQUA, soft=True)
        self.lander = lander
        self.visible = False
        self.power: int = 100
        self.activated = False

    def on_update(self, delta_time: float = 1 / 60):
        # Stay centred on the lander
        self.center_x = self.lander.center_x
        self.center_y = self.lander.center_y
        # If activated, use up some power
        if self.activated:
            self.power = max(self.power - delta_time, 0)
            if self.power == 0:
                self.deactivate()

    def activate(self):
        if self.power:
            self.visible = True
            self.activated = True

    def deactivate(self):
        self.visible = False
        self.activated = False


class GameView(arcade.View):

    def __init__(self):
        """Initialize the game"""
        super().__init__()
        self.all_sprites = arcade.SpriteList()

        self.game_camera = arcade.Camera()
        self.overlay_camera = arcade.Camera()



    def setup(self):
        """Get the game ready to play"""

        # Set the background color
        arcade.set_background_color(arcade.color.BLACK)

        # Setup the player
        self.lander = Lander()
        self.lander.center_y = self.window.height / 2
        self.lander.center_x = self.window.width / 2

        self.all_sprites.extend([self.lander, self.lander.engine, self.lander.shield])

    def on_update(self, delta_time: float):
        self.all_sprites.on_update()

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_RIGHT:
            self.lander.shield.activate()
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.lander.engine.activate()

    def on_mouse_release(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_RIGHT:
            self.lander.shield.deactivate()
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.lander.engine.deactivate()

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        # angle Lander at the mouse
        self.lander.face_point((x, y))
        self.lander.engine.face_point((x, y))

    def on_draw(self):
        """Draw all game objects"""
        arcade.start_render()

        # Draw the game objects
        self.game_camera.use()
        self.all_sprites.draw()

        # Draw the overlay - fuel, shield, etc.
        self.overlay_camera.use()
        arcade.draw_text(f"Shield: {int(self.lander.shield.power)}  Fuel: {int(self.lander.engine.fuel)}  Velocity: {self.lander.velocity}", 10, 30, arcade.color.BANANA_YELLOW, 20)


if __name__ == "__main__":
    window = arcade.Window(title="Lander Arcade", fullscreen=True)
    game_view = GameView()
    game_view.setup()
    window.show_view(game_view)
    arcade.run()
