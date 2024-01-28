import arcade
import arcade.gui
from constants import SCALING


class HowToPlayView(arcade.View):
    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view  # When we pause game, I pass an instance of the game_view so we can return to it
        self.manager = arcade.gui.UIManager()
        bg_tex = arcade.load_texture(":resources:gui_basic_assets/window/grey_panel.png")
        # Create a vertical BoxGroup to align buttons
        self.v_box = arcade.gui.UIBoxLayout()

        # Create the buttons
        back_button = arcade.gui.UIFlatButton(text="Back to menu", width=300 * SCALING)
        self.v_box.add(back_button.with_space_around(bottom=30 * SCALING))

        @back_button.event("on_click")
        def back(event):
            self.clear()
            self.window.show_view(self.menu_view)

        how_to_play_text = """
        The aim is to land the Lander onto the Landing pad.  You must be going slow enough, be completely over the Landing pad and at a safe angle!\n
        Left mouse button: Thrust
        Right mouse button: Shield
        Shift: Boost the engine (uses fuel at higher rate)
        Escape button: Pause
        """
        text_area = arcade.gui.UITextArea(x=100,
                               y=200,
                               width=500,
                               height=500,
                               text=how_to_play_text,
                               text_color=(0, 0, 0, 255))

        self.v_box.add(
            arcade.gui.UITexturePane(text_area.with_space_around(right=20),
                          tex=bg_tex,
                          padding=(10, 10, 10, 10)
            ))

        # Create a widget to hold the v_box widget, that will center the buttons
        self.manager.add(
            arcade.gui.UIAnchorWidget(
                anchor_x="center_x",
                anchor_y="center_y",
                child=self.v_box)
        )

    def on_key_press(self, key, _modifiers):
        self.clear()
        self.window.show_view(self.menu_view)

    def on_show_view(self):
        self.manager.enable()

    def on_hide_view(self):
        # Disable the UIManager when the view is hidden.
        self.manager.disable()

    def on_draw(self):
        arcade.start_render()
        self.manager.draw()
