import random

import arcade
from arcade import Scene

import constants
from classes.lander import Lander
from classes.world import World
from classes.landing_pad import LandingPad
from classes.hostage import Hostage
from classes.missile_launcher import MissileLauncher, SuperMissileLauncher
from classes.explosion import Explosion
from constants import BACKGROUND_COLOR, WORLD_WIDTH, WORLD_HEIGHT, SPACE_START, SPACE_END, SCALING
import collisions

from views.menu import MenuView
from views.next_level import NextLevelView
from pyglet.math import Vec2
from uuid import uuid4
from typing import List
from pathlib import Path


class GameView(arcade.View):

    def __init__(self):
        """Initialize the game"""
        super().__init__()

        # Want to leave space at the top of the screen for the mini-map
        self.game_camera = arcade.Camera(viewport_height=int((5/6) * self.window.height))
        constants.GAME_OBJECTS["camera"] = self.game_camera
        self.overlay_camera = arcade.Camera()
        self.scene = None
        self.lander = None
        self.world = None
        self.landing_pad = None
        self.level = None
        self.level_config = None
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
        self.hostages_text = None
        self.level_text = None
        self.score_text = None
        self.gravity_text = None
        self.fps_text = None
        self.pos_text = None
        self.timer = 0

        # Sounds
        self.level_complete = arcade.load_sound(Path('sounds/level_complete.mp3'))

    def setup(self, level: int = 1, score: int = 0):
        """Get the game ready to play"""

        # Set the background color
        arcade.set_background_color(BACKGROUND_COLOR)

        self.scene = arcade.Scene()

        # Adding spritelists now to get the ordering I want, and so that it's easy to see all of them in one go!
        # If we draw the engines before their owners, the angles aren't quite right
        self.scene.add_sprite_list("Explosions")
        self.scene.add_sprite_list("Lander")
        self.scene.add_sprite_list("Missiles")
        self.scene.add_sprite_list("Air Enemies")
        self.scene.add_sprite_list("Disabled Shields")
        self.scene.add_sprite_list('Engines')
        self.scene.add_sprite_list("Terrain Left Edge", use_spatial_hash=True)
        self.scene.add_sprite_list("Terrain Centre", use_spatial_hash=True)
        self.scene.add_sprite_list("Terrain Right Edge", use_spatial_hash=True)
        self.scene.add_sprite_list("Ground Enemies", use_spatial_hash=True)
        self.scene.add_sprite_list("Hostages", use_spatial_hash=True)
        self.scene.add_sprite_list("Landing Pad", use_spatial_hash=True)
        self.scene.add_sprite_list("Shields")

        self.level = level  # Ultimately want to use this to develop the game in later levels
        self.score = score
        self.level_config = constants.get_level_config(level)
        # Tied myself up in knots here.  I want to ensure there is a hill wide enough in the world for the
        # landing pad.  But the landing pad width depends on the lander width, and I pass the world in when
        # creating the lander ... Rather than sort that out, for now I'm just hard coding a number that's large
        # enough and passing that in!
        landing_pad_width_limit = 200
        self.world = World(scene=self.scene, camera_width=self.game_camera.viewport_width,
                           camera_height=self.game_camera.viewport_height,
                           landing_pad_width_limit=landing_pad_width_limit,
                           max_gravity=self.level_config.max_gravity)

        self.lander = Lander(scene=self.scene,
                             world=self.world,
                             fuel=self.level_config.fuel,
                             shield_charge=self.level_config.shield,
                             camera=self.game_camera)
        # Not sure of the best pattern to do this, but most of the sound functions depend on the lander.  I don't
        # want to always be having to pass it in - I want the object accessible in general in the module
        # So I set it here, just after having created it!
        constants.GAME_OBJECTS["lander"] = self.lander

        landing_pad_width = int(2 * self.lander.width)
        if landing_pad_width > landing_pad_width_limit:
            print("Your hardcoded value for the landing pad width limit isn't large enough!")
            return
        landing_pad_height = int(0.3 * landing_pad_width)
        self.landing_pad = LandingPad(scene=self.scene, lander=self.lander, world=self.world,
                                      width=landing_pad_width,
                                      height=landing_pad_height)

        # Starting location of the Lander
        self.lander.center_y = int((1/2) * (SPACE_END - SPACE_START)) + SPACE_START
        self.lander.center_x = WORLD_WIDTH / 2
        self.pan_camera_to_lander(1)
        self.lander.change_x = random.randint(-30, 30) / 60
        self.lander.change_y = -random.randint(10, 30) / 60

        # Add the missile launchers
        for i in range(self.level_config.missile_launchers):
            MissileLauncher(scene=self.scene, world=self.world, camera=self.game_camera)

        for i in range(self.level_config.shielded_missile_launchers):
            MissileLauncher(scene=self.scene, world=self.world, camera=self.game_camera, shield=True)

        for i in range(self.level_config.super_missile_launchers):
            SuperMissileLauncher(scene=self.scene, world=self.world, camera=self.game_camera)

        # Add the hostages
        for i in range(self.level_config.hostages):
            Hostage(scene=self.scene, world=self.world, lander=self.lander, camera=self.game_camera)

        # Construct the minimap
        minimap_width = int(0.75 * self.game_camera.viewport_width)
        minimap_height = self.window.height - self.game_camera.viewport_height
        self.minimap_texture = arcade.Texture.create_empty(str(uuid4()), (minimap_width, minimap_height))
        self.minimap_sprite = arcade.Sprite(center_x=self.game_camera.viewport_width / 2,
                                            center_y=(minimap_height / 2) + self.game_camera.viewport_height,
                                            texture=self.minimap_texture)
        self.minimap_sprite_list = arcade.SpriteList()
        self.minimap_sprite_list.append(self.minimap_sprite)

        self.fuel_text, self.shield_text, self.gravity_text, self.pos_text = self.scaled_and_centred_text(
            texts=["Fuel: XXXX", 'Shield: XXXX', 'Gravity: XXXX', 'Pos: XXXX'],
            width=(self.window.width - self.minimap_sprite.width) // 2,
            height=int(self.minimap_sprite.height),
            centre_x=(3 * self.window.width + self.minimap_sprite.width) // 4,
            centre_y=self.window.height - self.minimap_sprite.height // 2
        )
        self.level_text, self.score_text, self.hostages_text, self.fps_text = self.scaled_and_centred_text(
            texts=["Level: XXXX", 'Score: XXXX', 'Hostages: X', 'FPS: XXXX'],
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

        def rescale_and_draw(sprite_lists: List[arcade.SpriteList], scale_multiplier: int):
            for sprite_list in sprite_lists:
                for sprite in sprite_list:
                    sprite.scale *= scale_multiplier
                    # In the game, if the lander is at either end of the map, I keep other sprites in that same area,
                    # so that they stay on the screen.
                    # ie. I let other sprites be sprite < self.game_camera.viewport_width and sprite > WORLD_WIDTH - self.game_camera.viewport_width
                    # But for the mini-map, I always want them to wrap at the "correct" time
                    old_center_x = sprite.center_x
                    if sprite.center_x > WORLD_WIDTH - self.game_camera.viewport_width:
                        sprite.center_x -= WORLD_WIDTH - 2 * self.game_camera.viewport_width
                    elif sprite.center_x < self.game_camera.viewport_width:
                        sprite.center_x += WORLD_WIDTH - 2 * self.game_camera.viewport_width
                    sprite.draw()
                    sprite.center_x = old_center_x
                    sprite.scale /= scale_multiplier

        # I show the repeated terrain in the minimap - I think this makes the most sense
        proj = self.game_camera.viewport_width, WORLD_WIDTH - self.game_camera.viewport_width, 0, WORLD_HEIGHT
        with self.minimap_sprite_list.atlas.render_into(self.minimap_texture, projection=proj) as fbo:
            fbo.clear(self.minimap_background_colour)
            for parallax_factor in sorted(self.world.background_layers.keys(), reverse=True):
                self.world.background_layers[parallax_factor].draw()
            for name in ('Terrain Left Edge', 'Terrain Centre', 'Terrain Right Edge'):
                self.scene.get_sprite_list(name).draw()
            # Want the lander and the landing pad to stand out, rather than being tiny
            rescale_and_draw([self.scene[name] for name in ("Lander",
                                                            "Landing Pad",
                                                            "Air Enemies",
                                                            "Missiles",
                                                            "Ground Enemies",
                                                            "Hostages",
                                                            )], 6)

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
        # I wrap other sprites in the same way, ensuring they are always (when relevant) on the same side of
        # the world as the lander

        # First, just deal with sprite positions.  Then consider the camera.
        # Landing pad is effectively terrain.  Shields and Engines move themselves, as centred on owner
        non_terrain_spritelist_names = [
                                        "Lander",  # Important lander is first in the list
                                        "Missiles",
                                        "Air Enemies",
                                        "Ground Enemies",
                                        "Explosions",
                                        "Hostages",
                                        "Landing Pad"]

        non_terrain_spritelists = [self.scene[i] for i in non_terrain_spritelist_names]
        non_terrain_sprites = [s for i in non_terrain_spritelists for s in i]
        # Flip all sprites from one side to the other
        screen_width = self.game_camera.viewport_width
        for s in non_terrain_sprites:
            if s.center_x < screen_width:
                s.center_x += WORLD_WIDTH - 2 * screen_width
            elif s.center_x > WORLD_WIDTH - screen_width:
                s.center_x -= WORLD_WIDTH - 2 * screen_width
        # But if the lander is in the first or last 2 viewport_widths, we ensure the lander can see them
        if self.lander.center_x < 2 * screen_width:
            for s in [i for i in non_terrain_sprites
                      if WORLD_WIDTH - 2 * screen_width <= i.center_x + i.width / 2]:
                s.center_x -= WORLD_WIDTH - 2 * screen_width
        elif WORLD_WIDTH - 2 * screen_width <= self.lander.center_x:
            for s in [i for i in non_terrain_sprites
                      if 2 * screen_width >= i.center_x - i.width / 2]:
                s.center_x += WORLD_WIDTH - 2 * screen_width

        # If we've wrapped the lander to the other side of the world, we move the camera instantly
        if abs(self.lander.center_x - self.game_camera.position[0]) > WORLD_WIDTH - 4 * screen_width:
            if self.lander.center_x > self.game_camera.position[0]:
                new_x_position = self.game_camera.position[0] + WORLD_WIDTH - 2 * screen_width
            else:
                new_x_position = self.game_camera.position[0] - (WORLD_WIDTH - 2 * screen_width)
            new_position = Vec2(new_x_position + self.lander.change_x,
                                self.game_camera.position[1] + self.lander.change_y)
            self.game_camera.move_to(new_position, 1)
        else:
            # Gently pan the camera around after the lander
            self.pan_camera_to_lander(panning_fraction=0.04)

        # Check to see if the level's been completed!
        if self.lander.landed and len(self.scene['Hostages']) == 0:
            arcade.play_sound(self.level_complete)
            self.window.show_view(NextLevelView(level=self.level, score=self.score))

        # Update the minimap
        self.update_minimap()

        self.fuel_text.text = f"FUEL: {self.lander.engine.fuel:.0f}"
        self.shield_text.text = f"SHIELD: {self.lander.shield.charge:.0f}"
        self.level_text.text = f"LEVEL: {self.level:.0f}"
        self.score_text.text = f"SCORE: {self.score:.0f}"
        self.gravity_text.text = f"GRAVITY: {self.world.gravity:.0f}"
        self.hostages_text.text = f"HOSTAGES: {len(self.scene['Hostages'])}"
        self.fps_text.text = f"FPS: {arcade.get_fps():.0f}"
        self.pos_text.text = f"Pos: {self.lander.center_x:.0f}, {self.lander.center_y:.0f}"

        # Check for collisions
        collisions.check_for_collisions(self.scene, self.game_camera, self.world)

        # Parallax scrolling of the backgrounds
        # I find the updating the backgrounds in the on_update() function causes a slight flicker as you cross the
        # camera_width boundary - but that goes away if I move the update to the on_draw() function!
        # I've not worked out why, but there you go.  Parallax background position updates are done alongside the draw().

        # Just for testing - let's have a regular explosion
        # self.timer += delta_time
        # if self.timer > 10:
        #     self.timer = 0
        #     Explosion(scene=self.scene,
        #               world=self.world,
        #               camera=self.game_camera,
        #               mass=50,
        #               scale=0.2 * SCALING,
        #               radius_initial=int(self.lander.height) // 2,
        #               radius_final=int(self.lander.height) * 8,
        #               lifetime=4,  # seconds
        #               # Force here is what's applied to airborne objects that are
        #               # within the explosion (and presumably shielded!).
        #               # Say gravity is 100, lander mass is 20, so gravitational force
        #               # is f = ma -> 2000.
        #               # So trying to get a feel for what the right value should be,
        #               # but 4000 is double the kind of average gravitational pull
        #               force=4000,  # was 20
        #               velocity_x=0,
        #               velocity_y=0,
        #               center_x=3000,
        #               center_y=1000,
        #               owner=None)

    def on_mouse_press(self, x, y, button, modifiers):
        self.lander.engine.angle = self.lander.angle
        if button == arcade.MOUSE_BUTTON_RIGHT:
            self.lander.shield.activate()
            self.lander.trying_to_activate_shield = True
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.lander.engine.activate()

    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.BACKSLASH:
            self.lander.engine.activate()
        if symbol == arcade.key.Z:
            self.lander.shield.activate()
            self.lander.trying_to_activate_shield = True
        if modifiers & arcade.key.MOD_SHIFT:
            self.lander.engine.boost(True)
        if symbol == arcade.key.R:
            # eventually seem to run out of space.
            # Found this: https://stackoverflow.com/questions/71599404/python-arcade-caches-textures-when-requested-not-to
            # So hopefully this will be fixed in Arcade 2.7
            self.setup(level=self.level)
        if symbol == arcade.key.ESCAPE:
            # pass self, the current view, so we can return to it (ie. when we unpause)
            menu = MenuView(game_view=self)
            self.window.show_view(menu)

    def on_key_release(self, symbol, modifiers):
        if symbol == arcade.key.BACKSLASH:
            self.lander.engine.deactivate()
        if symbol == arcade.key.Z:
            self.lander.shield.deactivate()
            self.lander.trying_to_activate_shield = False
        if not modifiers & arcade.key.MOD_SHIFT:
            self.lander.engine.boost(False)

    def on_mouse_release(self, x, y, button, modifiers):
        self.lander.engine.angle = self.lander.angle
        if button == arcade.MOUSE_BUTTON_RIGHT:
            self.lander.shield.deactivate()
            self.lander.trying_to_activate_shield = False
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.lander.engine.deactivate()

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> None:
        self.lander.mouse_location = Vec2(x, y)

    def pan_camera_to_lander(self, panning_fraction: float = 1.0):
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

        # Drawing the background layers in order, from furthest back to closest
        for parallax_factor in sorted(self.world.background_layers.keys(), reverse=True):
            background_layer = self.world.background_layers[parallax_factor]
            # This is not the center!!  It's mis-named in the code.  It's the left hand side!
            # Also - not I'm doing an update here, really, as well as a draw.  I find that if I move the
            # update into the on_update() function, I get a slight flicker when we cross the camera_width boundary.
            # Not sure what's happening between that function and this, but if I do the update alongside the draw here
            # it's rock solid ...
            background_layer.center_x = self.game_camera.position[0] * parallax_factor
            background_layer.draw()

        if self.landing_pad.activated and self.lander.dead is False:
            self.lander.draw_landing_angle_guide()
        self.lander.draw_tractor_bream()
        # Draw game sprites
        self.scene.draw()

        # This draws all the hit boxes.
        # Slows things down, but can be used to work out what's going on with collisions!
        # for rect in self.scene["Explosions"]:
        #     rect.draw_hit_box((100, 100, 100, 255), 10)

        # Draw the overlay - minimap, fuel, shield, etc.
        self.overlay_camera.use()
        self.minimap_sprite_list.draw()
        for text in [self.level_text, self.score_text,
                     self.gravity_text, self.fuel_text,
                     self.shield_text, self.hostages_text,
                     self.fps_text, self.pos_text]:
            text.draw()
