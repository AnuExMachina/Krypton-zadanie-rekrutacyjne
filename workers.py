import encode
import uvicorn

from socket import socket
from threading import Thread, Lock
from fastapi import FastAPI
from json import load
from time import sleep



class SendingWorker(Thread):
    def __init__(self, data: int, socket: socket, lock: Lock, device: str, debug: bool = False):
        Thread.__init__(self, name=f"{device}Sender", daemon=True)
        self.data = encode.encode(data).encode("utf-8")
        self.socket = socket
        self.lock = lock
        self.device = device
        self.debug = debug
        Thread.start(self)
    
    def run(self):
        with self.lock:
            self.socket.send(self.data)
        if self.debug:
            print(f"{self.device}: sent data: {encode.decode(self.data)}")


class ReceivingWorker(Thread):
    def __init__(self, socket: socket, lock: Lock, device: str, debug: bool = False):
        Thread.__init__(self, name=f"{device}Receiver", daemon=True)
        self.socket = socket
        self.lock = lock
        self.data = None
        self.device = device
        self.debug = debug
        Thread.start(self)

    def run(self):
        while True:
            new_data = ""
            new_data += self.socket.recv(13*8).decode("utf-8")
            if not new_data:
                return
            with self.lock:
                self.data = encode.decode(new_data)["data"] 
            if self.debug:
                print(f"{self.device}: received data: {self.data}")

    def get_data(self):
        return self.data

class ApiWorker(Thread):
    app = FastAPI()

    def __init__(self, app):
        Thread.__init__(self, daemon=True)
        self.data = 2
        self.app = app
        Thread.start(self)
    
    def run(self):
        with open("settings.json", "r") as f:
            settings = load(f)
        uvicorn.run(self.app, host=settings["host"], port=settings["port"])

class WatchDogWorker(Thread):
    def __init__(self, sock: socket, data: bytes, lock: Lock):
        Thread.__init__(self, daemon=True, name="WatchdogSender")
        self.sock = sock
        self.data = data
        self.lock = lock
        Thread.start(self)
    
    def run(self):
        while True:
            with self.lock:
                self.sock.send((self.data[:3] + "1" + self.data[4:]))
            sleep(0.5)
    
    def set_data(self, data: bytes):
        with self.lock:
            self.data = data
