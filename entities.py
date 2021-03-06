from random import choice, randint
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
        # shooting
        self.ammo = 0
        # kills and deaths
        self.kills = 0
        self.deaths = 0
        self.score = 0
        # position
        self.pos = Vec(0, 0)
        self.rot = 0
        # effects
        self.frozen = False
        self.respawn = False
        # destroy[0] is if the player should be destroyed, destroy[1] is which player id destroyed them
        self.destroy = (False, None)
        self.current_crash_time = False
        self.current_respawn_time = False
        self.power_invincible = False
        # data for server to process
        self.overwrites = {"collisions": [],  # the player collided with a player should should be killed
                           "items": [],  # the player picked up an item
                           "new bullets": [],  # the server should make a new bullet
                           "kill bullets": [],  # which bullet ids the server should remove
                           "deaths by": [],  # which player id killed the player
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
        # shooting
        self.ammo = net_player.ammo
        self.last_shoot = 0
        # kills and deaths
        self.kills = 0
        self.deaths = 0
        self.score = net_player.score
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
        # keep track of which players the client has killed recently to not send multiple kill messages to the server
        self.recent_collisions = dict([(player_id, False) for player_id in client.player_ids])
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
            self.image.fill(POWER_COLOR, special_flags=pg.BLEND_RGB_ADD)
        # blue frozen effect
        if self.frozen:
            self.image.fill(FROZEN_COLOR, special_flags=pg.BLEND_RGBA_MULT)

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
            for shoot_angle in NORMAL_SHOOT_ANGLES:
                bullet_data = [Vec(self.pos.x, self.pos.y), self.rot + shoot_angle, self.player_id]
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

        # move faster during power mode
        if self.power_invincible:
            self.rot_acc *= POWER_SPEED_MULTIPLIER
            self.acc *= POWER_SPEED_MULTIPLIER

    def apply_friction(self, movement_type):
        # north, south, east, and west movement
        if movement_type == "nsew":
            hits = pg.sprite.spritecollide(self, self.client.shallows, False, collide_hit_rect_both)
            # only apply slow shallow movement if the player currently does not have star power
            if hits and not self.power_invincible:
                return PLAYER_SHALLOW_FRICTION
            else:
                return PLAYER_WATER_FRICTION
        # rotation movement
        elif movement_type == "rot":
            hits = pg.sprite.spritecollide(self, self.client.shallows, False, collide_hit_rect_both)
            # only apply slow shallow movement if the player currently does not have star power
            if hits and not self.power_invincible:
                return PLAYER_SHALLOW_ROT_FRICTION
            else:
                return PLAYER_WATER_ROT_FRICTION

    def respawn_player(self):
        # reset effects and attributes
        self.power_invincible = False
        self.power_time = False
        self.ammo = 0
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
                self.destroy_player(hit.player_id)
            # let the server know someone should be destroyed
            if hit != self and self.power_invincible and not hit.power_invincible and hit.current_respawn_time is False and hit.current_crash_time is False:
                # only send a collisions notice to the server if the client player hasn't already recently
                if self.recent_collisions[hit.player_id]:
                    if pg.time.get_ticks() - self.recent_collisions[hit.player_id] > PLAYER_CRASH_DURATION:
                        self.recent_collisions[hit.player_id] = pg.time.get_ticks()
                        self.overwrites['collisions'].append(hit.player_id)
                else:
                    self.recent_collisions[hit.player_id] = pg.time.get_ticks()
                    self.overwrites['collisions'].append(hit.player_id)

    def item_collisions(self):
        # test for collision
        hits = pg.sprite.spritecollide(self, self.client.items, False, collide_hit_rect_both)
        for hit in hits:
            # power items give the power invincibility effect
            if hit.current_item == "power":
                self.power_invincible = True
                self.power_time = pg.time.get_ticks()
            if hit.current_item == "bullet":
                self.ammo += BULLET_AMOUNT
            if hit.current_item == "largebullet":
                self.ammo += LARGE_BULLET_AMOUNT
            # make sure the item is set to inactive on the client side
            self.client.item_spawns[hit.item_id][0] = False
            # tell the server the item should be inactive
            self.overwrites['items'].append(hit.item_id)
            # destroy the item
            hit.kill()

    def bullet_collisions(self):
        # test for collision
        hits = pg.sprite.spritecollide(self, self.client.bullets, False, collide_hit_rect_both)
        for hit in hits:
            # only count as a kill if it wasn't a bullet made by the client player
            if hit.owner_player_id != self.player_id:
                # destroy the bullet
                self.overwrites['kill bullets'].append(hit.bullet_id)
                hit.kill()
                # only count it as a kill if the player can be legally killed
                if not self.power_invincible and self.current_crash_time is False and self.current_respawn_time is False:
                    # destroy the player
                    self.destroy_player(hit.owner_player_id)

    def destroy_player(self, killed_by_player_id):
        self.overwrites['deaths by'].append(killed_by_player_id)
        self.destroy = (False, None)
        self.image_string = PLAYER_IMGS["broken" + self.image_color]
        self.crash_time = pg.time.get_ticks()
        self.current_crash_time = pg.time.get_ticks() - self.crash_time

    def new_game_player_reset(self):
        self.last_shoot = 0
        self.image_string = PLAYER_IMGS[self.image_color]
        self.recent_collisions = dict([(player_id, False) for player_id in self.client.player_ids])

    def update_client(self):
        # new game respawn
        if self.client.new_game:
            self.new_game_player_reset()
            self.respawn_player()
        # destroy the player if told to by the server
        if self.destroy[0]:
            self.destroy_player(self.destroy[1])
        # respawn the player if told to by the server
        if self.respawn:
            self.respawn_player()
        # destroy the player if collided with a bullet
        self.bullet_collisions()

        # update the recent collisions with new players that have joined
        for player_id in self.client.player_ids:
            if player_id not in self.recent_collisions:
                self.recent_collisions[player_id] = False
                print("Added New Player ID", player_id)

        # if two players crash into each other
        self.player_collisions()

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
            # vf = vi + at
            self.vel = self.vel + self.acc * self.client.dt

            # displacement
            # d = vit + 1/2at^2
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
        # bullet collisions
        self.bullet_collisions()

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
    def __init__(self, client, item_id, name, current_item, pos):
        self._layer = ITEM_LAYER
        self.groups = client.all_sprites, client.items, client.colliders
        pg.sprite.Sprite.__init__(self, self.groups)
        # image
        self.image = client.item_imgs[current_item]
        self.rect = self.image.get_rect()
        self.hit_rect = self.rect
        self.rect.center = pos
        self.hit_rect.center = pos
        # data
        self.client = client
        self.name = name
        self.current_item = current_item
        self.pos = pos
        self.item_id = item_id
        # item bob
        self.tween = easeInOutSine
        self.step = randint(0, BOB_RANGE)
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
    def __init__(self, client, bullet_id, pos, angle, owner_player_id, do_rot):
        self.groups = client.all_sprites, client.bullets, client.colliders
        pg.sprite.Sprite.__init__(self, self.groups)
        self.image = client.bullet_imgs['basic']
        # rotate the image in the direction is is facing or not
        if do_rot:
            self.image = pg.transform.rotate(self.image, angle)
        self.rect = self.image.get_rect()
        # adjust the image size
        self.image = pg.transform.scale(self.image, (self.rect.width * BULLET_SIZE_MULTIPLIER,
                                                     self.rect.height * BULLET_SIZE_MULTIPLIER))
        self.rect = self.image.get_rect()
        self.hit_rect = self.rect
        self.pos = pos
        self.rect.center = pos
        # keeps track of how far the bullet has gone to know when to kill it
        self.total_distance = Vec(0, 0)
        # save data to access later
        self.bullet_id = bullet_id
        self.owner_player_id = owner_player_id
        self.client = client
        # debug
        self.color = ORANGE

    def update(self):
        # remove the bullet if it no longer exists in the game
        if self.bullet_id not in self.client.game['bullets']:
            self.kill()  # there is no need to tell the server to delete it, as it has already been deleted server-side
        # if the bullet still exists, check if it should be killed
        elif pg.sprite.spritecollideany(self, self.client.walls):
            self.destroy()
        # update the bullet with the latest position
        else:
            new_pos = self.client.game['bullets'][self.bullet_id][0]
            self.total_distance += self.pos - new_pos
            # kill the bullet if it has moved as far as it can, use squares as it is faster to calculate
            if self.total_distance.length_squared() >= BULLET_RANGE ** 2:
                self.destroy()
            else:
                self.pos = new_pos
                self.rect = self.image.get_rect()
                self.hit_rect = self.rect
                self.rect.center = self.pos

    def destroy(self):
        # tell the server to delete the sprite if it hits a wall
        self.client.player.overwrites['kill bullets'].append(self.bullet_id)
        self.kill()
