import socket

from time import time, sleep
from threading import Lock
from json import load

from workers import SendingWorker, ReceivingWorker


def work(data_a: int, data_b: int) -> int:
    return int(bin((data_a + data_b) * (int(time()) % 7))[:8*8].split("b")[1], 2) 

lock = Lock()
with open("settings.json", "r") as f:
    settings = load(f)

sock = socket.socket()
sock.connect((settings["host"], settings["port_c"]))
receiving_worker = ReceivingWorker(sock, lock, "C")
received_data = None
data_a = 0
data_b = 1

while True:
    received_data = receiving_worker.get_data()
    received_data = bin(int(received_data, 16)).split("b")[1] if received_data is not None else "00"
    if received_data == "0":
        continue

    data_a = int(received_data[:len(received_data) // 2], 2) if len(received_data) // 2 > 0 else 0
    data_b = int(received_data[len(received_data) // 2:], 2) if len(received_data) // 2 > 0 else 0
    s = SendingWorker(work(data_a, data_b), sock, lock, "C")
    sleep(0.1)
    del s