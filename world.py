import arcade
import random
from typing import Union, Tuple
from constants import WORLD_WIDTH, WORLD_HEIGHT, BACKGROUND_COLOR
import copy


class World:
    def __init__(self,
                 sky_color: Union[Tuple[int, int, int], arcade.color] = None,
                 ground_color: Union[Tuple[int, int, int], arcade.color] = None,
                 gravity: int = None,
                 star_count: int = None,
                 hill_height: float = None,
                 hill_width: float = None):
        self.sky_color = sky_color if sky_color else random.choices(range(256), k=3)
        self.ground_color = ground_color if ground_color else random.choices(range(256), k=3)
        self.gravity = gravity if gravity is not None else random.randint(20, 200)
        self.star_count = star_count if star_count is not None else random.randint(300, 1500)
        # Terrain attributes
        self.hill_height = hill_height if hill_height is not None else random.randint(20, 100) / 100
        self.hill_width = hill_width if hill_width is not None else random.randint(20, 100) / 100
        self.width, self.height = arcade.window_commands.get_display_size()

        # Not everything is a sprite!  But I don't need to detect collisions with everything, so that's ok.
        # Will have a list of shapes associated with the world that get drawn but can't be interacted with
        self.background_shapes = arcade.ShapeElementList()
        self.background_shapes.append(self.get_sky_to_space_fade_rectangle())
        for _ in range(self.star_count):
            self.background_shapes.append(self.get_star())
        # Perhaps some kind of background
        # Just needs to be obviously distinguishable from the foreground, which we need to "land" on
        # TODO

        # The foreground
        self.terrain_centre, self.terrain_edge = self.get_terrain()

    def get_terrain(self) -> arcade.SpriteList:
        def get_rect(x, max_x):
            height = max(50, int(random.randint(30, int((1/3) * WORLD_HEIGHT)) * self.hill_height))
            width = min(int(random.randint(100, 500) * self.hill_width), max_x - x)
            rect = arcade.SpriteSolidColor(width=width, height=height, color=self.ground_color)
            rect.bottom = 0
            rect.left = x
            return rect

        terrain_centre = arcade.SpriteList()
        terrain_edge = arcade.SpriteList()

        # Bunch of rectangle sprites from left to right
        x = 0
        while x < 2 * self.width:
            left_edge_rect = get_rect(x, max_x=2 * self.width)
            right_edge_rect = copy.copy(left_edge_rect)
            right_edge_rect.left = WORLD_WIDTH - 2 * self.width + x
            terrain_edge.append(left_edge_rect)
            terrain_edge.append(right_edge_rect)
            x += left_edge_rect.width
        while x < WORLD_WIDTH - 2 * self.width:
            rect = get_rect(x, max_x=WORLD_WIDTH - self.width)
            terrain_centre.append(rect)
            x += rect.width

        # I want a wrap around effect, so that you can endlessly fly sideways and it's a bit like you're just going round the world
        # To do this, I need an extra camera width on the end of the world, the matches the first camera width

        return terrain_centre, terrain_edge

    def get_star(self):
        # Stars in the sky ...
        x = random.randrange(WORLD_WIDTH)
        y = random.randrange(int((2 / 3) * WORLD_HEIGHT), WORLD_HEIGHT)
        radius = random.randrange(2, 8)
        brightness = random.randrange(127, 256)
        color = (brightness, brightness, brightness)
        return arcade.create_rectangle_filled(x, y, radius, radius, color, 45)

    def get_sky_to_space_fade_rectangle(self) -> arcade.Shape:
        # A rectangle from bottom to 2/3rds screen height, with increasing transparency from bottom to top,
        # so that the sky fades into space ...
        points = ((0, 0),
                  (WORLD_WIDTH, 0),
                  (WORLD_WIDTH, int((2 / 3) * WORLD_HEIGHT)),
                  (0, int((2 / 3) * WORLD_HEIGHT)))
        colors = ((*self.sky_color, 255),
                  (*self.sky_color, 255),
                  BACKGROUND_COLOR,
                  BACKGROUND_COLOR)
        return arcade.create_rectangle_filled_with_colors(points, colors)
