import collections
import itertools
import arcade
import random
from typing import Union, Tuple
from constants import WORLD_WIDTH, WORLD_HEIGHT, BACKGROUND_COLOR, SPACE_START, SPACE_END
import copy
from collections import defaultdict


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
                 camera_height: int = None,
                 max_gravity: int = 200):
        self.scene = scene
        self.landing_pad_width_limit = landing_pad_width_limit
        self.sky_color = sky_color if sky_color else random.choices(range(256), k=3)
        self.ground_color = ground_color if ground_color else random.choices(range(256), k=3)
        self.gravity = gravity if gravity is not None else random.randint(20, max(20, max_gravity))
        # I play with the below number - it's not an exact count!  But it does set how densely the sky is populated with stars
        self.star_count = star_count if star_count is not None else random.randint(100, 600)
        # Terrain attributes
        self.hill_height = hill_height if hill_height is not None else random.randint(20, 100) / 100
        self.hill_width = hill_width if hill_width is not None else random.randint(20, 100) / 100
        self.friction_coefficient = friction_coefficient if friction_coefficient is not None else random.randint(1, 5)
        self.max_terrain_height = None
        self.camera_width = camera_width
        self.camera_height = camera_height
        # Background parallax layers
        # key is the parallax factor.  0 (closest) matches foreground, 1 (furthest away possible) is completely static
        self.background_layers: defaultdict[float, arcade.ShapeElementList] = defaultdict(arcade.ShapeElementList)

        # Not everything is a sprite!  But I don't need to detect collisions with everything, so that's ok.
        # Will have a list of shapes associated with the world that get drawn but can't be interacted with, and shove
        # them into the 'background_layers'
        self.background_layers[1].append(self.get_sky_to_space_fade_rectangle())
        # Add the stars
        self.add_stars(parallax_factors=[0.9, 0.7, 0.5])
        # Add the clouds - parallax factors chosen to interweave with the mountains
        self.add_clouds(parallax_factors=[0.9, 0.7, 0.5])



        # Background layers are used for a parallax scrolling effect
        colour1 = (random.randint(20, 100), random.randint(20, 100), random.randint(20, 100))
        colour2 = (colour1[0] + 30, colour1[1] + 30, colour1[2] + 30)
        colour3 = (colour2[0] + 30, colour2[1] + 30, colour2[2] + 30)
        parallax_factor = 0.8
        self.background_layers[parallax_factor] = self.get_mountains(parallax_factor=parallax_factor,
                                                                     colour=colour3,
                                                                     height_range=(
                                                                     int(WORLD_HEIGHT / 3), int(WORLD_HEIGHT / 2)),
                                                                     width_range=(
                                                                     int(WORLD_WIDTH / 12), int(WORLD_WIDTH / 9)),
                                                                     num_triangles=3)
        parallax_factor = 0.6
        self.background_layers[parallax_factor] = self.get_mountains(parallax_factor=parallax_factor,
                                                                     colour=colour2,
                                                                     height_range=(
                                                                     int(WORLD_HEIGHT / 4), int(WORLD_HEIGHT / 3)),
                                                                     width_range=(
                                                                     int(WORLD_WIDTH / 12), int(WORLD_WIDTH / 8)),
                                                                     num_triangles=4)

        # Find that values below about 5 results in a flicker
        # when the world wraps when going from right to left.
        # Not sure what it is, but it's a tiny thing.
        parallax_factor = 0.45
        self.background_layers[parallax_factor] = self.get_mountains(parallax_factor=parallax_factor,
                                                                     colour=colour1,
                                                                     height_range=(
                                                                     int(WORLD_HEIGHT / 6), int(WORLD_HEIGHT / 4)),
                                                                     width_range=(
                                                                     int(WORLD_WIDTH / 15), int(WORLD_WIDTH / 10)),
                                                                     num_triangles=8)

        # The foreground
        self.terrain_left_edge, self.terrain_centre, self.terrain_right_edge = self.get_terrain(self.landing_pad_width_limit)
        self.scene.add_sprite_list("Terrain Left Edge", use_spatial_hash=True, sprite_list=self.terrain_left_edge)
        self.scene.add_sprite_list("Terrain Centre", use_spatial_hash=True, sprite_list=self.terrain_centre)
        self.scene.add_sprite_list("Terrain Right Edge", use_spatial_hash=True, sprite_list=self.terrain_right_edge)

        self.max_terrain_height = max([r.height for r in itertools.chain(self.terrain_left_edge, self.terrain_centre)])

    def add_clouds(self, *, parallax_factors: list[float]):
        def get_cloud_rectangles(*, vertical_range, number_of_strips) -> list[arcade.Shape]:
            # A background rectangle, presumably white-ish in colour, that's meant to give the impression of clouds
            cloud_rectangles = []
            y_high = vertical_range[0]
            for i in range(number_of_strips):
                # So more likely to have clouds bunched together at the bottom, which is a nice effect
                y_low = random.randint(vertical_range[0], min(y_high + 200, vertical_range[1]))
                y_high = random.randint(y_low, y_low + 100)
                points = ((0, y_low),
                          (WORLD_WIDTH, y_low),
                          (WORLD_WIDTH, y_high),
                          (0, y_high))
                colors = (
                    (*arcade.color.DUTCH_WHITE, 80),
                    (*arcade.color.DUTCH_WHITE, 150),
                    (*arcade.color.WHITE_SMOKE, 150),
                    (*arcade.color.WHITE_SMOKE, 150),
                )
                cloud_rectangles.append(arcade.create_rectangle_filled_with_colors(points, colors))

                if y_high >= vertical_range[1]:
                    break
            return cloud_rectangles

        # I also want horizontal white strips (ie. a bit like clouds)
        # The clouds don't actually move in a parallax way, but I do want them to be inbetween other parallax layers ...
        # So the parallax factor I'm using here is simply for the purpose of ordering when the clouds get drawn.
        number_of_strips = random.randint(3, 8)
        vertical_range = [int((1/6) * WORLD_HEIGHT), int(0.5 * WORLD_HEIGHT)]
        cloud_rectangles = get_cloud_rectangles(vertical_range=vertical_range, number_of_strips=number_of_strips)
        for cloud in cloud_rectangles:
            factor = random.choice(parallax_factors)
            self.background_layers[factor].append(cloud)

    def add_stars(self, *, parallax_factors: list[float]):
        # Weird thing with the stars.  Initially, they were at the foreground, and as you flew past them
        # they moved much liked the ground terrain did.  But when I added the parallax layers for the mountains,
        # with the back mountains being the tallest and most likely to be on screen at the same time as the stars,
        # it looked quite weird - these mounts would barely move whilst stars zipped past.
        # I've decided it feels better to have parallax layers for the stars as well to fix this problem - even
        # thought it does now kind of look as though you're going at warp speed and whipping past actual stars
        # rather than simply moving through the sky ...
        parallax_factors = sorted(parallax_factors, reverse=True)  # from furthest away to closest
        wrapping_point = WORLD_WIDTH - 2 * self.camera_width
        for index, factor in enumerate(parallax_factors):
            background_wrapping_point = int(wrapping_point * (1 - factor))
            # Want most stars to be furthest away, hence the division by the index
            for _ in range(int(self.star_count/(index+1))):
                # The lander can get up to WORLD_HEIGHT (and even a bit higher if it tries hard enough) - I want
                # it to still see stars in the space above it.  So I go above WORLD_HEIGHT when generating stars.
                for star in self.get_star(height_range=(int((2 / 3) * WORLD_HEIGHT), int(1.25 * WORLD_HEIGHT)),
                                                          brightness_range=(127, 256),
                                                          background_wrapping_point=background_wrapping_point):
                    self.background_layers[factor].append(star)

            # Let's have fewer stars, less bright, at the top of the atmosphere, below "space"
            # Above covers 0.59 of the world height.
            # Below covers 0.104 of the world height.
            # This gives a ratio which maintains star density
            for _ in range(int(self.star_count * (0.104 / 0.59) / (index+1))):
                for star in self.get_star(height_range=(int((5 / 9) * WORLD_HEIGHT), int((2 / 3) * WORLD_HEIGHT)),
                                                          brightness_range=(50, 127),
                                                          background_wrapping_point=background_wrapping_point):
                    self.background_layers[factor].append(star)

    def get_star(self, *, height_range: Tuple[int, int], brightness_range: Tuple[int, int], background_wrapping_point: int):
        # Stars in the sky ...
        # Kind of gets one star, but also any copies needed to make the wrap around logic work
        x = random.randrange(background_wrapping_point)
        y = random.randrange(*height_range)
        brightness = random.randrange(*brightness_range)

        radius = random.randrange(2, 8)
        color = (brightness, brightness, brightness)
        # If we scroll really slowly, the background_wrapping_point is less than the width of the screen,
        # so we won't actually fill it up!  So some copies may be needed

        stars = []
        # TODO: This still isn't quite right
        while x < self.camera_width:
            stars.append(arcade.create_rectangle_filled(x, y, radius, radius, color, 45))
            x += background_wrapping_point
        stars.append(arcade.create_rectangle_filled(x, y, radius, radius, color, 45))
        return stars

    def get_mountains(self, *, parallax_factor: float,
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

        def get_mountain(*, left, height, width):
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
            colour = (max(min(colour[0], 255), 0), max(min(colour[0], 255), 0), max(min(colour[0], 255), 0))
            triangle, triangle2 = get_mountain(left=left, height=height, width=width)
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
            # Don't want a really thin hill at one end of the terrain, so check how much space we've left and increase
            # the size of the current hill if there's only a tiny hill left over
            if 0 < max_x - x - width < 100 * self.hill_width:
                width += max_x - x - width
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
        rect = get_rect(x, max_x=WORLD_WIDTH - 2 * self.camera_width, min_x=int(landing_pad_width_limit * 1.5))
        terrain_centre.append(rect)
        x += rect.width
        while x < WORLD_WIDTH - 2 * self.camera_width:
            rect = get_rect(x, max_x=WORLD_WIDTH - 2 * self.camera_width)
            terrain_centre.append(rect)
            x += rect.width

        # I want a wrap around effect, so that you can endlessly fly sideways and it's a bit like you're just going round the world
        # To do this, I need an extra camera width on the end of the world, the matches the first camera width

        return terrain_left_edge, terrain_centre, terrain_right_edge

    def get_sky_to_space_fade_rectangle(self) -> arcade.Shape:
        # A rectangle from bottom to 2/3rds screen height, with increasing transparency from bottom to top,
        # so that the sky fades into space ...
        # Because of the way the parallax background layers work, I've made this really
        # wide so it covers the whole minimap
        points = ((-WORLD_WIDTH, 0),
                  (WORLD_WIDTH, 0),
                  (WORLD_WIDTH, SPACE_START),
                  (-WORLD_WIDTH, SPACE_START))
        colors = ((*self.sky_color, 255),
                  (*self.sky_color, 255),
                  BACKGROUND_COLOR,
                  BACKGROUND_COLOR)
        return arcade.create_rectangle_filled_with_colors(points, colors)
