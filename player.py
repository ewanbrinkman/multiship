import pygame as pg
from pygame.locals import *
from pygame.math import Vector2 as Vec
from random import randint
from settings import *


class NetPlayer:
    def __init__(self, player_id, x, y):
        # basic data
        self.player_id = player_id  # only data part of the player that is unchangeable
        self.username = None
        # position
        self.pos = Vec(x, y)
        self.vel = Vec(0, 0)
        self.acc = Vec(0, 0)
        self.rot = 0
        self.frozen = False
        # player image
        self.image_string = "shipblue.png"
        self.fillcolor = (randint(0, 255), randint(0, 255), randint(0, 255))

    def update(self, sprite_player):
        # change all of the net player's attributes to match the corresponding attribute in the sprite player
        for attr in sprite_player.__dict__:
            if hasattr(self, attr):
                setattr(self, attr, getattr(sprite_player, attr))


class SpritePlayer(pg.sprite.Sprite):
    def __init__(self, client, net_player):
        # pygame sprite creation with groups
        self.groups = client.sprite_players
        pg.sprite.Sprite.__init__(self, self.groups)
        # basic data
        self.player_id = net_player.player_id
        self.username = net_player.username
        # position
        self.pos = Vec(net_player.pos.x, net_player.pos.y)
        self.vel = Vec(net_player.vel.x, net_player.vel.y)
        self.acc = Vec(net_player.acc.x, net_player.acc.y)
        self.rot = net_player.rot
        self.rot_vel = 0
        self.rot_acc = 0
        self.frozen = net_player.frozen
        # save the client, to access data such as the game sent over the network
        self.client = client
        # sprite image
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
        # update the sprite to match the player received over the network
        net_player = self.client.game['players'][self.player_id]

        # change all of the net player's attributes to match the corresponding attribute in the sprite player
        for attr in net_player.__dict__:
            if hasattr(self, attr):
                setattr(self, attr, getattr(net_player, attr))

        # update rect position
        self.rect.center = (net_player.pos.x, net_player.pos.y)

        self.update_image()

    def update(self):
        # remove the player if they have disconnected from the server
        if self.player_id not in self.client.game['players']:
            self.kill()
        # if they are still connected, update
        else:
            # update the sprite with the latest data
            self.match_net_player()
            # basic collision updates
            self.collisions(self.client.sprite_players)

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
            self.acc = Vec(-PLAYER_ACC, 0).rotate(-self.rot)

    def collide_hit_rect_both(self, one, two):
        return one.hit_rect.colliderect(two.hit_rect)

    def collisions(self, group):
        # test collision
        hits = pg.sprite.spritecollide(self, group, False, self.collide_hit_rect_both)
        for hit in hits:
            if hit != self:
                # update this sprite if it collided
                self.image_string = "shipyellow.png"
                self.update_image()

    def collide_group(self, group, direction):
        pass

    def move(self):
        # update the players velocity with key presses
        # this is only done to the sprite player that represents the client
        self.apply_keys()
        # move the sprite player, if there are no restrictions in place (such as being frozen)
        if not self.frozen:
            # change position
            # apply friction
            self.acc += self.vel * PLAYER_FRICTION
            # equations of motion
            self.vel += self.acc
            self.pos += (self.vel + 0.5 * self.acc) * self.client.dt

            # change image
            # apply friction
            self.rot_acc += self.rot_vel * PLAYER_ROT_FRICTION
            # equations of motion
            self.rot_vel += self.rot_acc
            self.rot += ((self.rot_vel + 0.5 * self.rot_acc) * self.client.dt) % 360

            self.update_image()

        # collision detection
        self.hit_rect.centerx = self.pos.x
        self.collide_group(self.client.sprite_players, 'x')
        self.hit_rect.centery = self.pos.y
        self.collide_group(self.client.sprite_players, 'y')

        # basic collision updates
        self.collisions(self.client.sprite_players)

        # match the sprite's rect with where it should be based on the hit rect
        self.rect.center = self.hit_rect.center
