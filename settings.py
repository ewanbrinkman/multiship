# launch options
SOUND = False  # you can still toggle sound after starting
CONN_TIMEOUT = 3  # in seconds

# server
SERVER_IP = "192.168.1.175"
PORT = 4242
RECEIVE_LIMIT = 8192
MAX_CLIENTS = 8

# game
GAME_LENGTH = 20  # in seconds, 300 seconds = 5 minutes

# shades
WHITE = (255, 255, 255)
DARK_GRAY = (40, 40, 40)
BLACK = (0, 0, 0)
# base colors
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
# other color
ORANGE = (255, 140, 0)
PINK = (255, 204, 255)
# button colors
INACTIVE_BLUE = (0, 179, 255)
ACTIVE_BLUE = (126, 213, 255)
PRESSED_BLUE = (196, 238, 255)

# display
GAME_TITLE = "Multiship"
MAIN_MENU_TEXT = "Please Enter A Username By Clicking The First Entry Box"
FPS = 60
SCREEN_WIDTH = 1440
SCREEN_HEIGHT = 900
SERVER_SCREEN_WIDTH = 600
SERVER_SCREEN_HEIGHT = 450
MENU_BG_IMG = "menubg.tmx"
CLIENT_IMG = "watertile.png"
SERVER_IMG = "console.png"
# font
TEXT_COLOR = (0, 83, 92)
TITLE_SIZE = 150
NORMAL_SIZE = 50
USERNAME_SIZE = 40
USERNAME_HEIGHT = -15
ENTRY_SIZE = 35
BUTTON_SIZE = 50
OVERLAY_SIZE = 40
OVERLAY_WIDTH_DISTANCE = 20
OVERLAY_HEIGHT_DISTANCE = 20
THEME_FONT = "Booter.ttf"
# debug
PLAYER_COLOR = CYAN
OBSTACLE_COLOR = RED
SHALLOWS_COLOR = PINK
PLAYER_SPAWN_COLOR = MAGENTA
ITEM_SPAWN_COLOR = YELLOW
TILESIZE = 64
GRID_COLOR = DARK_GRAY
# layers
ITEM_LAYER = 1
PLAYER_LAYER = 2

# entry boxes
VALID_USERNAME = "AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz1234567890_-. "
VALID_IP = "1234567890."
VALID_PORT = "1234567890"
ENTRY_INACTIVE_COLOR = INACTIVE_BLUE
ENTRY_ACTIVE_COLOR = ACTIVE_BLUE
ENTRY_WIDTH = 330
ENTRY_TEXT_OFFSET = 5
REPEAT_PAUSE = 350
REPEAT_RATE = 50
# buttons
BUTTON_INACTIVE = INACTIVE_BLUE
BUTTON_ACTIVE = ACTIVE_BLUE
BUTTON_PRESSED = PRESSED_BLUE
BUTTON_WIDTH = 190
BUTTON_HEIGHT = 80

# player
# north, west, east, and south movement
PLAYER_ACC = 100
PLAYER_WATER_FRICTION = -0.5
PLAYER_SHALLOW_FRICTION = -3
# rotation movement
PLAYER_ROT_ACC = 100
PLAYER_WATER_ROT_FRICTION = -0.5
PLAYER_SHALLOW_ROT_FRICTION = -3
# images
PLAYER_IMGS_CYCLE = ["blue", "green", "yellow", "red"]
PLAYER_IMGS = {
    "basic": "shipbasic.png",
    "red": "shipred.png",
    "yellow": "shipyellow.png",
    "green": "shipgreen.png",
    "blue": "shipblue.png",
    "brokenred": "brokenred.png",
    "brokenyellow": "brokenyellow.png",
    "brokengreen": "brokengreen.png",
    "brokenblue": "brokenblue.png",
}
# hit rect
PLAYER_HIT_RECT_WIDTH = 66
PLAYER_HIT_RECT_HEIGHT = 66
PLAYER_BOUNCE_VEL = 25
PLAYER_CRASH_DURATION = 3000  # in milliseconds
# power invincibility
POWER_INVINCIBLE_DURATION = 12500  # in milliseconds
# respawn invincibility
TRANSITION_SPEED = 10
RESPAWN_ALPHA = [i for i in range(0, 255, TRANSITION_SPEED)]
RESPAWN_INVINCIBLE_DURATION = 3000  # in milliseconds

# items
ITEM_IMGS = {
    "power": "power.png"
}
BOB_RANGE = 15
BOB_SPEED = 0.4
NORMAL_ITEM_RESPAWN_TIME = 10  # in seconds
SPECIAL_ITEM_RESPAWN_TIME = 60  # in seconds

# cannonballs
CANNONBALL_VEL = 100

# sounds
MENU_BG_MUSIC = "Dryads Feast.mp3"
GAME_BG_MUSIC = "Blackmoor Tides Chant.wav"
