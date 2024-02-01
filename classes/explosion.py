
import arcade
from typing import List

# How on earth are explosions going to work ... ?
# Explosions will exert a force on mobile objects they come into contact with,
# but I don't think those objects will exert a force on them ...
# I think this means that their trajectory is completely determined by initial conditions and gravity?
# They can't go through the ground
# On contact, they will cause objects that can explode to explode (unless a force field is activated)
# They won't exert a force on other explosions ... I don't think this really makes sense
# They are always drawn behind anything using a force-field
# Properties would be:
#    initial size
#    final size
#    rate of increase of size (or maybe simply to just call this lifetime - measure in seconds)
#    force (that's applied to shielded mobile objects)
#    initial velocity - I *think* I want explosions to move

# Not sure what happens to a shielded object that is initially hit - technically this
# is before the existence of an explosion, but should be considered.  If a missile
# hits a shielded craft at speed and the explosion flies on, it might even push the ship
# backwards.  There should be a significant transfer of energy on impact
# But then might the object fly away faster than the explosion increases in size?  Does this matter?


class Explosion(arcade.Sprite):
    def __init__(self,
                 initial_radius: int,
                 final_radius: int,
                 lifetime: float,  # seconds
                 force: float,   # exerted on mobile objects in contact
                 velocity: List[float, float]):
        super().__init__(filename=filename, scale=scale * SCALING)
        self.scen
        self.shield: Shield = Shield(self)
        self.engine: Engine = Engine(self)
        self.world: World = world
        self.mass = mass
        # Don't like the Sprite.velocity attribute, since it's obvious delta_time can vary,
        # so it's not really a velocity - it's a change in position
        self.velocity_x: float = 0
        self.velocity_y: float = 0
        # Gravity only applies when we're not "in space"!
        self.in_space: bool | None = None
        # Gravity applies pretty heavily if someone tries to fly off into space
        self.above_space: bool | None = None

    def on_update(self, delta_time: float = 1 / 60):
        # Are we in space or not?
        self.in_space = True if self.center_y >= SPACE_START else False
        self.above_space = True if self.center_y >= SPACE_END else False
        # Calculate current velocity from auto-maintained self.change_XXX variables and delta time
        self.velocity_x = self.change_x / delta_time  # pixels per second!
        self.velocity_y = self.change_y / delta_time
        # Calculate the force being applied to the aircraft
        force_y = self.determine_force_y(0)
        force_x = self.determine_force_x(0)

        # s = ut + (0.5)at^2
        self.change_x = self.velocity_x * delta_time + 0.5 * (force_x / self.mass) * (delta_time ** 2)
        self.change_y = self.velocity_y * delta_time + 0.5 * (force_y / self.mass) * (delta_time ** 2)

        self.center_x += self.change_x
        self.center_y += self.change_y

        # Check for collisions
        self.check_for_collision()