import arcade
import arcade.gui
from constants import SCALING
import textwrap


class HowToPlayView(arcade.View):
    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view  # When we pause game, I pass an instance of the game_view so we can return to it
        self.manager = arcade.gui.UIManager()
        self.background = arcade.load_texture("images/title_screen.png")
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

        how_to_play_text = textwrap.dedent("""
        Thank goodness you're here, pilot!
        
        There are a number of hostages, scattered across various different hostile worlds. 
        Each hostage has a special device which provides them with an (EMP-proof) shield and a breathable atmosphere, 
        but they cannot move it and so are stuck where they are on the surface!
        
        We need you to get close enough to each of them so that your transporter can beam them aboard your ship.
        Each world has a secure underground base, accessed via a landing pad - land on the landing pad and any hostages
        on board will be taken to safety.  Once all hostages have been rescued, you can move on to the next world.
        
        Some of these worlds not only have a hostile atmosphere, but also enemies that will fire upon your ship!
        Thankfully, you can attack as well as defend yourself by using your trusty shield!  
        You can also carry a single EMP (electro-magnetic pulse) charge which will disable any active shields and 
        engines it touches for a while - but ensure that when fired your own shield and engine aren't activated!
        
        You can land on the landing pad before you have rescued all the hostages - the base will immediately refill
        your fuel, recharge your shield and reload the EMP charge.  Keep an eye on your fuel and shield levels - 
        on different missions, your ship may have different capacities for these vital resources.  Also, some worlds 
        have a stronger gravitational pull than others, so you may find you burn through your fuel quickly.
        
        LANDING
        The landing pads have a status light that activates when you get close, indicating whether or not it is safe 
        enough to land.  A red status indicates your ship is over the edge, moving too quickly or too tilted - touch 
        the pad and you will crash and burn ...  A green status indicates your descent is looking good.
        The ship will provide a helpful visual indicator, showing the angular range you need to keep within for a 
        successful landing.
        
        Your first mission will simply be a landing practice with no hostages to rescue.
        We have faith in you, pilot!  

        CONTROLS
        Left mouse button / backslash key: Thrust
        Right mouse button / Z: Shield
        Middle mouse button / X: Fire the EMP
        Shift: Boost the engine (uses fuel at higher rate)
        Escape button: Pause
        R: Reset level
        """)
        text_area = arcade.gui.UITextArea(x=100,
                                          y=200,
                                          width=1000,
                                          height=800,
                                          text=how_to_play_text,
                                          text_color=(0, 0, 0, 255))

        self.v_box.add(
            arcade.gui.UITexturePane(text_area.with_space_around(left=50, right=50),
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
        left, right, bottom, top = arcade.get_viewport()
        arcade.draw_lrwh_rectangle_textured(left, bottom, right - left, top - bottom, self.background)
        self.manager.draw()
