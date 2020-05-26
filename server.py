from os import path, listdir
from time import sleep
from random import randint, choice
import socket
from _thread import start_new_thread
from pickle import dumps, loads
import pygame as pg
from pygame.math import Vector2 as Vec
import pytmx
from entities import NetPlayer
from tilemap import format_map
from settings import *


class Server:
    def __init__(self):
        # start pygame
        pg.init()
        self.icon = None
        self.screen = None
        self.window_clock = None
        self.game_clock = None
        self.window_dt = 0.0
        self.game_dt = 0.0
        # start time
        self.server_start_time = pg.time.get_ticks() // 1000.0  # in whole seconds
        self.game_start_time = 0
        self.game_time_left = 0
        self.game_end_time = 0
        self.current_game_end_time = 0
        self.game_end_time_left = 0
        # get machine's information to create a server
        self.server_name = socket.gethostname()
        self.server_ip = socket.gethostbyname(self.server_name)
        self.server_port = PORT
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # server attributes
        self.running = True
        self.open = True
        self.connections = {}  # the connection objects
        self.threaded_clients = {}  # if client id is connected or not
        self.client_id_username = {}  # client id to username finder
        self.client_changes = {}
        self.server_commands = ["help", "listall", "getusername", "getid", "setattr", "setusername", "setcolor",
                                "kick", "kickall", "respawn", "freeze", "unfreeze", "freezeall", "unfreezeall",
                                "setitem", "open", "close"]
        self.current_player = 0  # the current client id
        # game attributes
        self.maps = []
        self.unplayed_maps = []
        self.current_bullet_id = 0
        self.current_game_id = 0
        # create the game
        self.game = {"players": {},
                     "current map": None,
                     "game time": self.game_time_left,
                     "score time": self.game_end_time_left,
                     "items": {},
                     "bullets": {},
                     "active": True
                     }
        # load data
        self.load()

    def load(self):
        # folders
        game_folder = path.dirname(__file__)
        img_folder = path.join(game_folder, "img")
        self.map_folder = path.join(game_folder, "map")

        # server pygame icon
        self.icon = pg.image.load(path.join(img_folder, SERVER_IMG))

        # get all the maps available
        game_folder = path.dirname(__file__)
        map_folder = path.join(game_folder, "map")
        for filename in listdir(map_folder):
            if filename.endswith(".tmx") and filename != MENU_BG_IMG and filename != GAME_BG_IMG:
                self.maps.append(filename)
        # create another list of maps, where random maps will be popped from
        # this will make sure the same maps aren't chosen, but it is still random
        self.unplayed_maps = self.maps.copy()

    def create_socket(self):
        # try to create a server, port must be unused
        try:
            self.socket.bind((self.server_name, self.server_port))
        except socket.error as e:
            print(e)
            print(f"Error Creating A Server On {self.server_name} At {self.server_ip}:{self.server_port}")

    def run(self):
        # start a thread for input
        start_new_thread(self.threaded_input, ())

        # start the game thread
        start_new_thread(self.threaded_game, ())

        # start the accept new connections thread
        start_new_thread(self.threaded_socket, ())

        # start the window
        self.screen = pg.display.set_mode((SERVER_SCREEN_WIDTH, SERVER_SCREEN_HEIGHT))
        pg.display.set_icon(self.icon)
        self.window_clock = pg.time.Clock()

        while self.running:
            # pause
            self.window_dt = self.window_clock.tick(FPS) / 1000.0

            # events
            for event in pg.event.get():
                if event.type == pg.QUIT or event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                    self.end()

            # update
            pg.display.set_caption(
                f"Server - IP: {self.server_ip} - Port: {self.server_port} - Clients: {len(self.connections)}")

            # draw
            self.screen.fill(WHITE)
            pg.display.flip()

        # quit program
        print("Quiting Pygame...")
        pg.quit()
        print("\nProcess Finished")

    def threaded_socket(self):
        # create a socket to host the server
        self.create_socket()

        # have the server socket start listening for client connections
        self.socket.listen()
        print(f"\nServer Started On {self.server_name}:\n\t- IP: {self.server_ip}\n\t- Port: {self.server_port}")
        print("Waiting for a connection...")

        while self.running:
            try:
                conn, addr = self.socket.accept()

                print(f"\nClient {self.current_player} Has Connected From IP: {addr[0]}")

                start_new_thread(self.threaded_client, (conn, self.current_player))
                self.current_player += 1
            except ConnectionAbortedError:
                print("Socket Connection Aborted - Server Closed")

    def end(self):
        print("\nStarting Server Termination")
        # stop all loops
        self.open = False
        self.running = False
        # close down the socket
        print("Closing Server Socket...")
        self.socket.close()

    def new_game(self):
        # set the game to inactive
        self.game['active'] = False

        # a new game is started so changed the id up one
        self.current_game_id += 1

        # get the current time to figure out how long until a new game should start
        self.game_end_time = pg.time.get_ticks()

        # get the game end time
        self.game_end_time = pg.time.get_ticks()

        # start a new game on the server
        print("\nStarting A New Game...")

        # select a new map that hasn"t been played in the current cycle through all the maps
        self.game['current map'] = self.unplayed_maps.pop(randint(0, (len(self.unplayed_maps) - 1)))
        print(f"The Chosen Map Is: {format_map(self.game['current map'])}")

        # reset game data
        self.game['items'].clear()
        self.game['bullets'].clear()
        # counters to give each item spawn and bullet a unique id for their group
        current_item_id = 0
        self.current_bullet_id = 0

        # get data about the current map
        tilemap_data = pytmx.load_pygame(path.join(self.map_folder, self.game['current map']), pixelalpha=True)
        for tile_object in tilemap_data.objects:
            # add each item to a dictionary to keep track if it is active or not
            if tile_object.type == "item":
                self.game['items'][current_item_id] = [True, tile_object.name]
                # choose a random item only if it is a random item spawn
                if tile_object.name == "random":
                    item_name = choice(ITEM_WEIGHTS_LIST)
                    self.game['items'][current_item_id].append(item_name)
                else:
                    self.game['items'][current_item_id].append(tile_object.name)
                current_item_id += 1

        # reset unplayed maps if it is empty
        if len(self.unplayed_maps) == 0:
            self.unplayed_maps = self.maps.copy()
            print("\nAll Maps Have Been Played, Refilled Map Selection With All Maps")

        print(f"\nWaiting {END_GAME_LENGTH / 1000.0} Seconds Until The Game Is Started...")

        # wait until enough time has passed
        self.current_game_end_time = pg.time.get_ticks() - self.game_end_time
        self.game_end_time_left = (END_GAME_LENGTH - self.current_game_end_time) / 1000.0
        self.game['score time'] = self.game_end_time_left
        while self.current_game_end_time < END_GAME_LENGTH:
            sleep(0.5)
            self.current_game_end_time = pg.time.get_ticks() - self.game_end_time
            self.game_end_time_left = (END_GAME_LENGTH - self.current_game_end_time) / 1000.0
            self.game['score time'] = self.game_end_time_left

        self.game_start_time = pg.time.get_ticks()

        # turn the game back on
        self.game['active'] = True

        print("\nThe Game Is Now Active")

    def threaded_item_respawn(self, item_id, game_id):
        # wait until enough time has passed, then set the item's active state back to True
        # the time until the item respawns depends on the item
        # the game_id makes sure this thread doesn't respawn an item from a different game
        # if this function is called right before a game ends, it would sleep through the eng game screen
        if self.game['items'][item_id][1] == "power":
            sleep(SPECIAL_ITEM_RESPAWN_TIME)
        else:
            sleep(NORMAL_ITEM_RESPAWN_TIME)
        if self.current_game_id == game_id:
            # if it is a random item spawn, choose the random item that will spawn
            if self.game['items'][item_id][1] == "random":
                item_name = choice(ITEM_WEIGHTS_LIST)
                self.game['items'][item_id][2] = item_name
                self.game['items'][item_id][0] = True
            else:
                self.game['items'][item_id][0] = True

    def threaded_game(self):
        # setup
        self.game_clock = pg.time.Clock()
        # start a new game
        self.new_game()
        # start the game timer
        while self.running:
            # pause
            self.game_dt = self.game_clock.tick(FPS) / 1000.0

            # update
            # move bullets
            for bullet_id, bullet_data in self.game['bullets'].items():
                angle = self.game['bullets'][bullet_id][1]
                self.game['bullets'][bullet_id][0] += Vec(BULLET_VEL, 0).rotate(-angle) * self.game_dt

            # current game times
            time_since_game_start = (pg.time.get_ticks() - self.game_start_time) // 1000.0  # in whole seconds
            self.game_time_left = GAME_LENGTH - time_since_game_start
            self.game['game time'] = self.game_time_left

            # reset the game after enough time has passed
            if time_since_game_start > GAME_LENGTH:
                # end current game and start a new game
                self.new_game()

    def verify_id_command(self, min_length, command):
        if len(command) >= min_length:
            # execute by player ID
            if command[1].isdigit():
                player_id = int(command[1])
                # if the player id is connected
                if player_id in self.threaded_clients and self.threaded_clients[player_id]:
                    return True
                else:
                    print(f"Command Error: No Client Is Connected With The ID {player_id}")
                    return False
            else:
                print("Command Error: Please Specify A Player ID Connected To The Server")
                return False
        else:
            print(f"Command Error: Requires At Least {min_length} Arguments")
            return False

    def verify_name_command(self, min_length, command):
        if len(command) >= min_length:
            # find player username by id
            username = " ".join(command[min_length - 1:])
            if username in self.client_id_username:
                return True
            else:
                print(f"Command Error: No Client Connected With The Username {username}")
                return False
        else:
            print(f"Command Error: Requires At Least {min_length} Arguments")
            return False

    def threaded_input(self):
        while self.running:
            # split the text command received into words
            command = input().split()
            # only execute a command if
            if command:

                # show a list of valid commands
                # syntax: help
                if command[0] == "help":
                    print("Valid Commands Are As Follows:")
                    for command in self.server_commands:
                        print(f"\t- {command}")

                # list all player ids and their respective usernames connected to the server
                # syntax: listall
                elif command[0] == "listall":
                    if len(self.game['players']) > 0:
                        print("All Players Connected Are As Follows:")
                        for player_id, username in self.client_id_username.items():
                            if type(player_id) is int:
                                print(f"\t- ID: {player_id} - Username: {username}")
                    else:
                        print("Command Error: There Are No Clients Currently Connected To The Server")

                # get a player username by id
                # syntax: getusername <player_id>
                elif command[0] == "getusername":
                    if self.verify_id_command(2, command):
                        player_id = int(command[1])
                        print(
                            f"Client ID {player_id} Has The Username {self.client_id_username[player_id]}")

                # get a player id by username
                # syntax: getid <player_username>
                elif command[0] == "getid":
                    if self.verify_name_command(2, command):
                        username = " ".join(command[1:])
                        player_id = self.client_id_username[username]
                        print(f"Client With The Username {username} Has The ID {player_id}")

                # change the username of a client
                # syntax: setusername <client_id> <new_player_username>
                elif command[0] == "setusername":
                    if self.verify_id_command(2, command):
                        player_id = int(command[1])
                        new_username = " ".join(command[2:])

                        self.overwrite_player_data(player_id, "username", new_username)
                        print(f"Changed The Username Of Client ID {player_id} To {new_username}")

                # change the username color of a client
                elif command[0] == "setcolor":
                    pass
                    #if self.verify_id_command()

                # kick a client from the server
                # syntax: kick <client_id>
                elif command[0] == "kick":
                    if self.verify_id_command(2, command):
                        player_id = int(command[1])
                        self.threaded_clients[player_id] = False
                        print(f"Kicked Client {player_id}")

                # kick all current players from the server
                # syntax: kickall
                elif command[0] == "kickall":
                    if len(self.game['players']) > 0:
                        print(f"All {len(self.game['players'])} Clients Have Been Kicked From The Server")
                        for player_id in self.game['players']:
                            self.threaded_clients[player_id] = False
                    else:
                        print("Command Error: There Are No Clients Currently Connected To The Server")

                # change a player"s position to be the spawn location
                # syntax: respawn <client_id>
                elif command[0] == "respawn":
                    if self.verify_id_command(2, command):
                        player_id = int(command[1])
                        self.overwrite_player_data(player_id, "respawn", True)
                        print(f"Respawned The Player With Client ID {player_id}")

                # stop a player from moving
                # syntax: freeze <client_id>
                elif command[0] == "freeze":
                    if self.verify_id_command(2, command):
                        player_id = int(command[1])
                        self.overwrite_player_data(player_id, "frozen", True)
                        print(f"Player {player_id} Has Been Frozen")

                # allow a player to move again
                # syntax: unfreeze <client_id>
                elif command[0] == "unfreeze":
                    if self.verify_id_command(2, command):
                        player_id = int(command[1])
                        self.overwrite_player_data(player_id, "frozen", False)
                        print(f"Player {player_id} Has Been Unfrozen")

                # freeze all players
                # syntax: freezeall
                elif command[0] == "freezeall":
                    for player_id in self.game['players']:
                        self.overwrite_player_data(player_id, "frozen", True)
                    print("All Players Have Been Frozen")

                # unfreeze all players
                # syntax: unfreezeall
                elif command[0] == "unfreezeall":
                    for player_id in self.game['players']:
                        self.overwrite_player_data(player_id, "frozen", False)
                    print("All Players Have Been Unfrozen")

                # set an item to either be active (True) or inactive (False)
                # syntax: setitem <item_id> <status>
                elif command[0] == "setitem":
                    item_id = command[1]
                    # if the item id passed in is an integer
                    if item_id.isdigit():
                        item_id = int(item_id)
                        # if the item id exisits
                        if item_id in self.game['items']:
                            if command[2] == "True" or command[2] == "False":
                                if command[2] == "True":
                                    # make the item active
                                    self.game['items'][item_id][0] = True
                                    print(f"The Item With ID {item_id} Is Now Active")
                                else:
                                    # make the item inactive
                                    self.game['items'][item_id][0] = False
                                    start_new_thread(self.threaded_item_respawn, (item_id, self.current_game_id))
                                    print(f"The Item With ID {item_id} Is Now Inactive")
                            else:
                                print("You Must Pass In \"True\" or \"False\" After The Item ID To Set The State")
                        else:
                            print("Item ID Not Found, "
                                  f"Item IDs On The Current Map Go From 0-{(len(self.game['items']) - 1)}")
                    else:
                        print("Item IDs Must Be An Integer")

                # open the server to new client connections
                # syntax: open
                elif command[0] == "open":
                    if self.open:
                        print("Server Is Already Open")
                    else:
                        self.open = True
                        print("Server Will Now Open")

                # close the server to new client connections
                # syntax: close
                elif command[0] == "close":
                    if not self.open:
                        print("Server Is Already Closed")
                    else:
                        self.open = False
                        print("Server Will Now Close")

                # end the program
                # syntax: end
                elif command[0] == "end":
                    self.end()

                else:
                    print("Command Error: Not A Valid Command, Do help For A List Of Valid Commands")

            else:
                print("Command Error: No Command Was Given")

    def overwrite_player_data(self, player_id, attribute, new_value, overwrite_method="replace"):
        # replace the existing attribute value with the provided value
        if overwrite_method == "replace":
            if attribute == "username":
                # update stored data to match the new data if a username switch happened
                self.client_id_username[player_id] = new_value
                self.client_id_username[new_value] = player_id
        # add the provided value to the existing attribute value
        elif overwrite_method == "add":
            old_value = getattr(self.game['players'][player_id], attribute)
            new_value = old_value + new_value

        # ensure the server will not ignore this change by accepting what the client sends
        self.client_changes[player_id][attribute] = [True, new_value]

    def threaded_client(self, connection, player_id):
        # save the connection to the server
        self.connections[player_id] = connection
        # client is connected
        self.threaded_clients[player_id] = True

        # create a new player and send it to the new client
        # the new player is not added to the players dictionary of the game until (and if) they are verified
        new_player = NetPlayer(player_id)
        connection.send(dumps(new_player))

        # send verification to client
        verify, reason, player_data = self.verify_client(connection)
        connection.sendall(dumps((verify, reason)))

        if verify:
            # add the verified player to the dictionary of players for the game
            self.game['players'][player_id] = player_data

            # update total player count
            self.count_players()

            # update the client id to username finder
            self.client_id_username[player_id] = self.game['players'][player_id].username
            self.client_id_username[self.game['players'][player_id].username] = player_id

            # reset overwrite data for this client
            self.client_changes[player_id] = {}
            player = self.game['players'][player_id]
            for attr in player.__dict__.items():
                # attr[0] is the attribute, attr[1] is the attributes value
                self.client_changes[player_id][attr[0]] = [False, None]

            # this loop will only end when this client disconnects or the server disconnects this client
            while self.threaded_clients[player_id]:
                try:
                    # receive data for the client's player
                    data = loads(connection.recv(RECEIVE_LIMIT))

                    # the players that should be destroyed
                    for overwrite_type, overwrite_data in data.overwrites.items():
                        # only overwrite data if the client has data that needs overwriting
                        if overwrite_data:
                            # the client player collided with another player that now has to be destroyed
                            if overwrite_type == "collisions":
                                for collision_player_id in overwrite_data:
                                    collision_player = self.game['players'][collision_player_id]
                                    if collision_player.respawn is False and collision_player.current_respawn_time is False and collision_player.current_crash_time is False:
                                        self.overwrite_player_data(collision_player_id, "destroy", (True, player_id))
                            # the player picked up an item
                            if overwrite_type == "items":
                                for item_id in overwrite_data:
                                    self.game['items'][item_id][0] = False
                                    start_new_thread(self.threaded_item_respawn, (item_id, self.current_game_id))
                            # the player launched a bullet
                            elif overwrite_type == "new bullets":
                                for new_bullet in overwrite_data:
                                    self.game['bullets'][self.current_bullet_id] = new_bullet
                                    self.current_bullet_id += 1
                            # the player launched a bullet
                            elif overwrite_type == "kill bullets":
                                for kill_bullet_id in overwrite_data:
                                    if kill_bullet_id in self.game['bullets'].keys():
                                        del self.game['bullets'][kill_bullet_id]
                            # this client's player was killed by another client's player
                            elif overwrite_type == "deaths by":
                                for killed_by_player_id in overwrite_data:
                                    self.overwrite_player_data(player_id, "deaths", 1, "add")
                                    self.overwrite_player_data(killed_by_player_id, "kills", 1, "add")
                                    self.overwrite_player_data(killed_by_player_id, "score", 100, "add")
                                    print(f"\nPlayer ID {player_id} Was Killed By Player ID {killed_by_player_id}")
                            # clear the data so on the next loop this data isn't overwritten again
                            overwrite_data.clear()

                    # update the client id to username finder
                    self.client_id_username[player_id] = self.game['players'][player_id].username
                    self.client_id_username[self.game['players'][player_id].username] = player_id

                    # update the client's player data
                    # only do this if the game is currently active
                    self.game['players'][player_id] = data

                    # override the client's player data changed by the server
                    for attr, value in self.client_changes[player_id].items():
                        if value[0]:
                            # overwrite the changes made by the client to the player data
                            setattr(self.game['players'][player_id], attr, value[1])
                    # reset overwrite data for this client
                    self.client_changes[player_id] = {}
                    player = self.game['players'][player_id]
                    for attr in player.__dict__.items():
                        # attr[0] is the attribute, attr[1] is the attribute's value
                        self.client_changes[player_id][attr[0]] = [False, None]

                    # send game data to the client if they are connected
                    if not data:
                        break
                    else:
                        reply = self.game
                        connection.sendall(dumps(reply))
                except EOFError:
                    break

            # close the connection with the client that has disconnected
            self.disconnect_client(player_id)

        else:
            # disconnect the unverified client
            print(f"Client {player_id} Denied Access:", reason)

            self.disconnect_client(player_id)

    def count_players(self):
        print(f"There Are {len(self.game['players'])}/{MAX_CLIENTS} Clients Connected")

    def verify_client(self, connection):
        # verify client has a unique username and the server has room
        player_data = loads(connection.recv(RECEIVE_LIMIT))
        verify = True
        reason = None
        if not bool(player_data.username):
            verify = False
            reason = f"Please Enter A Username"
        for player in self.game['players'].values():
            # use .lower() to ensure there are no duplicate usernames by case
            if player.username == player_data.username.lower():
                verify = False
                reason = f"Username Is Already Taken ({player_data.username})"
        if len(self.game['players']) > MAX_CLIENTS:
            verify = False
            reason = f"Too Many Clients Connected To Server ({len(self.game['players']) - 1}/{MAX_CLIENTS})"
        if not self.open:
            verify = False
            reason = "The Server Is Currently Not Accepting New Connections"
        return verify, reason, player_data

    def disconnect_client(self, player_id):
        # close the connection with the client
        self.connections[player_id].close()

        try:
            # remove the player from the id to username finder
            del self.client_id_username[player_id]
            del self.client_id_username[self.game['players'][player_id].username]
            # remove the unverified player from the player dictionary
            del self.game['players'][player_id]

            # client disconnected server message
            print(f"\nClient {player_id} Has Disconnected")
            # update total player count
            self.count_players()
        except KeyError:
            # the client was never verified (clients are only added to client_id_username and game data if verified)
            print(f"Client {player_id} Has Been Forcefully Disconnected By The Server")

        # remove the player from the connections list
        self.threaded_clients[player_id] = False
        # remove the disconnected client from the connections dictionary
        del self.connections[player_id]


if __name__ == "__main__":
    s = Server()
    s.run()
