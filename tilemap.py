import pygame as pg
from settings import *


class Camera:
    def __init__(self, map_width, map_height):
        self.rect = pg.Rect(0, 0, map_width, map_height)
        self.width = map_width
        self.height = map_height
        self.x = None
        self.y = None

    def apply_sprite(self, sprite):
        return sprite.rect.move(self.rect.topleft)

    def update(self, target):
        # make the target on the center of the screen
        self.x = -target.rect.centerx + int(SCREEN_WIDTH / 2)
        self.y = -target.rect.centery + int(SCREEN_HEIGHT / 2)

        # limit scrolling to map size
        self.x = min(0, self.x)  # left
        self.y = min(0, self.y)  # top
        self.x = max(-(self.width - SCREEN_WIDTH), self.x)  # right
        self.y = max(-(self.height - SCREEN_HEIGHT), self.y)  # left
        self.rect = pg.Rect(self.x, self.y, self.width, self.height)
