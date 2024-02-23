import itertools
import arcade
import random
from typing import Union, Tuple
from constants import WORLD_WIDTH, WORLD_HEIGHT, BACKGROUND_COLOR, SPACE_START, SPACE_END
import copy


class World:
    def __init__(self,
                 scene: arcade.Scene,
                 landing_pad_width_limit: int,
                 sky_color: Union[Tuple[int, int, int], arcade.color] = None,
                 ground_color: Union[Tuple[int, int, int], arcade.color] = None,
                 gravity: int = None,
                 friction_coefficient: float = None,
                 star_count: int = None,
                 hill_height: float = None,
                 hill_width: float = None,
                 camera_width: int = None,
                 camera_height: int = None):
        self.scene = scene
        self.landing_pad_width_limit = landing_pad_width_limit
        self.sky_color = sky_color if sky_color else random.choices(range(256), k=3)
        self.ground_color = ground_color if ground_color else random.choices(range(256), k=3)
        self.gravity = gravity if gravity is not None else random.randint(20, 200)
        self.star_count = star_count if star_count is not None else random.randint(300, 1500)
        # Terrain attributes
        self.hill_height = hill_height if hill_height is not None else random.randint(20, 100) / 100
        self.hill_width = hill_width if hill_width is not None else random.randint(20, 100) / 100
        self.friction_coefficient = friction_coefficient if friction_coefficient is not None else random.randint(1, 5)
        self.max_terrain_height = None
        self.camera_width = camera_width
        self.camera_height = camera_height

        # Not everything is a sprite!  But I don't need to detect collisions with everything, so that's ok.
        # Will have a list of shapes associated with the world that get drawn but can't be interacted with
        self.background_shapes = arcade.ShapeElementList()
        self.background_shapes.append(self.get_sky_to_space_fade_rectangle())
        for _ in range(self.star_count):
            star, star_for_world_wrap = self.get_star()
            self.background_shapes.append(star)
            if star_for_world_wrap is not None:
                self.background_shapes.append(star_for_world_wrap)

        self.background_layers: list[tuple[arcade.ShapeElementList, float]] = []  # float is the parallax factor
        colour1 = (random.randint(20, 100), random.randint(20, 100), random.randint(20, 100))
        colour2 = (colour1[0] + 30, colour1[1] + 30, colour1[2] + 30)
        colour3 = (colour2[0] + 30, colour2[1] + 30, colour2[2] + 30)
        factor = 0.9  # Factor of zero results in same scrolling as foreground
        self.background_layers.append((self.get_background_triangles(parallax_factor=factor,
                                                                     colour=colour3,
                                                                     height_range=(int(WORLD_HEIGHT / 3), int(WORLD_HEIGHT / 2)),
                                                                     width_range=(int(WORLD_WIDTH / 12), int(WORLD_WIDTH / 9)),
                                                                     num_triangles=3), factor))
        factor = 0.6
        self.background_layers.append((self.get_background_triangles(parallax_factor=factor,
                                                                     colour=colour2,
                                                                     height_range=(int(WORLD_HEIGHT / 4), int(WORLD_HEIGHT / 3)),
                                                                     width_range=(int(WORLD_WIDTH / 12), int(WORLD_WIDTH / 8)),
                                                                     num_triangles=4), factor))
        # Find that values below about 5 results in a flicker
        # when the world wraps when going from right to left.
        # Not sure what it is, but it's a tiny thing.
        factor = 0.45
        self.background_layers.append((self.get_background_triangles(parallax_factor=factor,
                                                                     colour=colour1,
                                                                     height_range=(int(WORLD_HEIGHT / 6), int(WORLD_HEIGHT / 4)),
                                                                     width_range=(int(WORLD_WIDTH / 15), int(WORLD_WIDTH / 10)),
                                                                     num_triangles=8), factor))

        # The foreground
        self.terrain_left_edge, self.terrain_centre, self.terrain_right_edge = self.get_terrain(self.landing_pad_width_limit)
        self.scene.add_sprite_list("Terrain Left Edge", use_spatial_hash=True, sprite_list=self.terrain_left_edge)
        self.scene.add_sprite_list("Terrain Centre", use_spatial_hash=True, sprite_list=self.terrain_centre)
        self.scene.add_sprite_list("Terrain Right Edge", use_spatial_hash=True, sprite_list=self.terrain_right_edge)

        self.max_terrain_height = max([r.height for r in itertools.chain(self.terrain_left_edge, self.terrain_centre)])


    def get_background_triangles(self, *, parallax_factor: float,
                                 colour: tuple[int, int, int],
                                 height_range: tuple[int, int],
                                 width_range: tuple[int, int],
                                 num_triangles: int
                                 ):
        #  It's made my brain hurt, but I'm trying to work out how wide the parallax background
        # needs to be so that it wraps when we want it to.
        # I think a lot of my confusion stems from the use of "background.center_x" on the ShapeElementList.
        # This seems to set the location of the start of the ShapeElementList - not the centre!!!!!
        # Knowing that, it all makes sense:
        # We need the last 2 camera_widths to be the same as the first.
        # So - when camera[x] = wrapping_point (= WORLD_WIDTH - 2 * camera_width), where are we on the background?
        # In general, we have: background.center_x = self.game_camera.position[0] * parallax_factor
        # So at wrapping point: background.center_x = wrapping_point * parallax_factor
        # But, as I've said above, that's not the center - it's the start.
        # To get from there to the wrapping_point, we have advanced this far: wrapping_point * (1 - parallax_factor)
        # So that is the point on the background that we want to do the wrap.

        def get_triangle(*, left, height, width):
            """Returns a triangle starting at >=x, and not ending >= max_x"""
            def brighten(colour: tuple[int, int, int]):
                values = [random.randint(50, 100) for _ in range(3)]
                colour = tuple(min(colour[a] + values[a], 255) for a in range(3))
                return colour

            width = min(width, background_wrapping_point - left)
            brightenend_colour = brighten(colour)
            triangle = arcade.create_triangles_filled_with_colors(point_list=((left, 0),
                                                                              (int(left + width/2), height),
                                                                              (left + width, 0)),
                                                                  color_list=[colour, brightenend_colour, colour])
            triangle2 = arcade.create_triangles_filled_with_colors(point_list=((left+background_wrapping_point, 0),
                                                                               (int(left+background_wrapping_point + width/2), height),
                                                                               (left+background_wrapping_point + width, 0)),
                                                                   color_list=[colour, brightenend_colour, colour])

            return triangle, triangle2

        background_triangles = arcade.ShapeElementList()
        wrapping_point = WORLD_WIDTH - 2 * self.camera_width
        background_wrapping_point = int(wrapping_point * (1 - parallax_factor))

        for i in range(num_triangles):
            height = random.randint(*height_range)
            width = random.randint(*width_range)
            left = random.randint(0, background_wrapping_point - width_range[0])
            colour = (colour[0] + random.randint(-10, 10), colour[1] + random.randint(-10, 10), colour[2] + random.randint(-10, 10))
            triangle, triangle2 = get_triangle(left=left, height=height, width=width)
            background_triangles.append(triangle)
            background_triangles.append(triangle2)
        return background_triangles

    def get_terrain(self, landing_pad_width_limit) -> Tuple[arcade.SpriteList, arcade.SpriteList, arcade.SpriteList]:
        # Generates a set of rectangles that's used as the terrain.
        # We are assured that at least one of them is wide enough for the landing pad.
        def get_rect(x, max_x, min_x=None):
            """Returns a rectangle starting at x, and not ending >= max_x"""
            height = max(50, int(random.randint(30, int((1/3) * WORLD_HEIGHT)) * self.hill_height))
            width = min(int(random.randint(100, 500) * self.hill_width), max_x - x)
            if min_x:
                # We make sure there is at least one spot for the landing pad
                width = max(min_x, width)
            rect = arcade.SpriteSolidColor(width=width, height=height, color=self.ground_color)
            rect.bottom = 0
            rect.left = x
            return rect

        terrain_centre = arcade.SpriteList()
        terrain_left_edge = arcade.SpriteList()
        terrain_right_edge = arcade.SpriteList()

        # Bunch of rectangle sprites from left to right
        x = 0
        while x < 2 * self.camera_width:
            left_edge_rect = get_rect(x, max_x=2 * self.camera_width)
            right_edge_rect = copy.copy(left_edge_rect)
            right_edge_rect.left = WORLD_WIDTH - 2 * self.camera_width + x
            terrain_left_edge.append(left_edge_rect)
            terrain_right_edge.append(right_edge_rect)
            x += left_edge_rect.width
        # Ensure there's a possible spot for the Landing Pad
        rect = get_rect(x, max_x=WORLD_WIDTH - self.camera_width, min_x=int(landing_pad_width_limit * 1.5))
        terrain_centre.append(rect)
        x += rect.width
        while x < WORLD_WIDTH - 2 * self.camera_width:
            rect = get_rect(x, max_x=WORLD_WIDTH - self.camera_width)
            terrain_centre.append(rect)
            x += rect.width

        # I want a wrap around effect, so that you can endlessly fly sideways and it's a bit like you're just going round the world
        # To do this, I need an extra camera width on the end of the world, the matches the first camera width

        return terrain_left_edge, terrain_centre, terrain_right_edge

    def get_star(self):
        # Stars in the sky ...
        x = random.randrange(WORLD_WIDTH - 2 * self.camera_width)
        y = random.randrange(int((2 / 3) * WORLD_HEIGHT), WORLD_HEIGHT)
        radius = random.randrange(2, 8)
        brightness = random.randrange(127, 256)
        color = (brightness, brightness, brightness)
        star = arcade.create_rectangle_filled(x, y, radius, radius, color, 45)
        star_copy = None
        if x < 2 * self.camera_width:
            # Due to the way we wrap the world around, stars with 2 camera_widths
            # of the start of the world should be replicated in the last 2 camera_widths
            world_wrap_distance = WORLD_WIDTH - 2 * self.camera_width
            star_copy = arcade.create_rectangle_filled(x + world_wrap_distance, y, radius, radius, color, 45)
        return star, star_copy

    def get_sky_to_space_fade_rectangle(self) -> arcade.Shape:
        # A rectangle from bottom to 2/3rds screen height, with increasing transparency from bottom to top,
        # so that the sky fades into space ...
        points = ((0, 0),
                  (WORLD_WIDTH, 0),
                  (WORLD_WIDTH, SPACE_START),
                  (0, SPACE_START))
        colors = ((*self.sky_color, 255),
                  (*self.sky_color, 255),
                  BACKGROUND_COLOR,
                  BACKGROUND_COLOR)
        return arcade.create_rectangle_filled_with_colors(points, colors)
