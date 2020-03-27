from os import path
import pygame as pg
from pygame.locals import *
from network import Network
from player import SpritePlayer
from tilemap import Camera, TiledMap
from widgets import EntryBox, Button
from settings import *


class Client:
    def __init__(self):
        # server to connect to
        self.server_ip = SERVER_IP
        self.port = PORT
        # client attributes
        self.username = "enter username"
        self.running = True
        self.menu = True
        self.connected = False
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
        self.camera = None
        # sprite groups
        self.sprite_players = pg.sprite.Group()
        # start screen
        self.entry_boxes = {}
        self.buttons = {}
        self.start_screen_bg = None
        # fonts
        self.theme_font = None
        # debug mode
        self.debug = False
        # display attributes
        self.fullscreen = True
        self.screen_width = SCREEN_WIDTH_MAX
        self.screen_height = SCREEN_HEIGHT_MAX
        # data to load
        self.player_imgs = {}

    def load(self):
        # folders
        game_folder = path.dirname(__file__)
        font_folder = path.join(game_folder, "font")
        img_folder = path.join(game_folder, "img")
        self.map_folder = path.join(game_folder, "map")
        # fonts
        self.theme_font = path.join(font_folder, THEME_FONT)
        # images
        for img in PLAYER_IMGS:
            new_img = pg.image.load(path.join(img_folder, img)).convert_alpha()
            #self.player_imgs[img] = pg.transform.scale(new_img, (PLAYER_WIDTH, PLAYER_HEIGHT))
            self.player_imgs[img] = new_img
        # start screen background
        self.start_screen_bg = pg.Surface((self.screen_width, self.screen_height))
        bg_image = pg.image.load(path.join(img_folder, START_BG_IMG)).convert_alpha()
        bg_image_rect = bg_image.get_rect()
        ratio = int(TILESIZE / bg_image_rect.width)
        bg_image = pg.transform.scale(bg_image, (bg_image_rect.width * ratio, bg_image_rect.height * ratio))
        for x in range(0, self.screen_width, TILESIZE):
            for y in range(0, self.screen_height, TILESIZE):
                self.start_screen_bg.blit(bg_image, (x, y))

    def load_map(self):
        # map creation
        self.map = TiledMap(path.join(self.map_folder, "map1.tmx"))
        self.map_img = self.map.make_map()
        self.map_rect = self.map_img.get_rect()

    def run(self):
        # start pygame
        pg.init()
        # set up display
        self.clock = pg.time.Clock()
        self.screen = pg.display.set_mode((self.screen_width, self.screen_height), pg.FULLSCREEN)
        pg.display.set_caption(
            f"Client - ID: {self.player_id} - Username: {self.username} - FPS: {round(self.clock.get_fps(), 2)}")

        # load data
        self.load()

        # load map and then camera
        self.load_map()
        self.camera = Camera(self.map.width, self.map.height)

        while self.running:
            # the start screen
            self.main_menu()

            # connect to a server only if program is running and port is an integer
            if self.running:
                # connect
                self.connect()
                # game loop
                self.game_loop()
                # reset client data when the client disconnects
                self.reset_data()
                # end of server connection, return to main menu

            # quit the program
            else:
                print("\nQuiting Program")
                pg.quit()

    def main_menu(self):
        # allows the user to hold down a key when entering text into an entry box
        pg.key.set_repeat(REPEAT_PAUSE, REPEAT_RATE)

        # entry boxes
        self.entry_boxes["username"] = EntryBox(self.screen_width / 2 - ENTRY_WIDTH / 2, 100, ENTRY_WIDTH, ENTRY_HEIGHT,
                                                self.theme_font, VALID_USERNAME, text=self.username)
        self.entry_boxes["server ip"] = EntryBox(self.screen_width / 2 - ENTRY_WIDTH / 2, 150, ENTRY_WIDTH, ENTRY_HEIGHT,
                                                 self.theme_font, VALID_IP, text=self.server_ip)
        self.entry_boxes["port"] = EntryBox(self.screen_width / 2 - ENTRY_WIDTH / 2, 200, ENTRY_WIDTH, ENTRY_HEIGHT,
                                            self.theme_font, VALID_PORT, text=str(self.port))
        # buttons
        self.buttons["connect"] = Button(self.screen_width / 2 - BUTTON_WIDTH / 2, 300, BUTTON_WIDTH, BUTTON_HEIGHT,
                                         self.theme_font, text="Connect")
        self.buttons["quit"] = Button(self.screen_width / 2 - BUTTON_WIDTH / 2, 400, BUTTON_WIDTH, BUTTON_HEIGHT,
                                      self.theme_font, text="Quit")

        # main menu loop
        while self.menu:
            # pause
            self.dt = self.clock.tick(FPS) / 1000
            # events, update, draw
            self.menu_events()
            self.menu_update()
            self.menu_draw()

        # cancels the effect that allows the user to hold down a key
        pg.key.set_repeat()

    def game_loop(self):
        # game loop while connected to the server
        while self.connected:
            # pause
            self.dt = self.clock.tick(FPS) / 1000
            # events, update, draw
            self.game_events()
            self.game_update()
            self.game_draw()

    def reset_data(self):
        # received over network
        self.game = None
        self.player = None
        self.player_id = None
        # stored data
        self.player_ids = []
        # sprite groups
        self.sprite_players = pg.sprite.Group()

    def connect(self):
        # connect to the server
        print(f"\nConnecting To Server At {self.server_ip}:{self.port}")
        self.network = Network(self.server_ip, self.port)
        self.player = self.network.get_player()
        # connected if a response was received from the server and the client's data isn't taken
        if self.player and self.verify_client():
            self.connected = True
        else:
            self.menu = True

    def disconnect(self):
        print(f"\nDisconnected From Server At {self.network.server_ip}:{self.network.server_port}")
        self.network.client.close()
        self.connected = False
        self.menu = True

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

    def menu_events(self):
        for event in pg.event.get():
            # quit the game
            if event.type == QUIT:
                self.menu = False
                self.running = False
            # quit the game
            if event.type == KEYDOWN:
                # quit the program
                if event.key == K_ESCAPE:
                    self.menu = False
                    self.running = False
                # fullscreen mode toggle
                if event.key == K_f:
                    # toggle fullscreen
                    self.fullscreen = not self.fullscreen
                    # change screen size accordingly
                    if self.fullscreen:
                        # fullscreen mode
                        self.screen_width = SCREEN_WIDTH_MAX
                        self.screen_height = SCREEN_HEIGHT_MAX
                        self.screen = pg.display.set_mode((self.screen_width, self.screen_height), FULLSCREEN)
                    else:
                        # mini screen mode
                        self.screen_width = SCREEN_WIDTH_MINI
                        self.screen_height = SCREEN_HEIGHT_MINI
                        self.screen = pg.display.set_mode((self.screen_width, self.screen_height))
                    # reposition widgets
                    for entry_box in self.entry_boxes.values():
                        entry_box.rect.x = self.screen_width / 2 - ENTRY_WIDTH / 2
                    for button in self.buttons.values():
                        button.rect.x = self.screen_width / 2 - BUTTON_WIDTH / 2

            # update entry boxes with pygame events
            for entry_box in self.entry_boxes.values():
                entry_box.events(event)

            # update buttons with pygame events and mouse position
            for button_name, button in self.buttons.items():
                if button.events(event, pg.mouse.get_pos()):
                    if button_name == "connect":
                        self.menu = False
                    elif button_name == "quit":
                        self.menu = False
                        self.running = False

    def menu_update(self):
        # update display caption with useful information
        pg.display.set_caption(
            f"Client - ID: {self.player_id} - Username: {self.username} - FPS: {round(self.clock.get_fps(), 2)}")

        # update with the data entered by the user
        self.username = self.entry_boxes['username'].text
        self.server_ip = self.entry_boxes['server ip'].text
        port_text = self.entry_boxes['port'].text
        if port_text:
            self.port = int(self.entry_boxes['port'].text)
        else:
            self.port = 0

    def menu_draw(self):
        # background
        self.screen.fill((255, 255, 255))

        self.screen.blit(self.start_screen_bg, (0, 0))

        # title
        self.draw_text(GAME_TITLE, TITLE_SIZE, TEXT_COLOR,
                       self.screen_width / 2, 50, align='s', font_name=self.theme_font)

        # entry boxes
        for entry_box in self.entry_boxes.values():
            entry_box.draw(self.screen)

        # buttons
        for button in self.buttons.values():
            button.draw(self.screen)

        # update the client's monitor
        pg.display.flip()

    def game_events(self):
        for event in pg.event.get():
            # quit the game
            if event.type == QUIT:
                self.disconnect()
                self.menu = False
                self.running = False
            # key presses
            if event.type == KEYDOWN:
                # quit the game
                if event.key == K_ESCAPE:
                    self.disconnect()
                # debug mode toggle
                if event.key == K_b:
                    self.debug = not self.debug
                # fullscreen mode toggle
                if event.key == K_f:
                    # toggle fullscreen
                    self.fullscreen = not self.fullscreen
                    # change screen size accordingly
                    if self.fullscreen:
                        # fullscreen mode
                        self.screen_width = SCREEN_WIDTH_MAX
                        self.screen_height = SCREEN_HEIGHT_MAX
                        self.screen = pg.display.set_mode((self.screen_width, self.screen_height), FULLSCREEN)
                    else:
                        # mini screen mode
                        self.screen_width = SCREEN_WIDTH_MINI
                        self.screen_height = SCREEN_HEIGHT_MINI
                        self.screen = pg.display.set_mode((self.screen_width, self.screen_height))

    def game_update(self):
        if self.connected:
            # receive the updated game over the network from the server
            # send the
            self.game = self.network.send(self.player)

            # update client's player with data received over the network
            self.player = self.game['players'][self.player_id]
            # update the client data with the data received over the network
            self.username = self.player.username

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
                    self.camera.update(sprite_player, self.screen_width, self.screen_height)

        # update display caption with useful information
        pg.display.set_caption(
            f"Client - ID: {self.player_id} - Username: {self.username} - FPS: {round(self.clock.get_fps(), 2)}")

    def draw_grid(self):
        for x in range(self.camera.x, self.screen_width, TILESIZE):
            pg.draw.line(self.screen, GRID_COLOR, (x, 0), (x, self.screen_height))
        for y in range(self.camera.y, self.screen_height, TILESIZE):
            pg.draw.line(self.screen, GRID_COLOR, (0, y), (self.screen_width, y))

    def game_draw(self):
        if self.connected:

            # background
            self.screen.fill((255, 255, 255))

            # map image
            self.screen.blit(self.map_img, self.camera.apply_rect(self.map_rect))

            # tile grid
            if self.debug:
                self.draw_grid()
            # thick map boundary line
            # pg.draw.rect(self.screen, GRID_COLOR, (0 + self.camera.x, 0 + self.camera.y, MAP_WIDTH, MAP_HEIGHT), 30)

            # player images
            # frozen color effect
            for sprite_player in self.sprite_players:
                if sprite_player.frozen:
                    sprite_player.image.fill((200, 200, 250, 255), special_flags=pg.BLEND_RGBA_MULT)
            # player sprite image and username
            for sprite_player in self.sprite_players:
                # blit to screen as done below so that the camera can be applied
                self.screen.blit(sprite_player.image, self.camera.apply_sprite(sprite_player))
                self.draw_text(sprite_player.username, USERNAME_SIZE, sprite_player.fillcolor,
                               sprite_player.pos.x + self.camera.x, sprite_player.rect.top + self.camera.y,
                               align='s', font_name=self.theme_font)

            # update the client's monitor
            pg.display.flip()

    def draw_text(self, text, size, fillcolor, x, y, align='n', font_name=None, ):
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
c.run()
