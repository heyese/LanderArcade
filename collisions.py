import arcade
from arcade import Sprite, Scene, SpriteList
from typing import Tuple
import math
from classes.landing_pad import LandingPad
from classes.lander import Lander
from classes.shield import Shield
from classes.game_object import GameObject
from classes.explosion import Explosion
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


def unit_vector_from_pos1_to_pos2(pos1: Tuple[float, float], pos2: Tuple[float, float]) -> Tuple[float, float]:
    # Unit vector from pos1 to pos2
    x1, y1 = pos1
    x2, y2 = pos2
    n1 = (x2 - x1) / modulus((x2 - x1, y2 - y1))
    n2 = (y2 - y1) / modulus((x2 - x1, y2 - y1))
    return n1, n2


# Circular collisions (think I'm going to treat all non-terrain collisions in this way)
# https://ravnik.eu/collision-of-spheres-in-2d/
def circular_collision(sprite1: Sprite, sprite2: Sprite) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    e = coefficient_of_restitution[frozenset({sprite1.__class__.__name__, sprite2.__class__.__name__})]
    n = unit_vector_from_pos1_to_pos2(sprite1.position, sprite2.position)
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
    terrain_spritelists = [
        # Purposefully ordered left to right, for explosion collision logic
        scene["Terrain Left Edge"],
        scene["Terrain Centre"],
        scene["Terrain Right Edge"],
    ]

    for sprite in itertools.chain(scene['Lander'],
                                  scene['Shields'],
                                  scene['Missiles'],
                                  scene['Enemies'],
                                  scene['Explosions'],
                                  ):
        check_for_collision_with_landing_pad(sprite, scene)
        check_for_collision_with_terrain(sprite, terrain_spritelists, scene)
        # TODO: check for other collisions


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
                check_for_shield_collision_with_rectangle_sprite(shield, landing_pad)
            return
        if sprite in scene['Explosions'].sprite_list:
            # TODO: explosions interacting with LandingPad
            pass
        # If we aren't the lander landing, and we're not a shield, and we're not an explosion, we die.
        sprite.die()


def check_for_collision_with_terrain(sprite: Sprite, terrain: List[SpriteList], scene: Scene):
    if sprite in scene['Shields'].sprite_list:
        shield: Shield = sprite
        # If a shield isn't activated, it's also not visible and not really meant to be there
        # Let's return now before any work is done
        if shield.activated:
            check_for_shield_collision_with_terrain(shield, terrain)
        return
    if sprite in scene['Explosions'].sprite_list:
        sprite: Explosion
        check_for_explosion_collision_with_terrain(sprite, terrain)
        return
    # I think everything else should just die ...
    sprite: GameObject
    if arcade.check_for_collision_with_lists(sprite, terrain):
        sprite.die()


def check_for_explosion_collision_with_terrain(explosion: Explosion, terrain: List[SpriteList]):
    # Rather than explosions looking like they're hovering in the air, it makes more sense to just
    # consider the centre points.  So if an explosion is on the ground, you only see the top half of it.

    # So I want the three ground rects - directly underneath, and left and right
    # Since rects are in order from left to right, this shouldn't be hard
    r1, r2, r3 = None, None, None
    for r in [i for t in terrain for i in t.sprite_list]:
        r1, r2, r3 = r2, r3, r
        if not r1:
            continue
        if r1.right <= explosion.center_x <= r3.left:
            break

    if explosion.center_y <= r2.top:
        explosion.change_y = 0
        explosion.on_ground = True
    else:
        explosion.on_ground = False
    if ((explosion.center_x <= r1.right and r1.top > explosion.center_y) or
            (explosion.center_x >= r3.left and r3.top > explosion.center_y)):
        explosion.change_x = 0


def check_for_shield_collision_with_terrain(shield: Shield, terrain: List[SpriteList]):
    collision_with_terrain = arcade.check_for_collision_with_lists(shield, terrain)
    for rect in collision_with_terrain:
        check_for_shield_collision_with_rectangle_sprite(shield, rect)


def check_for_shield_collision_with_rectangle_sprite(shield: Shield, rect: arcade.SpriteSolidColor):
    # 5 possibilities.  Bounce off left side, left corner, top side, right corner or right side.
    # Left or right side
    if (shield.center_y <= rect.top and
            ((shield.left < rect.left <= shield.right) or (shield.left <= rect.right < shield.right))):
        shield.owner.change_x *= -1
    # Top side
    elif (rect.left <= shield.center_x <= rect.right) and shield.bottom <= rect.top:
        shield.owner.change_y *= -1
    # Left and right corners
    elif (((shield.left < rect.left <= shield.right) or (shield.left <= rect.right < shield.right))
          and shield.bottom <= rect.top):
        # Want to bounce off the plane that is perpendicular to the vector from the corner to the shield centre
        # (Which is what happens when you bounce off a flat wall, except that the plane is much more obvious then!)
        if shield.left < rect.left <= shield.right:
            corner_x, corner_y = rect.left, rect.top
        else:
            corner_x, corner_y = rect.right, rect.top
        # Corner to shield centre vector (unit vector normal to plane)
        n_x, n_y = unit_vector_from_pos1_to_pos2((corner_x, corner_y), (shield.center_x, shield.center_y))
        # Tangential unit vector along plane
        t_x, t_y = -n_y, n_x
        # So want to project the existing movement vectors onto these vectors, then the tangential movement
        # is preserved and the movement along the normal vector is reversed ...
        normal_projection = dot((shield.owner.change_x, shield.owner.change_y), (n_x, n_y))
        tangential_projection = dot((shield.owner.change_x, shield.owner.change_y), (t_x, t_y))
        shield.owner.change_x = -normal_projection * n_x + tangential_projection * t_x
        shield.owner.change_y = -normal_projection * n_y + tangential_projection * t_y
        shield.center_x += -normal_projection * n_x + tangential_projection * t_x
        shield.center_y += -normal_projection * n_y + tangential_projection * t_y
        # In edge cases, we can get trapped in a rect - ie. after flipping the normal projection of our vector,
        # we're still colliding, so we then flip it again, which obviously doesn't work.
        # So below I keep pushing in the same direction until we're no longer colliding ...
        repeats = 0
        while arcade.check_for_collision(shield, rect):
            repeats += 1
            shield.owner.center_x += (-normal_projection * n_x + tangential_projection * t_x) * repeats
            shield.owner.center_y += (-normal_projection * n_y + tangential_projection * t_y) * repeats
            shield.center_x += (-normal_projection * n_x + tangential_projection * t_x) * repeats
            shield.center_y += (-normal_projection * n_y + tangential_projection * t_y) * repeats
            if repeats == 10:
                # Something's gone wrong - we're stuck!
                # Disable the shield to let the user know something's gone wrong
                shield.disable()
                break



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

