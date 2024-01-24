import arcade

class Shield(arcade.SpriteCircle):
    """The lander shield - a sprite that stays centred on the lander and can be activated / deactivated"""
    def __init__(self, owner: arcade.Sprite):
        super().__init__(radius=int(owner.height * 2),
                         # Transparent arcade.color.AQUA
                         color=(0, 255, 255, 50))
        self.owner = owner
        self.visible = False
        self.power: int = 100
        self.activated = False

    def on_update(self, delta_time: float = 1 / 60):
        # Stay centred on the lander
        self.center_x = self.owner.center_x
        self.center_y = self.owner.center_y
        # If activated, use up some power
        if self.activated:
            self.power = max(self.power - delta_time, 0)
            if self.power == 0:
                self.deactivate()

    def activate(self):
        if self.power:
            self.visible = True
            self.activated = True

    def deactivate(self):
        self.visible = False
        self.activated = False