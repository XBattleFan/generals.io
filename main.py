#!/usr/bin/env python
import math
import random
from socketIO_client import SocketIO, LoggingNamespace
import threading
import time
import json

from generals_client import GeneralsClient

def main():
    g = GeneralsClient("botws.generals.io", 80)
    
    g.i = 0
    g.home = None
    def process_update(*args):
        if g.home == None:
            g.home = g.generals[g.player_index]
        if g.i == 0:
            end = g.home - 1
        elif g.i == 1:
            end = g.home + 1
        elif g.i == 2:
            end = g.home + g.map_width
        else:
            end = g.home - g.map_width
        g.i = (g.i + 1)%4
        g.attack(g.home, end)

    g.register_listener(process_update)

    g.connect()

    while not g.connected:
        time.sleep(0.5)

    customGameId = "customgame105134823"
    g.join("thisbotwillruletheworld", "jseely-bot", g.GAME_TYPE_PRIVATE, private_game_id=customGameId)
    print("Joined game at http://bot.generals.io/games/{}".format(customGameId))

    while g.in_game_queue:
        print("Waiting in queue...")
        time.sleep(.5)
    while g.in_game:
        time.sleep(1)
    g.disconnect()

if __name__ == "__main__":
    main()
