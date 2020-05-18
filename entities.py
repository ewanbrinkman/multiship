import pygame as pg
from pygame.locals import *
from pygame.math import Vector2 as Vec
from settings import *


def update_player(old_player, new_player):
    # change all of the old player's attributes to match the corresponding attribute in the new player
    for attr in new_player.__dict__:
        if hasattr(old_player, attr):
            setattr(old_player, attr, getattr(new_player, attr))


def collide_hit_rect_both(one, two):
    return one.hit_rect.colliderect(two.hit_rect)


def collide_group(sprite, group, direction):
    if direction == 'x':
        hits = pg.sprite.spritecollide(sprite, group, False, collide_hit_rect_both)
        if hits:
            if hits[0].hit_rect.centerx > sprite.hit_rect.centerx:
                sprite.pos.x = hits[0].hit_rect.left - sprite.hit_rect.width / 2
            if hits[0].hit_rect.centerx < sprite.hit_rect.centerx:
                sprite.pos.x = hits[0].hit_rect.right + sprite.hit_rect.width / 2
            sprite.vel.x = 0
            sprite.hit_rect.centerx = sprite.pos.x
    if direction == 'y':
        hits = pg.sprite.spritecollide(sprite, group, False, collide_hit_rect_both)
        if hits:
            if hits[0].hit_rect.centery > sprite.hit_rect.centery:
                sprite.pos.y = hits[0].hit_rect.top - sprite.hit_rect.height / 2
            if hits[0].hit_rect.centery < sprite.hit_rect.centery:
                sprite.pos.y = hits[0].hit_rect.bottom + sprite.hit_rect.height / 2
            sprite.vel.y = 0
            sprite.hit_rect.centery = sprite.pos.y


class NetPlayer:
    def __init__(self, player_id, x, y):
        # basic data
        self.player_id = player_id  # only data part of the player that is unchangeable
        self.username = None
        # position
        self.pos = Vec(x, y)
        self.rot = 0
        self.frozen = False
        # player image
        self.image_color = None
        self.image_string = None
        self.fillcolor = TEXT_COLOR


class SpritePlayer(pg.sprite.Sprite):
    def __init__(self, client, net_player):
        # pygame sprite creation with groups
        self.groups = client.all_sprites, client.players
        pg.sprite.Sprite.__init__(self, self.groups)
        # basic data
        self.player_id = net_player.player_id
        self.username = net_player.username
        # position
        self.pos = Vec(net_player.pos.x, net_player.pos.y)
        self.vel = Vec(0, 0)
        self.acc = Vec(0, 0)
        self.rot = net_player.rot
        self.rot_vel = 0
        self.rot_acc = 0
        self.frozen = net_player.frozen
        # save the client, to access data such as the game sent over the network
        self.client = client
        # sprite image
        self.image_color = net_player.image_color
        self.image_string = net_player.image_string
        self.image = client.player_imgs[net_player.image_string]
        self.image = pg.transform.rotate(self.image, self.rot)
        self.rect = self.image.get_rect()
        self.rect.center = (net_player.pos.x, net_player.pos.y)
        self.hit_rect = pg.Rect(self.rect.x, self.rect.x, PLAYER_HIT_RECT_WIDTH, PLAYER_HIT_RECT_HEIGHT)
        self.hit_rect.center = self.rect.center
        self.fillcolor = net_player.fillcolor

    def update_image(self):
        self.image = self.client.player_imgs[self.image_string].copy()  # use .copy() to not modify the stored image
        self.image = pg.transform.rotate(self.image, self.rot)
        self.rect = self.image.get_rect()
        self.rect.center = (self.pos.x, self.pos.y)
        self.hit_rect = pg.Rect(self.rect.x, self.rect.y, PLAYER_HIT_RECT_WIDTH, PLAYER_HIT_RECT_HEIGHT)
        self.hit_rect.center = self.rect.center
        self.fillcolor = self.fillcolor

    def match_net_player(self):
        # get the correct player to overwrite data
        net_player = self.client.game['players'][self.player_id]
        # overwrite attributes
        update_player(self, net_player)
        # change the image to match the new data
        self.update_image()
        # change client username to match received username from net player
        self.client.username = self.username

    def update(self):
        # remove the player if they have disconnected from the server
        if self.player_id not in self.client.game['players']:
            self.kill()
        # if they are still connected, update
        else:
            # update the sprite with the latest data
            self.match_net_player()

    def apply_keys(self):
        # get key presses
        keys = pg.key.get_pressed()

        # reset acceleration
        self.acc = Vec(0, 0)
        self.rot_acc = 0

        # apply key presses
        if keys[K_a] or keys[K_LEFT]:
            self.rot_acc = PLAYER_ROT_ACC
        if keys[K_d] or keys[K_RIGHT]:
            self.rot_acc = -PLAYER_ROT_ACC
        if keys[K_w] or keys[K_UP]:
            self.acc = Vec(PLAYER_ACC, 0).rotate(-self.rot)
        if keys[K_s] or keys[K_DOWN]:
            self.acc = Vec(-PLAYER_ACC / 3, 0).rotate(-self.rot)

    def basic_collisions(self, group):
        # test collision
        hits = pg.sprite.spritecollide(self, group, False, collide_hit_rect_both)
        for hit in hits:
            if hit != self:
                # update this sprite if it collided
                self.image_string = PLAYER_IMGS['broken' + self.image_color]

    def apply_friction(self, movement_type):
        # north, south, east, and west movement
        if movement_type == 'nsew':
            hits = pg.sprite.spritecollide(self, self.client.shallows, False, collide_hit_rect_both)
            if hits:
                return PLAYER_SHALLOW_FRICTION
            else:
                return PLAYER_WATER_FRICTION
        # rotation movement
        elif movement_type == 'rot':
            hits = pg.sprite.spritecollide(self, self.client.shallows, False, collide_hit_rect_both)
            if hits:
                return PLAYER_SHALLOW_ROT_FRICTION
            else:
                return PLAYER_WATER_ROT_FRICTION

    def move(self):
        # update the players velocity with key presses
        # this is only done to the sprite player that represents the client
        self.apply_keys()
        # move the sprite player, if there are no restrictions in place (such as being frozen)
        if not self.frozen:
            # change position
            # apply friction
            self.acc += self.vel * self.apply_friction('nsew')
            # equations of motion
            self.vel += self.acc
            self.pos += (self.vel + 0.5 * self.acc) * self.client.dt
            # add wind
            self.pos += Vec(WINDX, WINDY)

            # change image
            # apply friction
            self.rot_acc += self.rot_vel * self.apply_friction('rot')
            # equations of motion
            self.rot_vel += self.rot_acc
            self.rot += ((self.rot_vel + 0.5 * self.rot_acc) * self.client.dt) % 360

        # collision detection
        self.hit_rect.centerx = self.pos.x
        collide_group(self, self.client.walls, 'x')
        self.hit_rect.centery = self.pos.y
        collide_group(self, self.client.walls, 'y')

        # basic collision updates
        self.basic_collisions(self.client.players)

        # match the sprite's rect with where it should be based on the hit rect
        self.rect.center = self.hit_rect.center
        # update the image with the correct positioning
        self.update_image()


class Obstacle(pg.sprite.Sprite):
    def __init__(self, client, x, y, width, height, type):
        if type == 'wall':
            self.groups = client.all_sprites, client.obstacles, client.walls
        elif type == 'shallow':
            self.groups = client.all_sprites, client.obstacles, client.shallows
        pg.sprite.Sprite.__init__(self, self.groups)
        self.rect = pg.Rect(x, y, width, height)
        self.hit_rect = self.rect
        self.type = type
