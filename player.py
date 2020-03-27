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
        self.frozen = False
        # player image
        self.image_string = "player_fwd.png"
        self.fillcolor = (randint(0, 255), randint(0, 255), randint(0, 255))

    def update(self, sprite_player):
        # make the client's net player match the client's sprite player
        # basic data
        self.username = sprite_player.username
        # position
        self.pos = sprite_player.pos
        self.vel = sprite_player.vel
        self.rect = sprite_player.rect
        self.frozen = sprite_player.frozen
        # player image
        self.image_string = sprite_player.image_string
        self.fillcolor = sprite_player.fillcolor


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
        self.frozen = net_player.frozen
        # save the client, to access data such as the game sent over the network
        self.client = client
        # sprite image
        self.image_string = net_player.image_string
        self.image = client.player_imgs[net_player.image_string]
        self.rect = self.image.get_rect()
        self.rect.center = (net_player.pos.x, net_player.pos.y)
        self.fillcolor = net_player.fillcolor

    def update_image(self):
        self.image = self.client.player_imgs[self.image_string].copy()
        self.image = pg.transform.scale(self.image, (self.image.get_rect().width * self.client.map.ratio,
                                                     self.image.get_rect().height * self.client.map.ratio))
        self.rect = self.image.get_rect()
        self.rect.center = (self.pos.x, self.pos.y)
        self.fillcolor = self.fillcolor

    def match_net_player(self):
        # update the sprite to match the player received over the network
        net_player = self.client.game['players'][self.player_id]
        # basic data
        self.username = net_player.username
        self.player_id = net_player.player_id
        # position
        self.pos = net_player.pos
        self.vel = net_player.vel
        self.frozen = net_player.frozen
        # update rect position
        self.rect.center = (net_player.pos.x, net_player.pos.y)
        # sprite image
        # update the base image to use if it does not match the data received by the server
        if self.image_string != net_player.image_string:
            self.image_string = net_player.image_string
        # constantly refresh sprite image with a copy of the stored image
        # if .copy() is not used, it will modify the image stored in player images
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

        # update velocity
        self.vel = Vec(0, 0)
        if keys[K_a] or keys[K_LEFT]:
            self.vel.x -= PLAYER_SPEED
        if keys[K_d] or keys[K_RIGHT]:
            self.vel.x += PLAYER_SPEED
        if keys[K_w] or keys[K_UP]:
            self.vel.y -= PLAYER_SPEED
        if keys[K_s] or keys[K_DOWN]:
            self.vel.y += PLAYER_SPEED
        if self.vel.x != 0 and self.vel.y != 0:
            self.vel *= 1 / 1.41421356237  # 1 over root 2

    def collisions(self, group):
        # test collision
        hits = pg.sprite.spritecollide(self, group, False)
        for hit in hits:
            if hit != self:
                # update this sprite if it collided
                self.image_string = "player_bwd.png"
                self.update_image()

    def collide_group(self, group, direction):
        pass

    def move(self):
        # update the players velocity with key presses
        # this is only done to the sprite player that represents the client
        self.apply_keys()
        # move the sprite player, if there are no restrictions in place (such as being frozen)
        if not self.frozen:
            self.pos += self.vel * self.client.dt

        # collision detection
        self.rect.centerx = self.pos.x
        self.collide_group(self.client.sprite_players, 'x')
        self.rect.centery = self.pos.y
        self.collide_group(self.client.sprite_players, 'y')

        # basic collision updates
        self.collisions(self.client.sprite_players)
