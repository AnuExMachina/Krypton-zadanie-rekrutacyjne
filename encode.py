from random import randint
from math import ceil

def encode(value: int) -> str:
    ff = str(randint(0,1))
    rtr = str(randint(0,1))
    can_id = ""
    for _ in range(32):
        can_id += str(randint(0,1))

    data = bin(value).split("b")[1].zfill(8*8)
    length = bin(ceil(len(data) / 8)).split("b")[1].zfill(4)    
    data = data.zfill(int(length, 2) * 8)
    frame = (ff + rtr + "00" + length + can_id + data).ljust(13*8, "0")
    return frame

def decode(message: bytes) -> dict:
    result = {
        "ff": 0,
        "rtr": 0,
        "length": 0,
        "can_id": 0,
        "data": 0
    }

    result["ff"] = message[0]
    result["rtr"] = message[1]
    result["length"] = int(message[4:8], 2)
    result["can_id"] = hex(int(message[9:40], 2))
    result["data"] = hex(int(message[40:40+result["length"]*8], 2)) if result["length"] > 0 else hex(0)

    return result

if __name__ == "__main__":
    message = encode(0x1234567800)
    print(f"message: {message}")
    print(len(message))
    print(f"hex message: {hex(int(message, 2))}")
    hex_pairs = []
    for i in range(0, len(message), 8):
        hex_pairs.append(hex(int(message[i:i+8], 2)))
    print(" ".join(hex_pairs))
    print(message[0:8])
    print(decode(message))
