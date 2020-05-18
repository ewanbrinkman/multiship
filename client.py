from os import path
import pygame as pg
from pygame.locals import *
from network import Network
from entities import SpritePlayer, update_player, Obstacle
from tilemap import Camera, TiledMap
from widgets import EntryBox, Button
from settings import *


class Client:
    def __init__(self):
        # server to connect to
        self.server_ip = SERVER_IP
        self.port = PORT
        # client attributes
        self.username = ''
        self.image_string = PLAYER_IMGS[PLAYER_IMGS_CYCLE[0]]
        self.running = True
        self.menu = True
        self.connected = False
        # network data
        self.game = None
        self.network = None
        self.player = None
        self.player_id = None
        self.kicked = False
        # stored data
        self.player_ids = []
        # game attributes
        self.screen = None
        self.clock = None
        self.dt = None
        self.camera = None
        # sprite groups
        self.all_sprites = pg.sprite.Group()
        self.players = pg.sprite.Group()
        self.obstacles = pg.sprite.Group()
        self.walls = pg.sprite.Group()
        self.shallows = pg.sprite.Group()
        # display
        self.theme_font = None
        self.fullscreen = True
        self.debug = False
        # data to load
        self.map_folder = None
        self.icon = None
        self.player_imgs = {}
        # start screen
        self.current_img_cycle = 0
        self.entry_boxes = {}
        self.buttons = {}
        self.menu_bg = None
        self.menu_bg_shiftx = 0
        self.menu_bg_shifty = 0
        self.main_menu_text = MAIN_MENU_TEXT
        self.selected_player_image = None
        self.selected_player_image_rect = None
        # maps
        self.map = None
        self.current_map = None
        # music
        self.menu_music = None
        self.game_music = None

    def load(self):
        # folders
        game_folder = path.dirname(__file__)
        font_folder = path.join(game_folder, 'font')
        img_folder = path.join(game_folder, 'img')
        snd_folder = path.join(game_folder, 'snd')
        self.map_folder = path.join(game_folder, 'map')

        # app icon
        self.icon = pg.image.load(path.join(img_folder, ICON_IMG))

        # fonts
        self.theme_font = path.join(font_folder, THEME_FONT)

        # images
        for filename in PLAYER_IMGS.values():
            new_img = pg.image.load(path.join(img_folder, filename)).convert_alpha()
            # rotate so the sprite moves in the direction it is pointing
            self.player_imgs[filename] = pg.transform.rotate(new_img, 90)

        # sounds
        self.menu_music = path.join(snd_folder, MENU_BG_MUSIC)
        self.game_music = path.join(snd_folder, GAME_BG_MUSIC)

        # load map
        self.render_maps()

    def render_maps(self):
        # menu background
        self.menu_bg = TiledMap(path.join(self.map_folder, MENU_BG_IMG))
        self.menu_bg.make_map()
        # amount to shift everything, to make up for the background being slightly bigger then the screen size
        self.menu_bg_shiftx = (self.menu_bg.rect.width - SCREEN_WIDTH) / 2
        self.menu_bg_shifty = (self.menu_bg.rect.height - SCREEN_HEIGHT) / 2

    def create_map(self, filename):
        # basic map background image with data
        self.map = TiledMap(path.join(self.map_folder, filename))
        self.map.make_map()

        # map objects
        for tile_object in self.map.tilemap_data.objects:
            # obstacles
            if tile_object.type == 'obstacle':
                if tile_object.name == 'wall':
                    Obstacle(self, tile_object.x, tile_object.y,
                             tile_object.width, tile_object.height, 'wall')
                if tile_object.name == 'shallow':
                    Obstacle(self, tile_object.x, tile_object.y,
                             tile_object.width, tile_object.height, 'shallow')

    def connect(self):
        # connect to the server
        print(f'\nConnecting To Server At {self.server_ip}:{self.port}')
        self.network = Network(self.server_ip, self.port)
        self.player = self.network.get_player()
        # connected if a response was received from the server and the client's data isn't taken
        if self.player:
            verify, reason = self.verify_client()
            if verify:
                # connection successful
                self.connected = True
                return True, reason
            else:
                # connection refused due: not verified
                return False, reason
        else:
            # cannot connect to specified address
            return False, f'Cannot Connect To A Server At {self.server_ip}:{self.port}'

    def disconnect(self):
        if self.kicked:
            print(f'\nKicked From Server At {self.network.server_ip}:{self.network.server_port}')
        else:
            print(f'\nDisconnected From Server At {self.network.server_ip}:{self.network.server_port}')
        self.network.client.close()
        self.connected = False
        self.menu = True

    def verify_client(self):
        # set client's id to received player id
        self.player_id = self.player.player_id

        # set player data to the settings set by the client at main menu
        self.player.username = self.username
        self.player.image_color = PLAYER_IMGS_CYCLE[self.current_img_cycle]
        self.player.image_string = self.image_string

        verify, reason = self.network.send(self.player)
        if verify:
            print('Successfully Joined Server')
        else:
            reason = 'Connection Refused: ' + reason
            print(reason)
            self.main_menu_text = reason
        return verify, reason

    def run(self):
        # start pygame
        pg.mixer.pre_init(44100, -16, 1, 2048)
        pg.init()
        # clock
        self.clock = pg.time.Clock()
        # set up display
        self.screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pg.FULLSCREEN)
        pg.display.set_caption(
            f'Client ID: {self.player_id} - Username: {self.username} - FPS: {round(self.clock.get_fps(), 2)}')

        # load data
        self.load()

        # icon
        pg.display.set_icon(self.icon)

        while self.running:
            # the start screen
            self.main_menu()

            # connect to a server only if program is running
            if self.running:
                self.game_loop()
            # quit the program
            else:
                print('\nQuiting Program Loop...')

        print('Quiting Pygame...')
        pg.quit()

        print('Bye!')

    def main_menu(self):
        # allows the user to hold down a key when entering text into an entry box
        pg.key.set_repeat(REPEAT_PAUSE, REPEAT_RATE)

        # set the current selected player image
        self.update_player_image()

        # entry boxes
        self.entry_boxes['username'] = EntryBox(SCREEN_WIDTH / 2 - ENTRY_WIDTH / 2,
                                                140, ENTRY_WIDTH,
                                                self.theme_font, VALID_USERNAME, text=self.username)
        self.entry_boxes['server ip'] = EntryBox(SCREEN_WIDTH / 2 - ENTRY_WIDTH / 2,
                                                 210, ENTRY_WIDTH,
                                                 self.theme_font, VALID_IP, text=self.server_ip)
        self.entry_boxes['port'] = EntryBox(SCREEN_WIDTH / 2 - ENTRY_WIDTH / 2,
                                            280, ENTRY_WIDTH,
                                            self.theme_font, VALID_PORT, text=str(self.port))
        # buttons
        self.buttons['connect'] = Button(SCREEN_WIDTH / 2 - SCREEN_WIDTH / 4,
                                         TILESIZE * 11 + TILESIZE / 2 - TILESIZE / 8, BUTTON_WIDTH, BUTTON_HEIGHT,
                                         self.theme_font, text='Connect')
        self.buttons['quit'] = Button(SCREEN_WIDTH / 2 + SCREEN_WIDTH / 4 - BUTTON_WIDTH,
                                      TILESIZE * 11 + TILESIZE / 2 - TILESIZE / 8, BUTTON_WIDTH, BUTTON_HEIGHT,
                                      self.theme_font, text='Quit')
        self.buttons['right'] = Button(SCREEN_WIDTH / 2 + 100, 570 - self.selected_player_image_rect.height / 2,
                                       BUTTON_WIDTH, BUTTON_HEIGHT, self.theme_font, text='Right')
        self.buttons['left'] = Button(SCREEN_WIDTH / 2 - 100 - BUTTON_WIDTH, 570 - self.selected_player_image_rect.height / 2,
                                       BUTTON_WIDTH, BUTTON_HEIGHT, self.theme_font, text='Left')

        # background music
        pg.mixer.music.load(self.menu_music)
        pg.mixer.music.play(loops=-1)

        # main menu loop
        while self.menu:
            # pause
            self.dt = self.clock.tick(FPS) / 1000
            # events, update, draw
            self.menu_events()
            self.menu_update()
            self.menu_draw()

        # cancels repeat key effect to not mess up key presses during the game
        pg.key.set_repeat()

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
                if event.key == K_F1:
                    self.fullscreen = not self.fullscreen
                    if self.fullscreen:
                        self.screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), FULLSCREEN)
                    else:
                        self.screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
                # mute volume
                if event.key == K_F2:
                    if pg.mixer.music.get_volume():
                        pg.mixer.music.set_volume(0)
                    else:
                        pg.mixer.music.set_volume(1)
                # change selected image
                if event.key == K_RIGHT:
                    self.select_player_image('right')
                # change selected image
                if event.key == K_LEFT:
                    self.select_player_image('left')

            # update entry boxes with pygame events
            for entry_box in self.entry_boxes.values():
                entry_box.events(event)

            # update buttons with pygame events and mouse position
            for button_name, button in self.buttons.items():
                if button.events(event, pg.mouse.get_pos()):
                    # update display to say connecting
                    if button_name == 'connect':
                        # try to connect
                        verify, reason = self.connect()
                        if verify:
                            self.main_menu_text = 'Connected!'
                            self.menu = False
                        # cannot connect to the specified address
                        else:
                            self.main_menu_text = reason

                    elif button_name == 'quit':
                        self.menu = False
                        self.running = False

                    elif button_name == 'right':
                        self.select_player_image('right')

                    elif button_name == 'left':
                        self.select_player_image('left')

    def select_player_image(self, direction):
        # select a new player image by moving right or left through the list
        if direction == 'right':
            if self.current_img_cycle == (len(PLAYER_IMGS_CYCLE) - 1):
                self.current_img_cycle = 0
            else:
                self.current_img_cycle += 1
            self.image_string = PLAYER_IMGS[PLAYER_IMGS_CYCLE[self.current_img_cycle]]
        elif direction == 'left':
            if self.current_img_cycle == 0:
                self.current_img_cycle = (len(PLAYER_IMGS_CYCLE) - 1)
            else:
                self.current_img_cycle -= 1
            self.image_string = PLAYER_IMGS[PLAYER_IMGS_CYCLE[self.current_img_cycle]]

        # update the player image with the new selection
        self.update_player_image()

    def update_player_image(self):
        # get current player image selection
        self.selected_player_image = self.player_imgs[self.image_string]
        self.selected_player_image = pg.transform.rotate(self.selected_player_image, -90)
        # get rect to set placement
        self.selected_player_image_rect = self.selected_player_image.get_rect()
        self.selected_player_image_rect.center = (SCREEN_WIDTH / 2, 570)

    def menu_update(self):
        # update display caption with useful information
        pg.display.set_caption(
            f'Client - ID: {self.player_id} - Username: {self.username} - FPS: {round(self.clock.get_fps(), 2)}')

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

        self.screen.blit(self.menu_bg.image, (0 - self.menu_bg_shiftx, 0))

        # title
        self.draw_text(GAME_TITLE, TITLE_SIZE, TEXT_COLOR, SCREEN_WIDTH / 2, 70,
                       align='center', font_name=self.theme_font)
        # main menu text
        self.draw_text(self.main_menu_text, NORMAL_SIZE, TEXT_COLOR, SCREEN_WIDTH / 2, 450,
                       align='center', font_name=self.theme_font)

        # entry boxes
        for entry_box in self.entry_boxes.values():
            entry_box.draw(self.screen)

        # buttons
        for button in self.buttons.values():
            button.draw(self.screen)

        # draw on screen
        self.screen.blit(self.selected_player_image, self.selected_player_image_rect)

        # update the client's monitor
        pg.display.flip()

    def load_game_data(self):
        # get the game data to load anything before starting the game loop
        self.game = self.network.send(self.player)
        self.current_map = self.game['current map']

        # create the map
        self.create_map(self.current_map)
        # create camera to fit map size
        self.camera = Camera(self.map.width, self.map.height)

    def reset_data(self):
        # reset data after game session
        # received over network
        self.game = None
        self.player = None
        self.player_id = None

        # client side
        self.player_ids = []
        for sprite in self.all_sprites.sprites():
            sprite.kill()  # will delete all sprites, including any other groups they are also in
        if self.kicked:
            self.main_menu_text = 'You Have Been Kicked From The Server'
        else:
            self.main_menu_text = MAIN_MENU_TEXT


    def game_loop(self):
        # load game data based on game data received from the server
        self.load_game_data()

        # background music
        pg.mixer.music.load(self.game_music)
        pg.mixer.music.play(loops=-1)

        # game loop while connected to the server
        while self.connected:
            # pause
            self.dt = self.clock.tick(FPS) / 1000
            # events, update, draw
            self.game_events()
            if self.update_game_data():
                self.game_update()
                self.game_draw()

        # reset client data when the client disconnects
        self.reset_data()

    def update_game_data(self):
        # only get the latest data from the server if the client has not disconnected themselves
        if self.connected:
            # receive the updated game over the network from the server
            received = self.network.send(self.player)
            if received is EOFError or received is ConnectionResetError:
                self.kicked = True
                self.disconnect()
                return False
            else:
                self.game = received
                return True

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
                # fullscreen mode toggle
                if event.key == K_F1:
                    self.fullscreen = not self.fullscreen
                    if self.fullscreen:
                        self.screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), FULLSCREEN)
                    else:
                        self.screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
                # mute volume
                if event.key == K_F2:
                    if pg.mixer.music.get_volume():
                        pg.mixer.music.set_volume(0)
                    else:
                        pg.mixer.music.set_volume(1)
                # debug mode toggle
                if event.key == K_F3:
                    self.debug = not self.debug

    def game_update(self):
        # update client's player with data received over the network
        self.player = self.game['players'][self.player_id]

        # create new pygame sprites for newly joined players
        for player_id in self.game['players']:
            if player_id not in self.player_ids:
                self.player_ids.append(player_id)
                SpritePlayer(self, self.game['players'][player_id])
        # update all sprite data, or kill the sprite if the player has disconnected
        self.players.update()

        # update the client's player sprite only, this means checking for key presses and collision detection
        for sprite_player in self.players:
            if sprite_player.player_id == self.player_id:
                sprite_player.move()

        # update the client's net work player to match the client's sprite player
        # this is required to send the server the updated data of the client's player
        for sprite_player in self.players:
            if sprite_player.player_id == self.player_id:
                update_player(self.player, sprite_player)

        # update camera
        for sprite_player in self.players:
            if sprite_player.player_id == self.player_id:
                self.camera.update(sprite_player)

        # update display caption with useful information
        pg.display.set_caption(
            f'Client - ID: {self.player_id} - Username: {self.username} - FPS: {round(self.clock.get_fps(), 2)}')

    def draw_grid(self):
        for x in range(self.camera.x, SCREEN_WIDTH, TILESIZE):
            pg.draw.line(self.screen, GRID_COLOR, (x, 0), (x, SCREEN_HEIGHT))
        for y in range(self.camera.y, SCREEN_HEIGHT, TILESIZE):
            pg.draw.line(self.screen, GRID_COLOR, (0, y), (SCREEN_WIDTH, y))

    def draw_debug(self):
        self.draw_grid()
        for sprite in self.all_sprites:
            pg.draw.rect(self.screen, IMAGE_RECT_COLOR, (sprite.rect.x + self.camera.x,
                                                         sprite.rect.y + self.camera.y,
                                                         sprite.rect.width,
                                                         sprite.rect.height), 1)
            pg.draw.rect(self.screen, HIT_RECT_COLOR, (sprite.hit_rect.x + self.camera.x,
                                                       sprite.hit_rect.y + self.camera.y,
                                                       sprite.hit_rect.width,
                                                       sprite.hit_rect.height), 1)

    def game_draw(self):
        # background
        self.screen.fill((255, 255, 255))

        # map image
        self.screen.blit(self.map.image, self.camera.apply_rect(self.map.rect))

        # player images
        # frozen color effect
        for sprite_player in self.players:
            if sprite_player.frozen:
                sprite_player.image.fill((200, 200, 250, 255), special_flags=pg.BLEND_RGBA_MULT)
        # player sprite image and username
        for sprite_player in self.players:
            # blit to screen as done below so that the camera can be applied
            self.screen.blit(sprite_player.image, self.camera.apply_sprite(sprite_player))
            self.draw_text(sprite_player.username, USERNAME_SIZE, sprite_player.fillcolor,
                           sprite_player.pos.x + self.camera.x,
                           sprite_player.hit_rect.top + USERNAME_HEIGHT + self.camera.y,
                           align='s', font_name=self.theme_font)

        # debug information
        if self.debug:
            self.draw_debug()

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


if __name__ == '__main__':
    c = Client()
    c.run()
