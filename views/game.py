import random

import arcade
from arcade import scene

from classes.lander import Lander
from classes.world import World
from classes.landing_pad import LandingPad
from classes.missile import Missile
from constants import BACKGROUND_COLOR, WORLD_WIDTH, WORLD_HEIGHT, SPACE_START, SPACE_END

from views.menu import MenuView
from views.next_level import NextLevelView
from pyglet.math import Vec2
from uuid import uuid4
from typing import List
import itertools

class GameView(arcade.View):

    def __init__(self):
        """Initialize the game"""
        super().__init__()

        # Want to leave space at the top of the screen for the mini-map
        self.game_camera = arcade.Camera(viewport_height=int((5/6) * self.window.height))
        self.overlay_camera = arcade.Camera()
        self.scene = None
        self.lander = None
        self.world = None
        self.landing_pad = None
        self.level = None
        self.score = None

        # Mini-map related
        # Background color must include an alpha component
        self.minimap_background_colour = (*BACKGROUND_COLOR, 255)
        self.minimap_sprite_list = None
        # Texture and associated sprite to render our minimap to
        self.minimap_texture = None
        self.minimap_sprite = None

        # The HUD text
        self.fuel_text = None
        self.shield_text = None
        self.level_text = None
        self.score_text = None
        self.gravity_text = None

    def setup(self, level: int = 1, score: int = 0):
        """Get the game ready to play"""

        # Set the background color
        arcade.set_background_color(BACKGROUND_COLOR)
        # Have a camera shake on impact  (arcade.camera.shake)

        self.scene = arcade.Scene()
        self.scene.add_sprite_list("Explosions")  # These get drawn behind everything else
        self.level = level  # Ultimately want to use this to develop the game in later levels
        self.score = score
        self.world = World(camera_width=self.game_camera.viewport_width, camera_height=self.game_camera.viewport_height)
        self.lander = Lander(scene=self.scene, world=self.world)
        self.landing_pad = LandingPad(lander=self.lander, world=self.world)

        # The world's terrain spritelist - these are the rectangles making up the ground, which I need to be able
        # to detect if I've hit.
        self.scene.add_sprite_list("Terrain Left Edge", use_spatial_hash=True, sprite_list=self.world.terrain_left_edge)
        self.scene.add_sprite_list("Terrain Centre", use_spatial_hash=True, sprite_list=self.world.terrain_centre)
        self.scene.add_sprite_list("Terrain Right Edge", use_spatial_hash=True, sprite_list=self.world.terrain_right_edge)
        self.scene.add_sprite("Landing Pad", self.landing_pad)

        # Starting location of the Lander
        self.lander.center_y = int((1/2) * (SPACE_END - SPACE_START)) + SPACE_START
        self.lander.center_x = WORLD_WIDTH / 2
        self.pan_camera_to_user(1)
        self.lander.change_x = random.randint(-30, 30) / 60
        self.lander.change_y = -random.randint(10, 30) / 60
        # The lander spritelist - ship, engine and shield
        self.scene.add_sprite_list("Lander")
        for i in (self.lander, self.lander.engine, self.lander.shield):
            self.scene.add_sprite("Lander", i)

        # Let's try adding a missile
        self.missile = Missile(scene=self.scene, world=self.world)
        self.missile.center_y = self.lander.center_y
        self.missile.center_x = self.lander.center_x + 800
        self.scene.add_sprite(name="Missiles", sprite=self.missile)
        self.scene.add_sprite(name="Missiles", sprite=self.missile.engine)

        # Construct the minimap
        minimap_width = int(0.75 * self.game_camera.viewport_width)
        minimap_height = self.window.height - self.game_camera.viewport_height
        self.minimap_texture = arcade.Texture.create_empty(str(uuid4()), (minimap_width, minimap_height))
        self.minimap_sprite = arcade.Sprite(center_x=self.game_camera.viewport_width / 2,
                                            center_y=(minimap_height / 2) + self.game_camera.viewport_height,
                                            texture=self.minimap_texture)
        self.minimap_sprite_list = arcade.SpriteList()
        self.minimap_sprite_list.append(self.minimap_sprite)

        self.fuel_text, self.shield_text, self.gravity_text = self.scaled_and_centred_text(
            texts=["Fuel: XXXX", 'Shield: XXXX', 'Gravity: XXXX'],
            width=(self.window.width - self.minimap_sprite.width) // 2,
            height=int(self.minimap_sprite.height),
            centre_x=(3 * self.window.width + self.minimap_sprite.width) // 4,
            centre_y=self.window.height - self.minimap_sprite.height // 2
        )
        self.level_text, self.score_text = self.scaled_and_centred_text(
            texts=["Level: XXXX", 'Score: XXXX'],
            width=(self.window.width - self.minimap_sprite.width) // 2,
            height=int(self.minimap_sprite.height),
            centre_x=(self.window.width - self.minimap_sprite.width) // 4,
            centre_y=self.window.height - self.minimap_sprite.height // 2
            )

    @staticmethod
    def scaled_and_centred_text(texts: List[str], width: int, height: int, centre_x: int, centre_y: int) -> List[arcade.Text]:
        # Doesn't seem to be a built in function to scale lines of text to width * height in pixels.
        # This function scales the font size of each text string so they are just under the given maximum width,
        # then sets the width of them all to the smallest font size (so all lines are the same size).
        # Then the cumulative height is considered and the font size scaled down again if necessary
        def get_text_obj_with_scaled_width(text: str,
                                           font_size_increment: int = 5) -> arcade.Text:
            # Returns a text object with maximum width given the known width constraint
            text_obj = arcade.Text(
                text=text,
                start_x=0,
                start_y=0,
                color=arcade.color.WHITE,
                font_size=10,
                font_name="Kenney Pixel Square",
                anchor_x="center",
                anchor_y="top"
            )
            while text_obj.content_width < width:
                text_obj.font_size += font_size_increment
            while text_obj.content_width > width:
                text_obj.font_size -= font_size_increment

            return text_obj

        # Pick the smallest font size such that all lines are under the give width
        text_objs = [get_text_obj_with_scaled_width(t) for t in texts]
        font_size_scaled_x = min(t.font_size for t in text_objs)
        for t in text_objs:
            t.font_size = font_size_scaled_x
            t.x = centre_x

        # Now make sure text isn't taking up too much vertical space ...
        while sum(t.content_height for t in text_objs) > height:
            for t in text_objs:
                t.font_size -= 1

        # Now just a case of placing them all
        text_objs_height = sum(t.content_height for t in text_objs)
        y = centre_y + text_objs_height // 2
        for t in text_objs:
            t.y = y
            y -= t.content_height

        return text_objs

    def update_minimap(self):
        # Want a mini-map: https://api.arcade.academy/en/latest/advanced/texture_atlas.html
        def rescale_and_draw(sprites: List[arcade.Sprite], scale_multiplier: int):
            for sprite in sprites:
                sprite.scale *= scale_multiplier
                sprite.draw()
                sprite.scale /= scale_multiplier

        proj = self.game_camera.viewport_width, WORLD_WIDTH - self.game_camera.viewport_width, 0, WORLD_HEIGHT
        with self.minimap_sprite_list.atlas.render_into(self.minimap_texture, projection=proj) as fbo:
            fbo.clear(self.minimap_background_colour)
            self.world.background_shapes.draw()
            self.scene.get_sprite_list('Terrain Left Edge').draw()
            self.scene.get_sprite_list('Terrain Centre').draw()
            self.scene.get_sprite_list('Terrain Right Edge').draw()
            # Want the lander and the landing pad to stand out, rather than being tiny
            rescale_and_draw([self.lander, self.landing_pad, self.missile], 4)

    def on_update(self, delta_time: float):
        self.scene.on_update(delta_time=delta_time)

        # I want the lander to always face the mouse pointer, but we only get updates on events (eg. mouse movement)
        # ie. If the mouse is still and the ship flies past it, without further events, it will be facing in the wrong
        # direction.
        # So on mouse move event I store the mouse coordinates, and on every update (event or not) I ensure the ship
        # is facing the right way.
        if self.lander.mouse_location is not None:
            self.lander.face_point((self.lander.mouse_location + self.game_camera.position))

        # If the Lander (or its explosion) flies off the edge of the world, I want to wrap it around instantly,
        # so the user doesn't notice.
        # I have crafted the World so that the first two window.widths are the same as the last two.
        # So I pull off this trick by never letting the user get closer than 1 window.width to the edge of the world
        # - when this boundary is crossed, the user is flipped to the other side (along with all the sprites!).
        centred_on = self.lander if not self.lander.explosion else self.lander.explosion
        world_wrap_distance = WORLD_WIDTH - 2 * self.game_camera.viewport_width
        world_wrapped = False
        if centred_on.center_x >= WORLD_WIDTH - self.game_camera.viewport_width:
            camera_x = self.game_camera.position[0] - world_wrap_distance
            centred_on.center_x -= world_wrap_distance
            # In fact, we need to move every single sprite with x position >= WORLD_WIDTH - 2 * self.game_camera.viewport_width:
            for s in itertools.chain(self.scene["Missiles"], self.scene["Explosions"]):
                if s.center_x >= WORLD_WIDTH - 2 * self.game_camera.viewport_width:
                    s.center_x -= world_wrap_distance

            world_wrapped = True
        elif centred_on.center_x < self.game_camera.viewport_width:
            camera_x = self.game_camera.position[0] + world_wrap_distance
            centred_on.center_x += world_wrap_distance
            for s in itertools.chain(self.scene["Missiles"], self.scene["Explosions"]):
                if s.center_x <= 2 * self.game_camera.viewport_width:
                    s.center_x += world_wrap_distance
            world_wrapped = True
        if world_wrapped:
            # If we've gone off the edge of the world, we immediately move the camera so the user doesn't notice
            camera_position = Vec2(camera_x, self.game_camera.position[1])
            self.game_camera.move_to(camera_position, 1)
        else:
            # Otherwise we gently pan the camera around
            self.pan_camera_to_user(panning_fraction=0.04)

        # Check to see if the level's been completed!
        if self.lander.landed:
            self.window.show_view(NextLevelView(level=self.level, score=self.score))

        # Update the minimap
        self.update_minimap()

        self.fuel_text.text = f"FUEL: {self.lander.engine.fuel:.0f}"
        self.shield_text.text = f"SHIELD: {self.lander.shield.power:.0f}"
        self.level_text.text = f"LEVEL: {self.level:.0f}"
        self.score_text.text = f"SCORE: {self.score:.0f}"
        self.gravity_text.text = f"GRAVITY: {self.world.gravity:.0f}"

    def on_mouse_press(self, x, y, button, modifiers):
        self.lander.engine.angle = self.lander.angle
        if button == arcade.MOUSE_BUTTON_RIGHT:
            self.lander.shield.activate()
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.lander.engine.activate()

    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.BACKSLASH:
            self.lander.engine.activate()
        if symbol == arcade.key.Z:
            self.lander.shield.activate()
        if modifiers & arcade.key.MOD_SHIFT:
            self.lander.engine.boost(True)
        if symbol == arcade.key.R:
            # eventually seem to run out of space.
            # Found this: https://stackoverflow.com/questions/71599404/python-arcade-caches-textures-when-requested-not-to
            # So hopefully this will be fixed in Arcade 2.7
            self.setup()
        if symbol == arcade.key.ESCAPE:
            # pass self, the current view, so we can return to it (ie. when we unpause)
            menu = MenuView(game_view=self)
            self.window.show_view(menu)

    def on_key_release(self, symbol, modifiers):
        if symbol == arcade.key.BACKSLASH:
            self.lander.engine.deactivate()
        if symbol == arcade.key.Z:
            self.lander.shield.deactivate()
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

        # Centre on the lander until it blows up, then centre on it's explosion
        centre_on = self.lander if not self.lander.explosion else self.lander.explosion
        camera_x0 = centre_on.center_x - (self.game_camera.viewport_width / 2)
        camera_y0 = centre_on.center_y - (self.game_camera.viewport_height / 2)

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
        if self.landing_pad.activated and self.lander.dead is False:
            self.lander.draw_landing_angle_guide()
        # Draw game sprites
        self.scene.draw()


        # Draw the overlay - minimap, fuel, shield, etc.
        self.overlay_camera.use()
        self.minimap_sprite_list.draw()
        for text in [self.level_text, self.score_text, self.gravity_text, self.fuel_text, self.shield_text]:
            text.draw()
