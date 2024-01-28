import arcade
from views.menu import MenuView
#  Views for instructions, game over, etc. https://api.arcade.academy/en/stable/tutorials/views/index.html
#  Camera for GUI overlay: https://api.arcade.academy/en/stable/examples/sprite_move_scrolling.html#sprite-move-scrolling
#  Scene - useful for ordering when sprites get drawn
from constants import WORLD_WIDTH, WORLD_HEIGHT, BACKGROUND_COLOR


class ResizableWindow(arcade.Window):
    def on_resize(self, width, height):
        """https://api.arcade.academy/en/latest/examples/resizable_window.html"""
        super().on_resize(width, height)


if __name__ == "__main__":
    window = ResizableWindow(title="Lander Arcade", width=WORLD_WIDTH, height=WORLD_HEIGHT, resizable=True)
    menu_view = MenuView()
    window.show_view(menu_view)
    arcade.run()
