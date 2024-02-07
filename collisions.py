import arcade
from arcade import Sprite, Scene, SpriteList
from typing import Tuple
import math
from classes.landing_pad import LandingPad
from classes.lander import Lander
from classes.shield import Shield
from classes.game_object import GameObject
import itertools
from typing import List


# The coefficient of restitution epsilon (e), is the ratio of the final to initial relative speed between two objects
# after they collide. It normally ranges from 0 to 1 where 1 would be a perfectly elastic collision.
coefficient_of_restitution = {
    # Tuple[Class, Class] : coefficient
    frozenset({"Lander", "Missile"}): 0.1,
    frozenset({"Explosion", "Missile"}): 0.1,
    frozenset({"Explosion", "Lander"}): 0.1,
}


def modulus(a: Tuple[float, float]) -> float:
    return math.sqrt(a[0]**2 + a[1]**2)


def dot(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    return a[0] * b[0] + a[1] * b[1]


def normal_vector_from_pos1_to_pos2(pos1: Tuple[float, float], pos2: Tuple[float, float]) -> Tuple[float, float]:
    # Unit vector from centre of sprite1 to centre of sprite2
    x1, y1 = pos1
    x2, y2 = pos2
    n1 = (x2 - x1) / modulus((x2 - x1, y2 - y1))
    n2 = (y2 - y1) / modulus((x2 - x1, y2 - y1))
    return n1, n2


# Circular collisions (think I'm going to treat all non-terrain collisions in this way)
# https://ravnik.eu/collision-of-spheres-in-2d/
def circular_collision(sprite1: Sprite, sprite2: Sprite) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    e = coefficient_of_restitution[frozenset({sprite1.__class__.__name__, sprite2.__class__.__name__})]
    n = normal_vector_from_pos1_to_pos2(sprite1.position, sprite2.position)
    t = -n[1], n[0]  # Tangent unit vector
    u1 = sprite1.velocity_x, sprite1.velocity_y  # My sprites have velocity_x,y attributes
    u2 = sprite2.velocity_x, sprite2.velocity_y
    u1_n = dot(u1, n)
    u2_n = dot(u2, n)
    u1_t = dot(u1, t)
    u2_t = dot(u2, t)
    m1 = sprite1.mass  # My sprites have mass attribute
    m2 = sprite2.mass
    v1_t = u1_t
    v2_t = u2_t

    v1_n = (m2 / (m1 + m2)) * ((m1 / m2 - e) * u1_n + (1 + e) * u2_n)
    v2_n = (m1 / (m1 + m2)) * ((1 + e) * u1_n + (m2 / m1 - e) * u2_n)

    v1 = v1_n * n[0] + v1_t * t[0], v1_n * n[1] + v1_t * t[1]
    v2 = v2_n * n[0] + v2_t * t[0], v2_n * n[1] + v2_t * t[1]

    return v1, v2


def check_for_collisions(scene: Scene):
    terrain_spritelists = [scene["Terrain Left Edge"],
                           scene["Terrain Centre"],
                           scene["Terrain Right Edge"],
                           ]

    for sprite in itertools.chain(scene['Lander'],
                                  scene['Shields'],
                                  scene['Missiles'],
                                  #scene['Explosions'],
                                  ):
        check_for_collision_with_landing_pad(sprite, scene)
        check_for_collision_with_terrain(sprite, terrain_spritelists, scene)


def check_for_collision_with_landing_pad(sprite: GameObject, scene: Scene):
    landing_pad_spritelist = scene['Landing Pad']
    collision = arcade.check_for_collision_with_list(sprite, landing_pad_spritelist)
    if collision:
        landing_pad: LandingPad = collision[0]
        # Lander and LandingPad
        # If we're the lander and the thing we've collided with is the landing pad,
        # and it wasn't safe to land - we explode!  (LandingPad code takes care of the actual landing)
        if sprite in scene['Lander'].sprite_list:
            lander: Lander = sprite
            if landing_pad.safe_to_land:
                lander.landed = True
                return
        if sprite in scene['Shields'].sprite_list:
            shield: Shield = sprite
            if shield.activated:
                # Bounce in some way
                # Not perfect, but for now just going to bounce back up!
                # TODO: Fix this - we get stuck if we don't come from above or below
                shield.owner.change_y *= -1
            return
        # If we aren't the lander landing, and we're not a shield, we're dead.
        sprite.die()


def check_for_collision_with_terrain(sprite: Sprite, terrain: List[SpriteList], scene: Scene):
    if sprite in scene['Shields'].sprite_list:
        shield: Shield = sprite
        # If a shield isn't activated, it's also not visible and not really meant to be there
        # Let's return now before any work is done
        if not shield.activated:
            return

    collision_with_terrain = arcade.check_for_collision_with_lists(sprite, terrain)
    if collision_with_terrain:

        # Shield and the Terrain
        # If an object has an activated shield, then it bounces ...
        # Already checked above that shield is activated.
        if sprite in scene['Shields'].sprite_list:
            shield: Shield = sprite
            r1, r2, r3 = get_left_centre_right_terrain_rectangles(sprite, scene)
            # we've either hit the right hand side of r1, the top of r2 or the left hand side of r3.
            if r1.right >= shield.left or r3.left <= shield.right:
                shield.owner.velocity_x *= -1
            if r2.top >= shield.bottom:
                shield.owner.velocity_y *= -1
            # Or we've bumped into a corner - no idea how to handle that yet ...


def get_left_centre_right_terrain_rectangles(sprite: Sprite, scene: Scene):
    # So I want the three ground rects - directly underneath, and left and right
    # Since rects are in order from left to right, this shouldn't be hard
    r1, r2, r3 = None, None, None
    for r in itertools.chain(scene["Terrain Left Edge"],
                             scene["Terrain Centre"],
                             scene["Terrain Right Edge"]):
        r1, r2, r3 = r2, r3, r
        if not r1:
            continue
        if r1.right <= sprite.center_x <= r3.left:
            break
    return r1, r2, r3


# def check_for_collision(sprite1: Sprite, sprite2: Sprite, scene: Scene) -> bool:
#     # If the aircraft collides with anything, kill the sprite and create an explosion
#     collision_with_terrain = arcade.check_for_collision_with_lists(self, [self.scene["Terrain Left Edge"],
#                                                                           self.scene["Terrain Centre"],
#                                                                           self.scene["Terrain Right Edge"]])
#
#     collision_in_air = arcade.check_for_collision_with_lists(self, [self.scene["Missiles"],
#                                                                     self.scene["Explosions"]])
#     # Basically, if two things collide and a force field isn't involved,
#     # there's an explosion, unless:
#     #  * it's the lander landing on the landing pad
#     #  * possibly in the future, it's the lander rescuing someone?
#     #  * Explosions don't explode when colliding with something else, but the something else does
#
#     # In a collision, I explode one party and assume the explosion will kill the other, but if it's quick
#     # that might not happen.  So I place a marker!
#     if self.collided is True:
#         self.die()
#         return
#
#     if collision_in_air or collision_with_terrain:
#         # In general, with a pair of objects in a collision, both explode. One immediately, and then
#         # the explosion of the first catches this bit of code in the other.
#         # Occasionally it's so quick that doesn't happen, so (if it's not a Shield), I tag the other object
#         # so it knows it must explode as well!
#         collided_with = collision_in_air[0] if collision_in_air else collision_with_terrain[0]
#         if collided_with.__class__.__name__ != "Shield":
#             collided_with.collided = True
#         if collision_in_air:
#             v1, v2 = circular_collision(self, collided_with)
#             self.velocity_x, self.velocity_y = v1
#             collided_with.velocity_x, collided_with.velocity_y = v2
#         else:
#             # If we're the lander and the thing we've collided with is the landing pad,
#             # just ignore.  The lander code can deal with that
#             if ((self.__class__ == "Lander" and collided_with.__class__ == 'LandingPad')
#                     or self.__class__ == "Explosion"):
#                 return
#
#         self.die()

