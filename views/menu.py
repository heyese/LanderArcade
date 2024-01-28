import arcade
import arcade.gui
from constants import SCALING


class MenuView(arcade.View):
    def __init__(self, game_view=None):
        super().__init__()
        self.game_view = game_view  # When we pause game, I pass an instance of the game_view so we can return to it
        self.manager = arcade.gui.UIManager()
        self.resume_button_added = False

        # Create a vertical BoxGroup to align buttons
        self.v_box = arcade.gui.UIBoxLayout()

        # Create the buttons
        start_button = arcade.gui.UIFlatButton(text="Start New Game", width=300 * SCALING)
        self.v_box.add(start_button.with_space_around(bottom=30 * SCALING))

        @start_button.event("on_click")
        def start(event):
            from views.game import GameView
            self.game_view = GameView()
            self.game_view.setup()
            self.window.show_view(self.game_view)

        how_to_play_button = arcade.gui.UIFlatButton(text="How to play", width=300 * SCALING)
        self.v_box.add(how_to_play_button.with_space_around(bottom=30 * SCALING))

        @how_to_play_button.event("on_click")
        def how_to_play(event):
            from views.how_to_play import HowToPlayView
            self.window.show_view(HowToPlayView(self))

        # Create a widget to hold the v_box widget, that will center the buttons
        self.manager.add(
            arcade.gui.UIAnchorWidget(
                anchor_x="center_x",
                anchor_y="center_y",
                child=self.v_box)
        )

    def on_key_press(self, key, _modifiers):
        if key == arcade.key.ESCAPE:   # resume game
            self.window.show_view(self.game_view)

    def on_show_view(self):
        self.manager.enable()
        # The "Resume Game" button is only shown if there is an existing game (ie. that's paused) to resume
        if self.game_view and not self.resume_button_added:
            resume_button = arcade.gui.UIFlatButton(text="Resume Game", width=300 * SCALING)
            self.v_box.add(resume_button.with_space_around(bottom=30 * SCALING))
            self.resume_button_added = True

            @resume_button.event("on_click")
            def resume(event):
                self.window.show_view(self.game_view)

    def on_hide_view(self):
        # Disable the UIManager when the view is hidden.
        self.manager.disable()

    def on_draw(self):
        self.clear()
        self.manager.draw()
