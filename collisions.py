from __future__ import annotations

import random

import arcade
from arcade import Sprite, Scene, SpriteList, Camera
import constants
from typing import Tuple
from pathlib import Path
import math
import itertools
from typing import List
from pyglet.math import Vec2
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from classes.landing_pad import LandingPad
    from classes.lander import Lander
    from classes.shield import Shield
    from classes.game_object import GameObject
    from classes.explosion import Explosion
    from classes.world import World


BOUNCE_SOUNDS = [arcade.load_sound(Path(bounce_sound)) for bounce_sound in Path('sounds').glob('bounce_*.mp3')]


# The coefficient of restitution epsilon (e), is the ratio of the final to initial relative speed between two objects
# after they collide. It normally ranges from 0 to 1 where 1 would be a perfectly elastic collision.
# Default value is 0.5
coefficient_of_restitution = {
    # Tuple[Class, Class] : coefficient
    frozenset({"Lander", "Missile"}): 0.1,
    frozenset({'RocketLauncher', 'Lander'}): 0.5,
    frozenset({"Explosion", "Missile"}): 0.1,
    frozenset({"Explosion", "Lander"}): 0.1,
    frozenset({"Shield", "Explosion"}): 0.1,
    frozenset({"Shield", "Shield"}): 3.5,  # For hostages, feels about right
    frozenset({"Shield", "Missile"}): 0.1,
    frozenset({"Shield", "Lander"}): 0.8,
    frozenset({'Shield', 'RocketLauncher'}): 0.5,
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
    e = coefficient_of_restitution.get(frozenset({sprite1.__class__.__name__, sprite2.__class__.__name__}), 0.5)
    if sprite1.__class__.__name__ == 'Shield':
        sprite1 = sprite1.owner
    if sprite2.__class__.__name__ == 'Shield':
        sprite2 = sprite2.owner
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


def check_for_collisions(scene: Scene, camera: Camera, world: World):

    # Collisions with the terrain and the landing pad are one-sided collisions.
    # The terrain and landing pad are fixed and not impacted at all.
    # The same is true for collisions with the activated shields of anything on the ground.
    # LandingPad shield is special - the lander can enter into it regardless of the state of the lander's shield.
    # (I thought this was a good idea, but I might just disable this for now until the game gets going!)

    # All other collisions, except those with explosions, are treated using the circular_collision() function above.
    # ie. Effectively treated like two circles hitting each other, with mass and "coefficient of restitution" affecting
    # resultant velocities.
    # Collisions with ground enemies are treated the same way, but the ground enemy just blows up (ie. it doesn't
    # get a velocity from the impact).

    # Whenever an object without an activated shield collides with something (including an explosion), it
    # (currently) blows up (although this could change, actually - think "end boss-style aircraft").

    # Explosions pass through each other without affecting each other.
    # As above, an explosion touching a non-shielded object will cause it to blow up.
    # An explosion colliding with a shielded object exerts a force which, I think, will only affect the object it's
    # colliding with.

    terrain_spritelists = [scene[name] for name in constants.TERRAIN_SPRITELISTS]

    general_object_spritelists = [scene[name] for name in constants.GENERAL_OBJECT_SPRITELISTS]

    lander: Lander = scene['Lander'].sprite_list[0] if scene['Lander'].sprite_list else None
    landing_pad: LandingPad = scene['Landing Pad'].sprite_list[0]

    considered_collisions = set()
    # The things below can hit each other.
    # The things missed off (eg. terrain and ground enemies) can only be hit by these things
    for sprite in itertools.chain(scene['Lander'],
                                  scene['Shields'],
                                  scene['Missiles'],
                                  scene['Air Enemies'],
                                  scene['Explosions'],
                                  ):

        is_collision = False
        # Terrain / Landing pad collisions don't affect the terrain / landing pad - it's only about what hit them
        is_collision |= check_for_collision_with_landing_pad(sprite, lander=lander, landing_pad=landing_pad, scene=scene)
        is_collision |= check_for_collision_with_terrain(sprite, terrain_spritelists, scene, world)
        is_collision |= check_for_collisions_general(sprite, general_object_spritelists, scene, considered_collisions, lander, camera)

        # Not 100% sold on this, but below, if the lander has collided with something,
        # I cause a little camera shake.  It's fixed amplitude and along the movement vector of the lander,
        # which is not necessarily the same as the vector along which it was hit, so not very sophisticated
        if lander is not None and lander in {sprite, getattr(sprite, 'owner')} and is_collision:
            angle = math.atan2(lander.change_y, lander.change_x)
            vector = Vec2(5 * math.cos(angle), 5 * math.sin(angle))
            camera.shake(vector,
                         speed=0.5,
                         damping=0.7)


def check_for_collision_with_landing_pad(sprite: Sprite, lander: Lander, landing_pad: LandingPad, scene: Scene) -> bool:
    # I have realized it should only ever be the lander that interacts with the landing pad,
    # because it will have its own force field that comes on automatically and will block everything except the lander
    if sprite in scene['Ground Enemies']:
        return False
    collision = arcade.check_for_collision(sprite, landing_pad)
    sprite_collided = bool(collision)
    if collision:
        # Lander and LandingPad
        # If we're the lander and the thing we've collided with is the landing pad,
        # and it wasn't safe to land - we explode!  (LandingPad code takes care of the actual landing)
        if sprite == lander:
            if landing_pad.safe_to_land:
                lander.landed = True
                sprite_collided = False
            else:
                lander.die()
        elif sprite in scene['Shields'].sprite_list:
            shield: Shield = sprite
            if shield.activated:
                check_for_shield_collision_with_rectangle_sprite(shield, landing_pad)
            else:
                # A collision with a deactivated shield isn't a collision
                sprite_collided = False
        elif sprite not in scene['Explosions'].sprite_list:
            sprite: GameObject
            sprite.die()
        elif sprite in scene['Explosions'].sprite_list:
            explosion: Explosion = sprite
            if landing_pad.left <= explosion.center_x <= landing_pad.right and explosion.center_y <= landing_pad.top:
                explosion.change_y = 0
                explosion.on_ground = True
            else:
                explosion.on_ground = False
            if (landing_pad.top > explosion.center_y and
                    ((explosion.left <= landing_pad.left - explosion.change_x <= explosion.center_x and explosion.change_x > 0) or
                     (explosion.right >= landing_pad.right - explosion.change_x >= explosion.center_x and explosion.change_x < 0))):
                explosion.change_x = 0
    return sprite_collided


def change_pos_of_sprite_and_shield_by_vector(obj: Sprite, x: float, y: float):
    obj.center_x += x
    obj.center_y += y
    obj.shield.center_x += x
    obj.shield.center_y += y


def is_sprite_in_camera_view(sprite: Sprite, camera: Camera):
    camera_left = camera.position[0]
    camera_right = camera.position[0] + camera.viewport_width
    camera_bottom = camera.position[1]
    camera_top = camera.position[1] + camera.viewport_height
    if (sprite.right < camera_left
            or sprite.left > camera_right
            or sprite.top < camera_bottom
            or sprite.bottom > camera_top):
        return False
    return True


def check_for_collisions_general(sprite: Sprite, general_object_spritelists: List[SpriteList], scene: Scene, considered_collisions: set, lander: Lander, camera: Camera):
    # Unfortunately, I've realized that checking for all these collisions slows the game down.
    # A weakness of python arcade, that they may well fix in a later version
    # https://api.arcade.academy/en/2.5.7/arcade_vs_pygame_performance.html#collision-detection
    # I think my solution will be to simply secretly only check for non-"use_spatial_hash=True" collisions
    # when the lander can see them.  ie. Non-terrain collisions off screen just won't happen
    # Alternatively, I could simply decide that missiles can't collide with each other - that would make a significant
    # difference and probably wouldn't affect the enjoyment of the game very much
    if not is_sprite_in_camera_view(sprite=sprite, camera=camera):
        return False
    collisions = arcade.check_for_collision_with_lists(sprite, general_object_spritelists)
    sprite_collided = False
    for collision in collisions:
        # Nothing to do if the sprite and the collision object are one and the same,
        # or if one is the shield of the other,
        # or if we've already dealt with this case
        if (sprite == collision
                or (sprite.__class__.__name__ == 'Shield' and sprite.owner == collision)
                or (collision.__class__.__name__ == 'Shield' and collision.owner == sprite)
                or ((collision, sprite) in considered_collisions)):
            continue
        else:
            considered_collisions.add((sprite, collision))

        if (sprite in scene['Shields'] and not sprite.activated or
                collision in scene['Shields'] and not collision.activated):
            # When a shield isn't activated, it isn't visible, and doesn't count as a collision
            continue

        # Here I'm considering what happens where one side of the "collision" is an explosion
        # It can only be the "sprite" side, as I've not put Explosions into general_object_spritelists.
        if "Explosion" == sprite.__class__.__name__:
            # But if an object comes into contact with an explosion and doesn't have an activated shield, it blows up
            # (ie. If you're not a shield and don't have a shield, or you're not a shield and have a shield but it's
            # deactivated, then you blow up)
            if (collision.__class__.__name__ != 'Shield' and (
                    getattr(collision, 'shield', None) is None or
                    ((shield := getattr(collision, 'shield', None)) is not None and shield.activated is False))):
                collision: GameObject
                collision.die()
            # If you 'collide' with an explosion and you have an activated shield, then the explosion applies a force
            # to you.  But I don't deal with that here - that is in the on_update() in GameObject.
            continue

        sprite_collided = True
        # Is this collision between two shields, where one is a shielded ground object?
        # In that case, that shield is essentially treated like the terrain - it is fixed in place,
        # and the other object bounces off without losing energy.
        if ({"Shield"} == {sprite.__class__.__name__, collision.__class__.__name__} and
                True in {sprite.owner.on_ground, collision.owner.on_ground}):
            if sprite.owner.on_ground:
                point = (sprite.owner.center_x, sprite.owner.center_y)
                obj_1, obj_2 = collision.owner, sprite.owner
            else:
                point = (collision.owner.center_x, collision.owner.center_y)
                obj_1, obj_2 = sprite.owner, collision.owner
            collision_with_fixed_point(point_x=point[0], point_y=point[1], obj=obj_1)

            # Now - have a bug-type scenario sometimes where shields can get "stuck" together.
            # ie. We compute the bounce back vector, but it's not enough for the two objects to stop colliding,
            # so then we immediately detect another collision but then bounce the two objects back a bit closer again!
            # So I check to see if the initial change we've applied is enough, and if not, apply it again.
            i = 0
            while True:
                i += 1
                change_pos_of_sprite_and_shield_by_vector(obj=obj_1, x=obj_1.change_x, y=obj_1.change_y)
                if not arcade.check_for_collision(obj_1.shield, obj_2.shield) or obj_1.center_y < 0:
                    # If we're no longer colliding, then we can undo the last pos change, as it will get applied later.
                    change_pos_of_sprite_and_shield_by_vector(obj=obj_1, x=-obj_1.change_x, y=-obj_1.change_y)
                    break
                if obj_1.center_y < 0:
                    # Ok - something has definitely gone wrong.  We've been stuck in this while loop, applied a bunch
                    # of little nudges to our object and it's now below ground.  We obviously somehow got the wrong
                    # direction initially - I'm simply going to bump the object back in the other direction
                    print("Switched the direction of the bounce so as to stay above ground!")
                    obj_1.change_x = -obj_1.change_x
                    obj_1.change_y = -obj_1.change_y
                if i == 30:
                    raise ValueError(f"Collision trap.  Rebound vector for obj_1: (x: {obj_1.change_x}, "
                                     f"y: {obj_1.change_y}). obj_1 centre: ({obj_1.center_x}, {obj_1.center_y}). "
                                     f"obj_2 centre: ({obj_2.center_x}, {obj_2.center_y}).")

            # Two shields have bounced
            arcade.play_sound(random.choice(BOUNCE_SOUNDS))
            continue

        # This is the general collision bit.  I essentially treat a collision like two circles colliding.
        # The resultant velocities depend on the respective masses, but ground objects don't suddenly start moving.
        # (Currently I just make ground objects very heavy and don't alter their (zero) velocity,
        # although I should really ignore their mass and just make objects bounce off, I think.)
        v1, v2 = circular_collision(sprite, collision)
        for obj, velocity in [(sprite, v1), (collision, v2)]:
            if obj in scene['Shields']:
                if obj.owner.on_ground is False:
                    obj.owner.change_x, obj.owner.change_y = v1[0] * (1/60), v1[1] * (1/60),
            else:
                if obj.on_ground is False:
                    obj.change_x, obj.change_y = v1[0] * (1/60), v1[1] * (1/60)
                obj.die()

    return sprite_collided


def collision_with_fixed_point(*, point_x: int, point_y: int, obj: Sprite):
    # Point to sprite centre vector (unit vector normal to plane)
    n_x, n_y = unit_vector_from_pos1_to_pos2((point_x, point_y), (obj.center_x, obj.center_y))
    # Tangential unit vector along plane
    t_x, t_y = -n_y, n_x
    # So want to project the existing movement vectors onto these vectors, then the tangential movement
    # is preserved and the movement along the normal vector is reversed ...
    normal_projection = dot((obj.change_x, obj.change_y), (n_x, n_y))
    tangential_projection = dot((obj.change_x, obj.change_y), (t_x, t_y))
    obj.change_x = -normal_projection * n_x + tangential_projection * t_x
    obj.change_y = -normal_projection * n_y + tangential_projection * t_y


def check_for_collision_with_terrain(sprite: Sprite, terrain: List[SpriteList], scene: Scene, world: World):
    # Trying to find ways to speed up my collision checks.
    # If the sprite is above the highest mountain, it's definitely not colliding with the terrain ...
    if sprite.bottom > world.max_terrain_height:
        return False
    elif sprite in scene['Shields'].sprite_list:
        shield: Shield = sprite
        if shield.activated:
            return check_for_shield_collision_with_terrain(shield, terrain, scene)
        # If a shield isn't activated, it's also not visible and not really meant to be there
        # Let's return now before any work is done
        return False
    elif sprite in scene['Explosions'].sprite_list:
        sprite: Explosion
        check_for_explosion_collision_with_terrain(sprite, terrain)
        return False
    # I think everything else should just die ...
    elif arcade.check_for_collision_with_lists(sprite, terrain):
        sprite: GameObject
        sprite.die()
        return True
    return False


def check_for_explosion_collision_with_terrain(explosion: Explosion, terrain: List[SpriteList]):
    # Rather than explosions looking like they're hovering in the air, it makes more sense to just
    # consider the centre points.  So if an explosion is on the ground, you only see the top half of it.
    # The reason this function is different to the others is that explosions don't bounce.

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
    if ((explosion.center_x + explosion.change_x <= r1.right and r1.top > explosion.center_y) or
            (explosion.center_x + explosion.change_x >= r3.left and r3.top > explosion.center_y)):
        explosion.change_x = 0
    # Not interested in returning whether the sprite collided or not, as don't do screen shakes for explosions


def check_for_shield_collision_with_terrain(shield: Shield, terrain: List[SpriteList], scene: Scene):
    # The LandingPad and Hostages' and Ground Enemies shields are allowed to clash with the terrain
    if shield.owner in itertools.chain(*[scene[name].sprite_list for name in constants.ALLOWED_TERRAIN_SHIELD_COLLISIONS_SPRITELISTS]):
        return False
    collision_with_terrain = arcade.check_for_collision_with_lists(shield, terrain)
    for rect in collision_with_terrain:
        rect: arcade.SpriteSolidColor
        check_for_shield_collision_with_rectangle_sprite(shield=shield, rect=rect)

    return bool(collision_with_terrain)


def check_for_shield_collision_with_rectangle_sprite(shield: Shield, rect: arcade.SpriteSolidColor):
    # 5 possibilities.  Bounce off left side, left corner, top side, right corner or right side.
    # Left or right side
    sprite_collided = False
    if (shield.center_y <= rect.top and
            ((shield.left < rect.left <= shield.right) or (shield.left <= rect.right < shield.right))):
        shield.owner.change_x *= -1
        sprite_collided = True
    # Top side
    elif (rect.left <= shield.center_x <= rect.right) and shield.bottom <= rect.top:
        shield.owner.change_y *= -1
        sprite_collided = True
    # Left and right corners
    elif (((shield.left < rect.left <= shield.right) or (shield.left <= rect.right < shield.right))
          and shield.bottom <= rect.top):
        # Want to bounce off the plane that is perpendicular to the vector from the corner to the shield centre
        # (Which is what happens when you bounce off a flat wall, except that the plane is much more obvious then!)
        if shield.left < rect.left <= shield.right:
            corner_x, corner_y = rect.left, rect.top
        else:
            corner_x, corner_y = rect.right, rect.top
        collision_with_fixed_point(point_x=corner_x, point_y=corner_y, obj=shield.owner)
        sprite_collided = True

    if sprite_collided:
        arcade.play_sound(random.choice(BOUNCE_SOUNDS))
    # Check to see if we still have a collision between these two objects.
    # If we do, keep applying the bounce back vector
    if sprite_collided:
        while True:
            change_pos_of_sprite_and_shield_by_vector(obj=shield.owner, x=shield.owner.change_x, y=shield.owner.change_y)
            if not arcade.check_for_collision(shield, rect):
                # If we're no longer colliding, then we can undo the last pos change, as it will get applied later.
                change_pos_of_sprite_and_shield_by_vector(obj=shield.owner, x=-shield.owner.change_x, y=-shield.owner.change_y)
                break


def place_on_world(sprite: Sprite, world: World, scene: Scene):
    # Idea here is that I have a sprite I want to place on the terrain, but want to make sure
    # it doesn't collide with something already there.
    # Note the sprite lists that make up the items on the terrain below.
    # I make a list of all the surfaces of the terrain rectangles, then
    # split up those surfaces that already have an object on them into the free bits,
    # then filter out every bit that's not wide enough for the sprite, then
    # pick one of the remaining surface bits at random and place the sprite
    # somewhere on it at random

    surfaces = [((r.left, r.right), r.top) for r in world.terrain_left_edge.sprite_list + world.terrain_centre.sprite_list]
    for spr in itertools.chain(*[scene[group].sprite_list for group in constants.PLACE_ON_WORLD_SPRITELISTS]):
        spr_width = spr.width if not getattr(spr, 'shield', None) else spr.shield.width

        # Find the surface the sprite is on, then split that surface into the two remaining segments
        for s in surfaces[:]:
            (x_left, x_right), y = s
            if x_left <= spr.center_x - spr_width / 2 and x_right >= spr.center_x + spr_width / 2:
                surfaces.remove(s)
                surfaces.extend([((x_left, spr.center_x - spr_width / 2), y), ((spr.center_x + spr_width / 2, x_right), y)])

    # Surfaces is now a list of the free spaces on top of the terrain.
    # Any of these that's wide enough will work for whatever we're placing on the world

    # Bit confusing, but want to consider potential sprite shield when thinking of the sprite width
    # But since the object hasn't been placed yet, can't use shield.left, shield.right - have to consider the width
    sprite_width = sprite.width if not getattr(sprite, 'shield', None) else sprite.shield.width
    surfaces = [s for s in surfaces if s[0][1] - s[0][0] > sprite_width]
    if not surfaces:
        # There are no free spaces on the terrain for the sprite
        return False
    # Pick one of the surfaces for the sprite
    random.shuffle(surfaces)
    ((x_left, x_right), y) = surfaces[0]
    # Now we have chosen the surface, we can choose exactly where on the surface.
    sprite.center_x = random.randint(int(x_left + sprite_width / 2), int(x_right - sprite_width / 2))
    sprite.bottom = y
    return True
