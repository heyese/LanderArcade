from __future__ import annotations
import arcade
import itertools
from classes.game_object import GameObject


shield_disabled_when_collisions_exist_with = [
    "Terrain Left Edge",
    "Terrain Centre",
    "Terrain Right Edge",
    "Missiles",
    "Shields",  # only activated shields
    "Ground Enemies",
    "Air Enemies",
    "Explosions"]


class Shield(arcade.SpriteCircle):
    """The shield - a sprite that stays centred on the owner and can be activated / deactivated"""
    def __init__(self, scene: arcade.Scene, owner: arcade.Sprite, radius: int = None, charge: int = 100):
        if radius is None:
            radius = int(max(owner.height, owner.width) * 1.5)
        super().__init__(radius=radius,
                         # Transparent arcade.color.AQUA
                         color=(0, 255, 255, 50))
        self.owner: GameObject = owner
        self.visible = False
        self.initial_charge = charge
        self.charge = charge
        self.activated = False
        self.scene = scene
        self.scene.add_sprite('Shields', self)
        self.disabled = False
        self.disabled_timer = None

    def recharge(self):
        self.charge = self.initial_charge

    def on_update(self, delta_time: float = 1 / 60):
        # Stay centred on the lander
        self.center_x = self.owner.center_x
        self.center_y = self.owner.center_y
        # If activated, use up some power
        if self.activated:
            self.charge = max(self.charge - delta_time, 0)
            if self.charge == 0:
                self.deactivate()
        # If disabled (ie. someone tried to activate it whilst an object was within its perimeter), count down to being un-disabled
        if self.disabled:
            if self.disabled_timer is None:
                self.disabled_timer = 0.5  # seconds
            else:
                self.disabled_timer -= delta_time
                if self.disabled_timer <= 0:
                    self.disabled_timer = None
                    self.disabled = False
                    # If the shield owner happens to be the Lander itself, and the user is still trying to operate
                    # the shield (ie. mouse button / key still pressed), we auto try to re-enable it here
                    if self.owner in self.scene["Lander"].sprite_list and self.owner.trying_to_activate_shield:
                        self.activate()

    def activate(self):
        if self.disabled is False:
            if not self.charge:
                self.disabled = True
                return
            # Except for the Landing Pad, Cannot enable shield when an object is already within the perimeter
            # If you try to, it is disabled for a small period
            if self.owner not in itertools.chain(self.scene["Landing Pad"], self.scene["Hostages"]):
                collisions = arcade.check_for_collision_with_lists(self, [self.scene[i] for i in shield_disabled_when_collisions_exist_with])
                for obj in collisions:
                    if obj in self.scene["Shields"] and not obj.activated:
                        # Collisions with de-activated shields don't count
                        continue
                    self.disabled = True
                    return
            self.visible = True
            self.activated = True

    def deactivate(self):
        self.visible = False
        self.activated = False

    def disable(self):
        self.deactivate()
        self.disabled = True


class DisabledShield(arcade.SpriteCircle):
    """If someone tries to activate the actual shield with an object within it's perimeter, the shield
    is disabled for a period of time, during which this "disabled shield" is displayed"""
    def __init__(self, scene: arcade.Scene, owner: arcade.Sprite):
        super().__init__(radius=int(max(owner.height, owner.width) * 1.5),
                         # Transparent arcade.color.AQUA
                         color=(255, 0, 0, 50))
        self.owner: GameObject = owner
        self.visible = False
        self.scene = scene
        self.scene.add_sprite('Disabled Shields', self)

    def on_update(self, delta_time: float = 1 / 60):
        # Stay centred on the lander
        self.center_x = self.owner.center_x
        self.center_y = self.owner.center_y
        # This "shield" only becomes visible when the main shield is disabled
        self.visible = True if self.owner.shield.disabled else False
