import socket

from time import sleep
from json import load
from random import randint
from threading import Lock
from time import time
from sys import exit

from workers import SendingWorker, ReceivingWorker


def work() -> str:
    output_current = randint(0, 200)
    transistor_current = randint(0, 200)
    hv_voltage = randint(0, 200)
    lv_voltage = randint(0, 200)
    temperature = randint(0, 200)

    ok = output_current < output_limit and transistor_current < transistor_limit and hv_limits[0] < hv_voltage < hv_limits[1] and lv_limits[0] < lv_voltage < lv_limits[1] and temperature

    if ok:
        return int(bin(2**15).split("b")[1] + bin(randint(0, 2**16)).split("b")[1].zfill(16) + bin(hv_voltage).split("b")[1].zfill(16) + bin(lv_voltage).split("b")[1].zfill(16), 2)
    if randint(0,100) > 90:
        return int(bin(2**7).split("b")[1] + bin(randint(0, 2**16)).split("b")[1].zfill(16) + bin(hv_voltage).split("b")[1].zfill(16) + bin(lv_voltage).split("b")[1].zfill(16), 2)
    
    status = 0

    if output_current > output_limit:
        status += 2**14
    elif output_current == output_limit:
        status += 2**6

    if transistor_current > transistor_limit:
        status += 2**13
    elif transistor_current == transistor_limit:
        status += 2**5
        
    if hv_voltage > hv_limits[1]:
        status += 2**12
    elif hv_voltage < hv_limits[0]:
        status += 2**11
    elif hv_voltage == hv_limits[1]:
        status += 2**4
    elif hv_voltage == hv_limits[0]:
        status += 2**3

    if lv_voltage > lv_limits[1]:
        status += 2**10
    elif lv_voltage < lv_limits[0]:
        status += 2**9
    elif lv_voltage == lv_limits[1]:
        status += 2**2
    elif lv_voltage == lv_limits[1]:
        status += 2**1

    if temperature > thermal_limit:
        status += 2**8
    elif temperature == thermal_limit:
        status += 2**0

    data = bin(status).split("b")[1] + bin(randint(0, 2**16)).split("b")[1].zfill(16) + bin(hv_voltage).split("b")[1].zfill(16) + bin(lv_voltage).split("b")[1].zfill(16)

    return int(data.zfill(8*8), 2)

lock = Lock()
with open("settings.json", "r") as f:
    settings = load(f)
sock = socket.socket()
sock.connect((settings["host"], settings["port_b"]))

receiving_worker = ReceivingWorker(sock, lock, "B")

output_limit = 100
transistor_limit = 100
hv_limits = (0, 100)
lv_limits = (0, 100)
thermal_limit = 100

data = None

working = False

while True:
    data = receiving_worker.get_data()

    if not data:
        sleep(settings["sleep_time_b"])
        continue

    data = bin(int(data, 16)).split("b")[1].zfill(8*8)

    if data[0] == "1":
        working = True
    if data[1] == "1":
        working = False

    hv_limits = (int(data[16:32], 2), int(data[32:48], 2))
    lv_limits = (int(data[48:], 2), 100)

    if not working:
        continue

    with lock:
        data_to_send = work()

    s = SendingWorker(data_to_send, sock, lock, "B")

    sleep(settings["sleep_time_b"])
    del s