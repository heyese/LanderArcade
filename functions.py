import arcade
from arcade import Sprite
from pyglet.math import Vec2
from typing import Tuple
import math

# Circular collisions (think I'm going to treat all non-terrain collisions in this way)
# https://ravnik.eu/collision-of-spheres-in-2d/

# The coefficient of restitution epsilon (e), is the ratio of the final to initial relative speed between two objects
# after they collide. It normally ranges from 0 to 1 where 1 would be a perfectly elastic collision.
coefficient_of_restitution = {
    # Tuple[Class, Class] : coefficient
    frozenset({"Lander", "Missile"}): 0.2,
    frozenset({"Explosion", "Missile"}): 0.9,
    frozenset({"Explosion", "Lander"}): 0.9,
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
