import socket

from time import sleep
from json import load
from random import randint
from threading import Lock
from time import time

from workers import SendingWorker


lock = Lock()
working = True
with open("settings.json", "r") as f:
    settings = load(f)
sock = socket.socket()
sock.connect((settings["host"], settings["port_a"]))


while working:
    with lock:
        data = randint(0, 255**8)
    s = SendingWorker(data, sock, lock, "A")

    sleep(settings["sleep_time_a"])
    del s