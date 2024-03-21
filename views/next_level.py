import arcade
import arcade.gui
from constants import SCALING


class NextLevelView(arcade.View):
    def __init__(self, level: int):
        super().__init__()
        self.manager = arcade.gui.UIManager()
        self.level = level + 1

        # Create a vertical BoxGroup to align buttons
        self.v_box = arcade.gui.UIBoxLayout()

        # Create the buttons
        start_button = arcade.gui.UIFlatButton(text=f"Start Level {self.level}", width=500 * SCALING)
        self.v_box.add(start_button.with_space_around(bottom=30 * SCALING))
        # I'm not sure how to move this import to the top level without getting a circular import ...
        from views.game import GameView
        self.game_view = GameView()
        self.game_view.setup(level=self.level)

        @start_button.event("on_click")
        def start(event):
            self.window.show_view(self.game_view)

        # Create a widget to hold the v_box widget, that will center the buttons
        self.manager.add(
            arcade.gui.UIAnchorWidget(
                anchor_x="center_x",
                anchor_y="center_y",
                child=self.v_box)
        )

    def on_key_press(self, key, _modifiers):
        if key == arcade.key.ENTER:   # resume game
            self.window.show_view(self.game_view)

    def on_show_view(self):
        self.manager.enable()

    def on_hide_view(self):
        # Disable the UIManager when the view is hidden.
        self.manager.disable()

    def on_draw(self):
        self.manager.draw()
