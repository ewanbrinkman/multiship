import pygame as pg
import pytmx
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

    def apply_rect(self, rect):
        return rect.move(self.rect.topleft)

    def update(self, target, screen_width, screen_height):
        # make the target on the center of the screen
        self.x = -target.rect.centerx + int(screen_width / 2)
        self.y = -target.rect.centery + int(screen_height / 2)

        # limit scrolling to map size
        self.x = min(0, self.x)  # left
        self.y = min(0, self.y)  # top
        self.x = max(-(self.width - screen_width), self.x)  # right
        self.y = max(-(self.height - screen_height), self.y)  # left
        self.rect = pg.Rect(self.x, self.y, self.width, self.height)


class TiledMap:
    def __init__(self, filename):
        tilemap = pytmx.load_pygame(filename, pixelalpha=True)
        self.ratio = TILESIZE / tilemap.tilewidth
        self.width = tilemap.width * tilemap.tilewidth * self.ratio
        self.height = tilemap.height * tilemap.tileheight * self.ratio
        self.tilemap_data = tilemap

    def render(self, surface):
        tile_image = self.tilemap_data.get_tile_image_by_gid
        for layer in self.tilemap_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid in layer:
                    tile = tile_image(gid)
                    if tile:
                        surface.blit(tile, (x * self.tilemap_data.tilewidth,
                                            y * self.tilemap_data.tileheight))

    def make_map(self):
        map_surface = pg.Surface((self.width / self.ratio, self.height / self.ratio))
        self.render(map_surface)
        map_surface = pg.transform.scale(map_surface, (int(map_surface.get_width() * self.ratio),
                                                       int(map_surface.get_height() * self.ratio)))
        return map_surface
