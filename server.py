import socket
from _thread import start_new_thread
from pickle import dumps, loads
import pygame as pg
from pygame.math import Vector2 as Vec
from entities import NetPlayer
from settings import *


class Server:
    def __init__(self):
        # get machine's information to create a server
        self.server_name = socket.gethostname()
        self.server_ip = socket.gethostbyname(self.server_name)
        self.server_port = PORT
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # server attributes
        self.open = False
        self.connections = {}
        self.threaded_clients = {}  # if client id is connected or not
        self.client_id_username = {}  # client id to username finder
        self.client_changes = {}
        self.server_commands = ['help', 'listall', 'kickall',
                                'getusername', 'getid', 'kick',
                                'setusername', 'respawn', 'freeze',
                                'unfreeze', 'freezeall', 'unfreezeall']
        # game attributes
        self.clock = None
        self.maps = ['map1.tmx']
        # create the game
        self.game = {'current player': 0,
                     'players': {},
                     'current map': self.maps[0],
                     }
        # create a socket to host the server
        self.create_socket()

    def create_socket(self):
        # try to create a server, port must be unused
        try:
            self.socket.bind((self.server_name, self.server_port))
        except socket.error as e:
            print(e)
            print(f'Error Creating A Server On {self.server_name} At {self.server_ip}:{self.server_port}')

    def open_socket(self):
        # open the server
        self.socket.listen()
        self.open = True
        print(f'Server Started On {self.server_name}:\n\t- IP: {self.server_ip}\n\t- Port: {self.server_port}')
        print('Waiting for a connection...')

        # start the game thread
        start_new_thread(self.threaded_game, ())

        # start a thread for input
        start_new_thread(self.threaded_input, ())

        while self.open:
            conn, addr = self.socket.accept()

            print(f'\nClient {self.game["current player"]} Has Connected From IP: {addr[0]}')

            start_new_thread(self.threaded_client, (conn, self.game['current player']))
            self.game['current player'] += 1

    def threaded_game(self):
        while self.open:
            # any game data for the server to keep track of
            self.clock = pg.time.Clock()
            self.clock.tick(FPS)

    def verify_id_command(self, min_length, command):
        if len(command) >= min_length:
            # execute by player ID
            if command[1].isdigit():
                player_id = int(command[1])
                # if the player id is connected
                if player_id in self.threaded_clients and self.threaded_clients[player_id]:
                    return True
                else:
                    print(f'Command Error: No Client Is Connected With The ID {player_id}')
                    return False
            else:
                print('Command Error: Please Specify A Player ID Connected To The Server')
                return False
        else:
            print(f'Command Error: Requires At Least {min_length} Arguments')
            return False

    def verify_name_command(self, min_length, command):
        if len(command) >= min_length:
            # find player username by id
            username = ' '.join(command[min_length - 1:])
            if username in self.client_id_username:
                return True
            else:
                print(f'Command Error: No Client Connected With The Username {username}')
                return False
        else:
            print(f'Command Error: Requires At Least {min_length} Arguments')
            return False

    def threaded_input(self):
        while self.open:
            # split the text command received into words
            command = input().split()
            # only execute a command if
            if command:

                # show a list of valid commands
                # syntax: help
                if command[0] == 'help':
                    print('Valid Commands Are As Follows:')
                    for command in self.server_commands:
                        print(f'\t- {command}')

                # list all player ids and their respective usernames connected to the server
                # syntax: listall
                elif command[0] == 'listall':
                    if len(self.game['players']) > 0:
                        print('All Players Connected Are As Follows:')
                        for player_id, username in self.client_id_username.items():
                            if type(player_id) is int:
                                print(f'\t- ID: {player_id} - Username: {username}')
                    else:
                        print('Command Error: There Are No Clients Currently Connected To The Server')

                # kick all current players from the server
                # syntax: kickall
                elif command[0] == 'kickall':
                    if len(self.game['players']) > 0:
                        print(f'All {len(self.game["players"])} Clients Have Been Kicked From The Server')
                        for player_id in self.game['players']:
                            self.threaded_clients[player_id] = False
                    else:
                        print('Command Error: There Are No Clients Currently Connected To The Server')

                # get a player username by id
                # syntax: getusername <player_id>
                elif command[0] == 'getusername':
                    if self.verify_id_command(2, command):
                        player_id = int(command[1])
                        print(
                            f'Client ID {player_id} Has The Username {self.client_id_username[player_id]}')

                # get a player id by username
                # syntax: getid <player_username>
                elif command[0] == 'getid':
                    if self.verify_name_command(2, command):
                        username = ' '.join(command[1:])
                        player_id = self.client_id_username[username]
                        print(f'Client With The Username {username} Has The ID {player_id}')

                # kick a client from the server
                # syntax: kick <client_id>
                elif command[0] == 'kick':
                    if self.verify_id_command(2, command):
                        player_id = int(command[1])
                        self.threaded_clients[player_id] = False
                        print(f'Kicked Client {player_id}')

                # change the username of a client
                # syntax: setusername <client_id> <new_player_username>
                elif command[0] == 'setusername':
                    if self.verify_id_command(2, command):
                        player_id = int(command[1])
                        new_username = ' '.join(command[2:])

                        self.overwrite_player_data(player_id, 'username', new_username)
                        print(f'Changed The Username Of Client ID {player_id} To {new_username}')

                # change a player's position to be the spawn location
                # syntax: respawn <client_id>
                elif command[0] == 'respawn':
                    if self.verify_id_command(2, command):
                        player_id = int(command[1])
                        new_pos = Vec(PLAYER_SPAWN_X, PLAYER_SPAWN_Y)
                        self.overwrite_player_data(player_id, 'pos', new_pos)

                # stop a player from moving
                # syntax: freeze <client_id>
                elif command[0] == 'freeze':
                    if self.verify_id_command(2, command):
                        player_id = int(command[1])
                        self.overwrite_player_data(player_id, 'frozen', True)
                        print(f'Player {player_id} Has Been Frozen')

                # allow a player to move again
                # syntax: unfreeze <client_id>
                elif command[0] == 'unfreeze':
                    if self.verify_id_command(2, command):
                        player_id = int(command[1])
                        self.overwrite_player_data(player_id, 'frozen', False)
                        print(f'Player {player_id} Has Been Unfrozen')

                # freeze all players
                # syntax: freezeall
                elif command[0] == 'freezeall':
                    for player_id in self.game['players']:
                        self.overwrite_player_data(player_id, 'frozen', True)
                    print('All Players Have Been Frozen')

                # unfreeze all players
                # syntax: unfreezeall
                elif command[0] == 'unfreezeall':
                    for player_id in self.game['players']:
                        self.overwrite_player_data(player_id, 'frozen', False)
                    print('All Players Have Been Unfrozen')

                else:
                    print('Command Error: Not A Valid Command, Do help For A List Of Valid Commands')

            else:
                print('Command Error: No Command Was Given')

    def overwrite_player_data(self, player_id, attribute, new_value):
        # change data that will be sent over the network
        setattr(self.game['players'][player_id], attribute, new_value)

        if attribute == 'username':
            # update stored data to match the new data if a username switch happened
            self.client_id_username[player_id] = new_value
            self.client_id_username[new_value] = player_id

        # ensure the server will not ignore this change by accepting what the client sends
        self.client_changes[player_id][attribute] = [True, new_value]

    def threaded_client(self, connection, player_id):
        # save the connection to the server
        self.connections[player_id] = connection

        # create a new player and send it to the new client
        self.game['players'][player_id] = NetPlayer(player_id, PLAYER_SPAWN_X, PLAYER_SPAWN_Y)
        connection.send(dumps(self.game['players'][player_id]))

        # update total player count
        self.count_players()

        # send verification to client
        verify, reason, username = self.verify_client(connection)
        connection.sendall(dumps((verify, reason)))

        # client is connected
        self.threaded_clients[player_id] = True

        # update the client id to username finder
        self.client_id_username[player_id] = self.game['players'][player_id].username
        self.client_id_username[self.game['players'][player_id].username] = player_id

        if verify:

            # register username
            self.game['players'][player_id].username = username

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

                    # update the client id to username finder
                    self.client_id_username[player_id] = self.game['players'][player_id].username
                    self.client_id_username[self.game['players'][player_id].username] = player_id

                    # update the client's player data
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
            print(f'Client {player_id} Denied Access:', reason)

            self.disconnect_client(player_id)

    def count_players(self):
        print(f'There Are {len(self.game["players"])}/{MAX_CLIENTS} Clients Connected')

    def verify_client(self, connection):
        # verify client has a unique username and the server has room
        data = loads(connection.recv(RECEIVE_LIMIT))
        verify = True
        reason = None
        for player in self.game['players'].values():
            # use .lower() to ensure there are no duplicate usernames by case
            if player.username == data.username.lower():
                verify = False
                reason = f'Username Is Already Taken ({data.username})'
        if len(self.game['players']) > MAX_CLIENTS:
            verify = False
            reason = f'Too Many Clients Connected To Server ({len(self.game["players"]) - 1}/{MAX_CLIENTS})'
        return verify, reason, data.username

    def disconnect_client(self, player_id):
        # server message
        print(f'\nClient {player_id} Has Disconnected')

        # close the connection with the client
        self.connections[player_id].close()

        # remove the player from the id to username finder
        del self.client_id_username[player_id]
        del self.client_id_username[self.game['players'][player_id].username]

        # remove the player from the connections list
        self.threaded_clients[player_id] = False

        # remove the unverified player from the player dictionary
        del self.game['players'][player_id]
        # remove the disconnected client from the connections dictionary
        del self.connections[player_id]

        # update total player count
        self.count_players()


s = Server()
s.open_socket()
