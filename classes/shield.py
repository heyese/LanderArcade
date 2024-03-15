from __future__ import annotations
import arcade
from classes.game_object import GameObject
from pathlib import Path
import constants


shield_disabled_when_collisions_exist_with = [
    "Lander",
    "Missiles",
    "Shields",  # only activated shields
    "Ground Enemies",
    "Air Enemies",
    "Explosions"]

terrain = [
    "Terrain Left Edge",
    "Terrain Centre",
    "Terrain Right Edge", ]


class Shield(arcade.SpriteCircle):
    """The shield - a sprite that stays centred on the owner and can be activated / deactivated"""
    def __init__(self, scene: arcade.Scene,
                 owner: arcade.Sprite,
                 radius: int = None,
                 charge: int = 100,
                 sound_enabled: bool = False,
                 max_volume: float = 0.3):
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
        self._disabled_timer = 0
        self.disabled_shield = DisabledShield(scene=scene, owner=self.owner)

        self.center_x = self.owner.center_x
        self.center_y = self.owner.center_y
        self.velocity_x = self.owner.velocity_x
        self.velocity_y = self.owner.velocity_y

        # Shield sounds
        self.sound_enabled = sound_enabled
        self.shield_activate_sound = constants.SOUNDS['sounds/shield_activated.mp3']
        self.shield_disabled_sound = constants.SOUNDS['sounds/shield_disabled.mp3']
        # Don't currently use the continuous sound
        #self.shield_continuous = constants.SOUNDS['sounds/shield_continuous.wav']
        self.max_volume = max_volume
        # This keeps track of the "media player" that is playing the current sound
        # Each time I play a sound, I think it returns a different player!
        self.media_player = None

    def recharge(self):
        self.charge = self.initial_charge

    @property
    def disabled(self):
        return self._disabled_timer > 0

    def on_update(self, delta_time: float = 1 / 60):
        # These don't actually make a difference - just so we can reference them in functions
        self.velocity_x = self.owner.velocity_x
        self.velocity_y = self.owner.velocity_y

        # Stay centred on the lander
        self.center_x = self.owner.center_x
        self.center_y = self.owner.center_y
        # If activated, use up some power
        if not self.owner.dead:
            if self.activated:
                self.charge = max(self.charge - delta_time, 0)
                if self.charge == 0:
                    self.deactivate()
            # If disabled (ie. someone tried to activate it whilst an object was within its perimeter),
            # count down to being un-disabled
            if self.disabled:
                self._disabled_timer -= delta_time
                if self._disabled_timer <= 0:
                    self._disabled_timer = 0
                    # If the shield owner happens to be the Lander itself, and the user is still trying to operate
                    # the shield (ie. mouse button / key still pressed), we auto try to re-enable it here
                    if self.owner in self.scene["Lander"].sprite_list and self.owner.trying_to_activate_shield:
                        self.activate()

    def activate(self):
        if self.disabled:
            # If the shield is disabled, sound was played when it was disabled
            return

        if not self.charge and self.owner in self.scene["Lander"].sprite_list:
            # If the user is trying to activate their shield but has no charge, we play the sound every time
            # to help them understand
            self.media_player = self.sound_enabled and arcade.play_sound(self.shield_disabled_sound, volume=self.max_volume)
            return

        if self.attempted_to_activate_shield_with_collision():
            self.disable_for(1)
            return

        # Shield is being activated
        self.visible = True
        self.activated = True
        self.media_player = self.sound_enabled and arcade.play_sound(self.shield_activate_sound, volume=self.max_volume)

    def deactivate(self):
        self.visible = False
        self.activated = False

    def disable_for(self, seconds: float):
        self._disabled_timer = seconds
        self.media_player = self.sound_enabled and arcade.play_sound(self.shield_disabled_sound,
                                                                     volume=self.max_volume)
        self.deactivate()

    def attempted_to_activate_shield_with_collision(self):
        # Cannot enable shield when an object is already within the shield perimeter
        # If you try to, it is disabled for a small period.
        # Except that ground objects are allowed to have their shields collide with the terrain.
        # And except for Hostages who always have an activated shield, regardless.
        if self.owner not in self.scene["Hostages"]:
            collisions = arcade.check_for_collision_with_lists(self, [self.scene[i] for i in shield_disabled_when_collisions_exist_with])
            if self.owner not in self.scene["Ground Enemies"]:
                terrain_collisions = arcade.check_for_collision_with_lists(self, [self.scene[i] for i in terrain])
                collisions += terrain_collisions
            for obj in collisions:
                if obj in self.scene["Shields"] and not obj.activated:
                    # Collisions with de-activated shields don't count
                    continue
                if self.owner == obj or self is obj:
                    # collisions with your own shield are obviously allowed
                    continue
                return True
            return False


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

