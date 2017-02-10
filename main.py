#!/usr/bin/env python
from socketIO_client import SocketIO, LoggingNamespace
import threading
import time
import json

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
    TILE_FOG_OBSTACLE = -4

    def __init__(self, address, port):
        self.cities = []
        self.map = []
        self.socket = SocketIO(address, port, LoggingNamespace)
        self.socket.on("connect", self.on_connect)
        self.socket.on("reconnect", self.on_reconnect)
        self.socket.on("disconnect", self.on_disconnect)
        self.socket.on("game_start", self.on_game_start)
        self.socket.on("game_update", self.on_game_update)
        self.listen = True
        def run(*args):
            while self.listen:
                self.socket.wait(1)
        self.listenThread = threading.Thread(target=run)
        self.listenThread.start()

    def disconnect(self):
        self.listen = False
        self.listenThread.join()

    def join(self, user_id, username, private_game_id):
        self.socket.emit("set_username", user_id, username)
        self.socket.emit("join_private", private_game_id, user_id)
        self.socket.emit("set_force_start", private_game_id, True)
        print("Joined custom game at http://bot.generals.io/games/{}".format(private_game_id))

    def on_game_update(self, *args):
        print("hello world")

    def on_game_start(self, *args):
        self.playerIndex = args[0]["playerIndex"]
        replay_url = "http://bot.generals.io/replays/{}".format(args[0]["replay_id"])
        print("Game starting! The replay will be available after the game at {}".format(replay_url))

    def on_connect(self):
        print("Connected to server!")

    def on_disconnect(self):
        print("Disconnected from server!")

    def on_reconnect(self):
        print("Reconnected to server!")

def main():
    g = GeneralsClient("botws.generals.io", 80)
    g.join("thisbotwillruletheworld", "jseely-bot", private_game_id="customgameid6743")
    input()
    g.disconnect()

if __name__ == "__main__":
    main()
