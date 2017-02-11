#!/usr/bin/env python
from socketIO_client import SocketIO, LoggingNamespace
import threading

def patch(old, diff):
    out = []
    i = 0
    while i < len(diff):
        if diff[i] > 0:
            out.extend(old[len(out):len(out) + diff[i]])
        i = i + 1
        if i < len(diff) and diff[i] > 0:
            out.extend(diff[i+1:i+1+diff[i]])
            i = i + diff[i]
        i = i + 1
    return out

class GeneralsClient:
    TILE_EMPTY = -1
    TILE_MOUNTAIN = -2
    TILE_FOG = -3
    TILE_FOG = -4

    GAME_TYPE_FFA = "play"
    GAME_TYPE_1V1 = "join_1v1"
    GAME_TYPE_PRIVATE = "join_private"
    GAME_TYPE_2V2 = "join_team"

    def __init__(self, address, port):
        self._init_fields()
        self._init_socket(address, port)

    def connect(self):
        self._stay_connected = True
        def run(*args):
            while self._stay_connected:
                self.socket.wait(1)
        self._socket_connection_thread = threading.Thread(target=run)
        self._socket_connection_thread.start()

    def disconnect(self):
        self._stay_connected = False
        self._socket_connection_thread.join()
        self.in_game = False
        self.in_game_queue = False
        self.connected = False

    def join(self, user_id, username, game_type, private_game_id=None, team_id=None):
        if not self.connected:
            raise Exception("No active connection to server")
        if self.in_game or self.in_game_queue:
            raise Exception("Already in a game or waiting for a game")
        self.socket.emit("set_username", user_id, username)
        self._join_game_queue(user_id, game_type, private_game_id, team_id)
        self.socket.emit("set_force_start", self._get_queue_id(game_type, private_game_id), True)
        self.in_game_queue = True

    def attack(self, start, end, is50 = None):
        self.socket.emit("attack", start, end, is50)

    def clear_moves(self):
        self.socket.emit("clear_moves")

    def register_listener(self, listener):
        self._listeners.append(listener)

    def _init_fields(self):
        self.in_game = False
        self.in_game_queue = False
        self.connected = False

        self.cur_game = -1
        self.replay_ids = []
        self.results = []

        self.cur_tile = None
        self.home = None
        self.cities = []
        self.map = []

        self._listeners = []

    def _init_socket(self, address, port):
        self.socket = SocketIO(address, port, LoggingNamespace)
        self.socket.on("connect", self._on_connect)
        self.socket.on("disconnect", self._on_disconnect)
        self.socket.on("game_start", self._on_game_start)
        self.socket.on("game_update", self._on_game_update)
        self.socket.on("game_lost", self._on_game_lost)
        self.socket.on("game_won", self._on_game_won)

    def _on_connect(self):
        self.connected = True

    def _on_disconnect(self):
        self.disconnect()

    def _on_game_start(self, *args):
        self.in_game = True
        self.in_game_queue = False
        self._load_game_start_data(args)

    def _load_game_start_data(self, args):
        data = args[0]
        self.cur_game = self.cur_game + 1
        self.player_index = data["playerIndex"]
        self.replay_ids.append(data["replay_id"])
        self.chat_room_key = data["chat_room"]
        if "team_chat_room" in data:
            self.team_chat_room_key = data["team_chat_room"]
        else:
            self.team_chat_room_key = None
        self.usernames = data["usernames"]
        if "teams" in data:
            self.teams = data["teams"]
        else:
            self.teams = None

    def _on_game_update(self, *args):
        self._load_game_update(args)
        self._generate_computed_fields()
        self._notify_listeners()

    def _on_game_lost(self, *args):
        self.results.append({
            "victory": False,
            "killer": args[0]["killer"]
        })

        self.socket.emit("leave_game")
        self.in_game = False

    def _on_game_won(self, *args):
        self.results.append({
            "victory": True
        })

        self.socket.emit("leave_game")
        self.in_game = False

    def _load_game_update(self, args):
        data = args[0]
        self.turn = data["turn"]
        self.map = patch(self.map, data["map_diff"])
        self.cities = patch(self.cities, data["cities_diff"])
        self.generals = data["generals"]
        self.scores = data["scores"]

    def _generate_computed_fields(self):
        self.map_width = self.map[0]
        self.map_height = self.map[1]
        self.map_size = self.map_width * self.map_height

        self.armies = self.map[2:self.map_size+1]
        self.terrain = self.map[self.map_size+2:len(self.map)-1]

    def _notify_listeners(self):
        for listener in self._listeners:
            threading.Thread(target=listener).start()

    def _join_game_queue(self, user_id, game_type, private_game_id, team_id):
        if game_type == self.GAME_TYPE_FFA or game_type == self.GAME_TYPE_1V1:
            self.socket.emit(game_type, user_id)
        elif game_type == self.GAME_TYPE_PRIVATE:
            self.socket.emit(game_type, private_game_id, user_id)
        elif game_type == self.GAME_TYPE_2V2:
            self.socket.emit(game_type, team_id, user_id)
        else:
            raise Exception("Unknown game type {}".format(game_type))

    def _get_queue_id(self, game_type, private_game_id = None):
        if game_type == self.GAME_TYPE_FFA:
            return None
        if game_type == self.GAME_TYPE_1V1:
            return "1v1"
        if game_type == self.GAME_TYPE_2V2:
            return "2v2"
        if game_type == self.GAME_TYPE_PRIVATE:
            return private_game_id
        raise Exception("Unknown game_type {}".format(game_type))
