from os import path
import pygame as pg
from pygame.locals import *
from network import Network
from player import SpritePlayer
from tilemap import Camera
from settings import *


class Client:
    def __init__(self):
        # client attributes
        self.running = True
        self.connected = False
        self.username = input("Enter Username: ")
        # received over network
        self.game = None
        self.network = None
        self.player = None
        self.player_id = None
        # stored data
        self.player_ids = []
        # game attributes
        self.screen = None
        self.clock = None
        self.dt = None
        # sprite groups
        self.sprite_players = pg.sprite.Group()
        # data to load
        self.player_imgs = {}
        # start client by connecting to the server
        self.connect()
        if self.connected:
            self.run()

    def load(self):
        # folders
        game_folder = path.dirname(__file__)
        img_folder = path.join(game_folder, 'img')
        for img in PLAYER_IMGS:
            new_img = pg.image.load(path.join(img_folder, img)).convert_alpha()
            self.player_imgs[img] = pg.transform.scale(new_img, (PLAYER_WIDTH, PLAYER_HEIGHT))

    def connect(self):
        # connect to the server
        print(f"Connecting To Server At {SERVER_IP}:{PORT}")
        self.network = Network()
        self.player = self.network.get_player()
        # connected if a response was received from the server and the client's data isn't taken
        if self.player and self.verify_client():
            self.connected = True

    def verify_client(self):
        # set client's id to received player id
        self.player_id = self.player.player_id
        # set player object username to client's chosen username
        self.player.username = self.username
        verify, reason = self.network.send(self.player)
        if verify:
            print("Successfully Joined Server")
        else:
            print("Unable To Connect To Server:", reason)
        return verify

    def disconnect(self):
        self.running = False
        pg.quit()

    def run(self):
        # start pygame
        pg.init()
        # set up display
        self.clock = pg.time.Clock()
        self.camera = Camera(MAP_WIDTH, MAP_HEIGHT)
        self.screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        #self.screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), FULLSCREEN)
        pg.display.set_caption(
            f"Client - ID: {self.player_id} - Username: {self.username} - FPS: {round(self.clock.get_fps(), 2)}")
        # load data
        self.load()
        # game loop
        while self.running:
            # pause
            self.dt = self.clock.tick(FPS) / 1000
            # events, update, draw
            self.events()
            self.update()
            self.draw()

    def events(self):
        for event in pg.event.get():
            # quit the game
            if event.type == QUIT:
                self.disconnect()
            # quit the game
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                self.disconnect()

    def update(self):
        # receive the updated game over the network from the server
        # send the
        self.game = self.network.send(self.player)

        # update client's player with data received over the network
        self.player = self.game['players'][self.player_id]
        # update the client data with the data received over the network
        self.username = self.player.username
        # update display caption with useful information
        pg.display.set_caption(
            f"Client - ID: {self.player_id} - Username: {self.username} - FPS: {round(self.clock.get_fps(), 2)}")

        # create new pygame sprites for newly joined players
        for player_id in self.game['players']:
            if player_id not in self.player_ids:
                self.player_ids.append(player_id)
                SpritePlayer(self, self.game['players'][player_id])
        # update all sprite data, or kill the sprite if the player has disconnected
        self.sprite_players.update()

        # update the client's player sprite only, this means checking for key presses and collision detection
        for sprite_player in self.sprite_players:
            if sprite_player.player_id == self.player_id:
                sprite_player.move()

        # update the client's net work player to match the client's sprite player
        # this is required to send the server the updated data of the client's player
        for sprite_player in self.sprite_players:
            if sprite_player.player_id == self.player_id:
                self.player.update(sprite_player)

        # update camera
        for sprite_player in self.sprite_players:
            if sprite_player.player_id == self.player_id:
                self.camera.update(sprite_player)

    def draw_grid(self):
        for x in range(self.camera.x, SCREEN_WIDTH, TILESIZE):
            pg.draw.line(self.screen, GRID_COLOR, (x, 0), (x, SCREEN_HEIGHT))
        for y in range(self.camera.y, SCREEN_HEIGHT, TILESIZE):
            pg.draw.line(self.screen, GRID_COLOR, (0, y), (SCREEN_WIDTH, y))

    def draw(self):
        # background
        self.screen.fill((255, 255, 255))

        # tile grid
        self.draw_grid()
        # thick map boundary line
        pg.draw.rect(self.screen, (GRID_COLOR), (0 + self.camera.x, 0 + self.camera.y, MAP_WIDTH, MAP_HEIGHT), 30)

        # player images
        # frozen color effect
        for sprite_player in self.sprite_players:
            if sprite_player.frozen:
                sprite_player.image.fill((200, 200, 250, 255), special_flags=pg.BLEND_RGBA_MULT)
        # player sprite image and username
        for sprite_player in self.sprite_players:
            # blit to screen as done below so that the camera can be applied
            self.screen.blit(sprite_player.image, self.camera.apply_sprite(sprite_player))
            self.draw_text(sprite_player.username, "ARCADECLASSIC.TTF", USERNAME_SIZE, sprite_player.fillcolor,
                           sprite_player.pos.x + self.camera.x, sprite_player.rect.top + self.camera.y, align='s')

        # update the client's monitor
        pg.display.flip()

    def draw_text(self, text, font_name, size, fillcolor, x, y, align='n'):
        font = pg.font.Font(font_name, size)
        text_surface = font.render(text, True, fillcolor)
        text_rect = text_surface.get_rect()
        if align == 'nw':
            text_rect.topleft = (x, y)
        elif align == 'ne':
            text_rect.topright = (x, y)
        elif align == 'sw':
            text_rect.bottomleft = (x, y)
        elif align == 'se':
            text_rect.bottomright = (x, y)
        elif align == 'n':
            text_rect.midtop = (x, y)
        elif align == 's':
            text_rect.midbottom = (x, y)
        elif align == 'e':
            text_rect.midright = (x, y)
        elif align == 'w':
            text_rect.midleft = (x, y)
        elif align == 'center':
            text_rect.center = (x, y)
        self.screen.blit(text_surface, text_rect)


c = Client()
