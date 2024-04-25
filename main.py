import socket

from time import sleep
from json import load
from threading import Lock
from time import time
from random import randint
from sys import exit 
from fastapi import FastAPI, Request

from workers import ReceivingWorker, SendingWorker, ApiWorker, WatchDogWorker


STATUSES = [
    "ready",
    "output overcurrent",
    "transistor overcurrent",
    "HV overvoltage",
    "HV undervoltage",
    "LV overvoltage",
    "LV undervoltage",
    "thermal failure",
    "control autodiagnostics failure",
    "output overcurrent triggered",
    "transistor overcurrent triggered",
    "HV overvoltage triggered",
    "HV undervoltage triggered",
    "LV overvoltage triggered",
    "LV undervoltage triggered",
    "thermal failsafe triggered"
]

def generate_some_data_for_b(start: bool = True) -> str:
    data = (str(int(start)) + str(int(not start))).ljust(16, "0")

    low_hv = randint(0, 2**16)
    high_hv = randint(0, 2**16)
    low_lv = randint(0, 2**16)
    data += bin(low_hv).split("b")[1].zfill(16) + bin(high_hv).split("b")[1].zfill(16) + bin(low_lv).split("b")[1].zfill(16)

    return int(data, 2)


if __name__ == "__main__":
    app = FastAPI()
    app_mode = "default"

    with open("settings.json", "r") as f:
        settings = load(f)

    lock_a = Lock()
    data_a = None

    lock_b = Lock()
    data_b = None

    lock_c = Lock()
    data_c = None
            
    server_socket_a = socket.socket()
    server_socket_a.bind((settings["host"], settings["port_a"]))
    server_socket_a.listen(5)
    client_socket_a, _ = server_socket_a.accept()
    receiving_worker_a = ReceivingWorker(client_socket_a, lock_a, "A")

    server_socket_b = socket.socket()
    server_socket_b.bind((settings["host"], settings["port_b"]))
    server_socket_b.listen(5)
    client_socket_b, _ = server_socket_b.accept()
    receiving_worker_b = ReceivingWorker(client_socket_b, lock_b, "B")
    b_current_settings = generate_some_data_for_b(False)

    start_time = time() 

    server_socket_c = socket.socket()
    server_socket_c.bind((settings["host"], settings["port_c"]))
    server_socket_c.listen(5)
    client_socket_c, _ = server_socket_c.accept()
    receiving_worker_c = ReceivingWorker(client_socket_c, lock_c, "C")

    @app.get("/a")
    async def get_a():
        data = receiving_worker_a.get_data()
        return data

    @app.get("/b")
    async def get_b():
        data = receiving_worker_b.get_data()
        if data is None:
            return {"Status": "Device B is not currently working."}
        data = int(data, 16)
        data = bin(data).split('b')[1].zfill(8*8)
        return {
            "status": [STATUSES[i] for i in range(16) if data[i] == "1"], 
            "I-LV-1": int(data[16:32], 2), 
            "HV": int(data[32:48], 2),
            "LV": int(data[48:], 2)
            } if data != 0 else 0

    @app.post("/b")
    async def post_b(req: Request):
        req = await req.json()
        if req["hv_lower"] >= req["hv_upper"]:
            return {"Status": "Incorrect hv input data"}
        if req["lv_lower"] >= 100:
            return {"Status": "Incorrect lv input data"}
        hv_lower_limit = bin(req["hv_lower"]).split("b")[1].zfill(16)
        hv_upper_limit = bin(req["hv_upper"]).split("b")[1].zfill(16)
        lv_lower_limit = bin(req["lv_lower"]).split("b")[1].zfill(16)

        start = bin(req["start"]).split("b")[1]
        stop = bin(req["stop"]).split("b")[1]
        wd.set_data(start + stop + "0" * 14 + hv_lower_limit + hv_upper_limit + lv_lower_limit)
        SendingWorker(int(start + stop + "0" * 14 + hv_lower_limit + hv_upper_limit + lv_lower_limit, 2), client_socket_b, lock_b, "B")
        return {"message": "Data set successfully!"}

    @app.get("/c")
    async def get_c():
        return receiving_worker_c.get_data()

    @app.post("/app")
    async def post_app(req: Request):
        req = await req.json()
        app_mode = req["mode"]
        return {"message": "Mode set successfully!"}

    wd = WatchDogWorker(client_socket_b, b_current_settings, lock_b)
    api_worker = ApiWorker(app)
    while True:
        with lock_a:
            data_a = receiving_worker_a.get_data()
        data_a = int(data_a, 16) if data_a is not None else 0

        with lock_b:
            data_b = receiving_worker_b.get_data()
        data_b = int(data_b, 16) if data_b is not None else 0

        with lock_c:
            data_c = receiving_worker_c.get_data()
        
        with lock_a:
            with lock_b:
                new_data_for_c = bin(data_a // 2).split("b")[1].zfill(4*8) + bin(data_b // 2).split("b")[1].zfill(4*8)
                s = SendingWorker(int(new_data_for_c, 2), client_socket_c, lock_c, "C")
        
        sleep(min([settings["sleep_time_a"], settings["sleep_time_b"], 0.1]))
        del s