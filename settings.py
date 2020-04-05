# server settings
SERVER_IP = "192.168.86.60"
PORT = 4242
RECEIVE_LIMIT = 2048
MAX_CLIENTS = 10
CONN_TIMEOUT = 5  # in seconds

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
# other colors
INACTIVE_BLUE = (0, 179, 255)
ACTIVE_BLUE = (126, 213, 255)
PRESSED_BLUE = (148, 224, 255)

# display settings
GAME_TITLE = "Get Shipped"
FPS = 60
SCREEN_WIDTH = 1440
SCREEN_HEIGHT = 900
MENU_BG_IMG = "menubg.tmx"
ICON_IMG = "watertile.png"

# debug settings
HIT_RECT_COLOR = RED
IMAGE_RECT_COLOR = GREEN
TILESIZE = 64
GRID_COLOR = DARK_GRAY

# font settings
TEXT_COLOR = (0, 83, 92)
TITLE_SIZE = 150
USERNAME_SIZE = 40
USERNAME_HEIGHT = -15
ENTRY_SIZE = 35
BUTTON_SIZE = 50
THEME_FONT = "Booter.ttf"

# entry box settings
VALID_USERNAME = "AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz1234567890_-. "
VALID_IP = "1234567890."
VALID_PORT = "1234567890"
ENTRY_INACTIVE_COLOR = INACTIVE_BLUE
ENTRY_ACTIVE_COLOR = ACTIVE_BLUE
ENTRY_WIDTH = 330
ENTRY_TEXT_OFFSET = 5
REPEAT_PAUSE = 350
REPEAT_RATE = 50
# button settings
BUTTON_INACTIVE = INACTIVE_BLUE
BUTTON_ACTIVE = ACTIVE_BLUE
BUTTON_PRESSED = PRESSED_BLUE
BUTTON_WIDTH = 190
BUTTON_HEIGHT = 80

# player settings
PLAYER_ACC = 2
PLAYER_FRICTION = -0.01
PLAYER_SPAWN_X = 700
PLAYER_SPAWN_Y = 300
PLAYER_IMGS = ["shipblue.png", "shipyellow.png"]
PLAYER_HIT_RECT_WIDTH = 66
PLAYER_HIT_RECT_HEIGHT = 66
PLAYER_ROT_ACC = 3
PLAYER_ROT_FRICTION = -0.01

# sound
MENU_BG_MUSIC = "Dryads Feast.mp3"
GAME_BG_MUSIC = "Blackmoor Tides Chant.wav"

# game settings
WINDX = 0
WINDY = 0
