from random import choice
from itertools import chain
from pytweening import easeInOutSine
import pygame as pg
from pygame.locals import *
from pygame.math import Vector2 as Vec
from settings import *


def update_net_object(old_player, new_player):
    # change all of the old player's attributes to match the corresponding attribute in the new player
    for attr in new_player.__dict__:
        if hasattr(old_player, attr):
            setattr(old_player, attr, getattr(new_player, attr))


def collide_hit_rect_both(one, two):
    return one.hit_rect.colliderect(two.hit_rect)


def collide_group(sprite, group, direction):
    if direction == "x":
        hits = pg.sprite.spritecollide(sprite, group, False, collide_hit_rect_both)
        if hits:
            if hits[0].hit_rect.centerx > sprite.hit_rect.centerx:
                sprite.pos.x = hits[0].hit_rect.left - sprite.hit_rect.width / 2
            if hits[0].hit_rect.centerx < sprite.hit_rect.centerx:
                sprite.pos.x = hits[0].hit_rect.right + sprite.hit_rect.width / 2
            sprite.vel.x = 0
            sprite.hit_rect.centerx = sprite.pos.x
    if direction == "y":
        hits = pg.sprite.spritecollide(sprite, group, False, collide_hit_rect_both)
        if hits:
            if hits[0].hit_rect.centery > sprite.hit_rect.centery:
                sprite.pos.y = hits[0].hit_rect.top - sprite.hit_rect.height / 2
            if hits[0].hit_rect.centery < sprite.hit_rect.centery:
                sprite.pos.y = hits[0].hit_rect.bottom + sprite.hit_rect.height / 2
            sprite.vel.y = 0
            sprite.hit_rect.centery = sprite.pos.y


def alpha(sprite, r, g, b):
    alpha_chain = sprite.respawn_alpha
    blend_type = pg.BLEND_RGBA_MULT
    try:
        sprite.image.fill((r, g, b, next(alpha_chain)), special_flags=blend_type)
    except StopIteration:
        sprite.respawn_alpha = chain(RESPAWN_ALPHA)
        alpha_chain = sprite.respawn_alpha
        blend_type = pg.BLEND_RGBA_MULT
        sprite.image.fill((r, g, b, next(alpha_chain)), special_flags=blend_type)

class NetPlayer:
    def __init__(self, player_id):
        # basic data
        self.player_id = player_id  # only data part of the player that is unchangeable
        self.username = None
        self.ammo = 999
        # position
        self.pos = Vec(0, 0)
        self.rot = 0
        # effects
        self.frozen = False
        self.respawn = False
        self.destroy = False
        self.current_crash_time = False
        self.current_respawn_time = False
        self.power_invincible = False
        # data for server to process
        self.overwrites = {"collisions": [],
                           "items": [],
                           "new bullets": [],
                           "kill bullets": [],
                           }
        # player image
        self.image_color = None
        self.image_string = None
        self.fillcolor = TEXT_COLOR


class SpritePlayer(pg.sprite.Sprite):
    def __init__(self, client, net_player):
        self._layer = PLAYER_LAYER
        # pygame sprite creation with groups
        self.groups = client.all_sprites, client.players, client.colliders
        pg.sprite.Sprite.__init__(self, self.groups)
        # basic data
        self.player_id = net_player.player_id
        self.username = net_player.username
        self.ammo = net_player.ammo
        self.last_shoot = 0
        # position
        self.pos = Vec(net_player.pos.x, net_player.pos.y)
        self.vel = Vec(0, 0)
        self.acc = Vec(0, 0)
        self.rot = net_player.rot
        self.rot_vel = 0
        self.rot_acc = 0
        # effects
        self.frozen = net_player.frozen
        self.respawn = net_player.respawn
        self.destroy = net_player.destroy
        self.respawn_alpha = chain(RESPAWN_ALPHA)
        self.respawn_time = False
        self.current_respawn_time = net_player.current_respawn_time
        self.crash_time = False
        self.current_crash_time = net_player.current_crash_time
        self.power_invincible = False
        self.power_time = False
        # data for the server to process
        self.overwrites = net_player.overwrites
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
        # store the original size of the image, to resize the image smaller when crashed
        self.image_width = self.rect.width
        self.image_height = self.rect.height
        # debug
        self.color = PLAYER_SPAWN_COLOR

    def update_image(self):
        self.image = self.client.player_imgs[self.image_string].copy()  # use .copy() to not modify the stored image
        self.rect = self.image.get_rect()
        # store the original size of the image, to resize the image smaller when crashed
        self.image_width = self.rect.width
        self.image_height = self.rect.height

        # if the player is current doing the crashing animation
        if self.current_crash_time:
            # make the image smaller based on how long the player has been crashed
            crash_size_decimal = abs(1 - self.current_crash_time / PLAYER_CRASH_DURATION)
            if crash_size_decimal <= 0.02:
                crash_size_decimal = 0.02
            self.image = pg.transform.scale(self.image, (int(self.image_width * crash_size_decimal),
                                                         int(self.image_height * crash_size_decimal)))
            # make hit rect smaller as well using the crash size decimal
            self.hit_rect = pg.Rect(self.rect.x, self.rect.y,
                                    int(PLAYER_HIT_RECT_WIDTH * crash_size_decimal),
                                    int(PLAYER_HIT_RECT_HEIGHT * crash_size_decimal))

        # image details
        self.image = pg.transform.rotate(self.image, self.rot)
        self.rect = self.image.get_rect()
        self.rect.center = (self.pos.x, self.pos.y)
        if not self.current_crash_time:
            self.hit_rect = pg.Rect(self.rect.x, self.rect.y, PLAYER_HIT_RECT_WIDTH, PLAYER_HIT_RECT_HEIGHT)
        self.hit_rect.center = self.rect.center
        self.fillcolor = self.fillcolor

        # flashing respawn invincibility effect
        if self.current_respawn_time:
            alpha(self, 255, 255, 255)
        # yellow power invincibility effect
        if self.power_invincible:
            self.image.fill((255, 255, 51, 255), special_flags=pg.BLEND_RGBA_MULT)
        # blue frozen effect
        if self.frozen:
            self.image.fill((200, 200, 250, 255), special_flags=pg.BLEND_RGBA_MULT)

    def match_net_player(self):
        # get the correct player to overwrite data
        net_player = self.client.game['players'][self.player_id]
        # overwrite attributes
        update_net_object(self, net_player)
        # change the image to match the new data
        self.update_image()
        # change client username to match received username from net player
        if self.player_id == self.client.player.player_id:
            self.client.username = self.username

    def update(self):
        # remove the player if they have disconnected from the server
        if self.player_id not in self.client.game['players']:
            self.kill()
        # if they are still connected, update
        else:
            # update the sprite with the latest data
            self.match_net_player()

    def shoot(self):
        # only shoot a bullet if enough time has passed since the last shot and the player has ammo
        if pg.time.get_ticks() - self.last_shoot > SHOOT_RATE and self.ammo:
            self.ammo -= 1
            self.last_shoot = pg.time.get_ticks()
            # create a new vector for the bullet so the bullet does not use the player's vector
            bullet_data = [Vec(self.pos.x, self.pos.y), self.rot]
            self.overwrites['new bullets'].append(bullet_data)

    def apply_keys(self):
        # get key presses
        keys = pg.key.get_pressed()

        # apply key presses
        if keys[K_a] or keys[K_LEFT]:
            self.rot_acc = PLAYER_ROT_ACC
        if keys[K_d] or keys[K_RIGHT]:
            self.rot_acc = -PLAYER_ROT_ACC
        if keys[K_w] or keys[K_UP]:
            self.acc = Vec(PLAYER_ACC, 0).rotate(-self.rot)
        if keys[K_s] or keys[K_DOWN]:
            self.acc = Vec(-PLAYER_ACC / 3, 0).rotate(-self.rot)
        if keys[K_SPACE]:
            self.shoot()

    def apply_friction(self, movement_type):
        # north, south, east, and west movement
        if movement_type == "nsew":
            hits = pg.sprite.spritecollide(self, self.client.shallows, False, collide_hit_rect_both)
            if hits:
                return PLAYER_SHALLOW_FRICTION
            else:
                return PLAYER_WATER_FRICTION
        # rotation movement
        elif movement_type == "rot":
            hits = pg.sprite.spritecollide(self, self.client.shallows, False, collide_hit_rect_both)
            if hits:
                return PLAYER_SHALLOW_ROT_FRICTION
            else:
                return PLAYER_WATER_ROT_FRICTION

    def respawn_player(self):
        # reset effects
        self.power_invincible = False
        self.power_time = False
        # reset image
        self.image_string = PLAYER_IMGS[self.image_color]
        self.update_image()
        # reset movement and rotation
        self.acc = Vec(0, 0)
        self.vel = Vec(0, 0)
        self.rot_acc = 0
        self.rot_vel = 0
        self.rot = 0
        # go to a random spawn point, if it is a new game, the spawn point has already been chosen
        if self.client.new_game is False:
            self.pos = choice(self.client.spawn_points)
        # set respawn attributes
        self.respawn = False
        self.crash_time = False
        self.current_crash_time = False
        self.respawn_time = pg.time.get_ticks()
        self.current_respawn_time = pg.time.get_ticks() - self.respawn_time
        # make sure a new game respawn isn't done again
        self.client.new_game = False

    def player_hit(self, direction):
        if direction == "x":
            hits = pg.sprite.spritecollide(self, self.client.players, False, collide_hit_rect_both)
            if hits:
                for hit in hits:
                    if hit != self:
                        if hit.hit_rect.centerx > self.hit_rect.centerx:
                            self.vel.x = -PLAYER_BOUNCE_VEL
                        if hit.hit_rect.centerx < self.hit_rect.centerx:
                            self.vel.x = PLAYER_BOUNCE_VEL
        if direction == "y":
            hits = pg.sprite.spritecollide(self, self.client.players, False, collide_hit_rect_both)
            if hits:
                for hit in hits:
                    if hit != self:
                        if hit.hit_rect.centery > self.hit_rect.centery:
                            self.vel.y = -PLAYER_BOUNCE_VEL
                        if hit.hit_rect.centery < self.hit_rect.centery:
                            self.vel.y = PLAYER_BOUNCE_VEL

    def player_collisions(self):
        # test for collision
        hits = pg.sprite.spritecollide(self, self.client.players, False, collide_hit_rect_both)
        for hit in hits:
            if hit != self and hit.power_invincible and not self.power_invincible and self.current_respawn_time is False and self.current_crash_time is False:
                # update this sprite if it collided
                self.destroy_player()
            # let the server know someone should be destroyed
            if hit != self and self.power_invincible and not hit.power_invincible and hit.current_respawn_time is False and hit.current_crash_time is False:
                self.overwrites['collisions'].append(hit.player_id)

    def item_collisions(self):
        # test for collision
        hits = pg.sprite.spritecollide(self, self.client.items, False, collide_hit_rect_both)
        for hit in hits:
            # power items give the power invincibility effect
            if hit.name == "power":
                self.power_invincible = True
                self.power_time = pg.time.get_ticks()
            # make sure the item is set to inactive on the client side
            self.client.item_spawns[hit.item_id][0] = False
            # tell the server the item should be inactive
            self.overwrites['items'].append(hit.item_id)
            # destroy the item
            hit.kill()

    def destroy_player(self):
        self.destroy = False
        self.image_string = PLAYER_IMGS["broken" + self.image_color]
        self.crash_time = pg.time.get_ticks()
        self.current_crash_time = pg.time.get_ticks() - self.crash_time

    def update_client(self):
        # new game respawn
        if self.client.new_game:
            self.respawn_player()

        # destroy the player if told to by the server
        if self.destroy:
            self.destroy_player()

        # respawn the player if told to by the server
        if self.respawn:
            self.respawn_player()

        # reset acceleration
        self.acc = Vec(0, 0)
        self.rot_acc = 0

        # if the player isn't crashed, they can move
        if self.crash_time is False:
            # update the players velocity with key presses
            self.apply_keys()
        # if they are crashed, respawn after they have stayed crashed long enough
        else:
            self.current_crash_time = pg.time.get_ticks() - self.crash_time
            if self.current_crash_time >= PLAYER_CRASH_DURATION:
                self.respawn_player()
        # remove the respawn invincibility effect after enough time has passed
        if self.respawn_time is not False:
            self.current_respawn_time = pg.time.get_ticks() - self.respawn_time
            if self.current_respawn_time >= RESPAWN_INVINCIBLE_DURATION:
                self.respawn_time = False
                self.current_respawn_time = False
        # remove the power invincibility effect after enough time has passed
        if self.power_time is not False:
            current_power_time = pg.time.get_ticks() - self.power_time
            if current_power_time >= POWER_INVINCIBLE_DURATION:
                self.power_invincible = False
                self.power_time = False

        # move the sprite player, if there are no restrictions in place (such as being frozen)
        if not self.frozen:
            # change position

            # apply friction
            self.acc += self.vel * self.apply_friction("nsew")

            # new velocity after
            self.vel = self.vel + self.acc * self.client.dt

            # displacement
            displacement = self.vel * self.client.dt + 0.5 * self.acc * self.client.dt ** 2
            self.pos += displacement

            # change image

            # apply friction
            self.rot_acc += self.rot_vel * self.apply_friction("rot")

            # new velocity after
            self.rot_vel = self.rot_vel + self.rot_acc * self.client.dt

            # displacement
            rot_displacement = self.rot_vel * self.client.dt + 0.5 * self.rot_acc * self.client.dt ** 2
            self.rot += rot_displacement % 360

        # save pos for doing hit rect on players
        old_pos = Vec(self.pos.x, self.pos.y)

        # collision detection
        self.hit_rect.centerx = self.pos.x
        collide_group(self, self.client.walls, "x")
        self.hit_rect.centery = self.pos.y
        collide_group(self, self.client.walls, "y")
        # match the sprite's rect with where it should be based on the hit rect
        self.rect.center = self.hit_rect.center

        # reset hit rect for player hit detection
        self.hit_rect.center = (old_pos.x, old_pos.y)
        # player hits collision detection
        self.hit_rect.centerx = self.pos.x
        self.player_hit("x")
        self.hit_rect.centery = self.pos.y
        self.player_hit("y")
        # match the sprite's rect with where it should be based on the hit rect
        self.rect.center = self.hit_rect.center

        # if two players crash into each other
        self.player_collisions()

        # player gets item
        self.item_collisions()

        # update the image with the correct positioning
        self.update_image()


class Obstacle(pg.sprite.Sprite):
    def __init__(self, client, x, y, width, height, type):
        if type == "wall":
            self.groups = client.all_sprites, client.obstacles, client.walls, client.colliders
            # debug
            self.color = OBSTACLE_COLOR
        elif type == "shallow":
            self.groups = client.all_sprites, client.obstacles, client.shallows, client.colliders
            # debug
            self.color = SHALLOWS_COLOR
        pg.sprite.Sprite.__init__(self, self.groups)
        self.rect = pg.Rect(x, y, width, height)
        self.hit_rect = self.rect
        self.type = type


class SpriteItem(pg.sprite.Sprite):
    def __init__(self, client, name, pos, item_id):
        self._layer = ITEM_LAYER
        self.groups = client.all_sprites, client.items, client.colliders
        pg.sprite.Sprite.__init__(self, self.groups)
        # image
        self.image = client.item_imgs[name]
        self.rect = self.image.get_rect()
        self.hit_rect = self.rect
        self.rect.center = pos
        self.hit_rect.center = pos
        # data
        self.client = client
        self.name = name
        self.pos = pos
        self.item_id = item_id
        self.active = False
        # item bob
        self.tween = easeInOutSine
        self.step = 0
        self.direction = 1
        # debug
        self.color = ITEM_SPAWN_COLOR

    def update(self):
        # bobbing motion (subtract 0.5 to shift halfway)
        offset = BOB_RANGE * (self.tween(self.step / BOB_RANGE) - 0.5)
        self.rect.centery = self.pos.y + offset * self.direction
        self.step += BOB_SPEED
        # switch and reset if hit maximum
        if self.step > BOB_RANGE:
            self.step = 0
            self.direction *= -1


class SpriteBullet(pg.sprite.Sprite):
    def __init__(self, client, bullet_id, pos, angle):
        self.groups = client.all_sprites, client.bullets, client.colliders
        pg.sprite.Sprite.__init__(self, self.groups)
        self.image = client.bullet_imgs['basic']
        self.image = pg.transform.rotate(self.image, angle)
        self.rect = self.image.get_rect()
        self.hit_rect = self.rect
        self.pos = pos
        self.rect.center = pos
        # save data to access later for deleting
        self.bullet_id = bullet_id
        self.client = client
        # debug
        self.color = ORANGE

    def update(self):
        # remove the bullet if it no longer exists in the game
        if self.bullet_id not in self.client.game['bullets']:
            self.kill()
        # if the bullet still exists, check if it should be killed
        elif pg.sprite.spritecollideany(self, self.client.walls):
            # tell the server to delete the sprite if it hits a wall
            self.client.player.overwrites['kill bullets'].append(self.bullet_id)
            self.kill()
        # update the bullet with the latest position
        else:
            self.pos = self.client.game['bullets'][self.bullet_id][0]
            self.rect = self.image.get_rect()
            self.hit_rect = self.rect
            self.rect.center = self.pos
