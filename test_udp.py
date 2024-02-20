"""
Script used to test the `tbot_serial.py` script.

Author:
    Marco Perin

"""
import sys
import socket
from socket import socket as socket_t
from serial import Serial

from math import sin
from clab_datalogger_receiver.serial_communication._utils import (
    get_serial,
    get_serial_port_from_console_if_needed,
)
from clab_datalogger_receiver.received_structure import PlottingStruct
from cobs import cobs
from time import time
from struct import pack as struct_pack
from random import random

from clab_datalogger_receiver.udp_communication.types import UDPData


SEND_DATA_TOKEN = b'\x41'
STOP_DATA_TOKEN = b'\x42'

# ip = '147.162.118.154'
# ip = '127.0.0.1'
ip = 'localhost'
port = 42069


def get_random_single_data(datatype: str):
    """Return a random value of type given y datatype."""
    if datatype == 'f':
        return random()

    raise NotImplementedError(
        f'random data for type {datatype} is not implemented'
    )


def get_random_seed(rx_data_struct: PlottingStruct) -> list[list[float]]:
    """Return random values for each plot item in the data structure."""
    ret = []

    for subplots in rx_data_struct.subplots:
        ret_i = []
        for field in subplots.fields:
            ret_i.append(get_random_single_data(field.data_type) * 10)

        ret.append(ret_i)
    return ret


idx_sin = 2


def get_random_data(
    rx_data_struct: PlottingStruct, seed: list[list[float]]
) -> bytes:
    """Return data representing the packet specified by `data_struct`."""
    subs = []

    for s_i, subplots in enumerate(rx_data_struct.subplots):
        dat = {}
        dat_vals = []
        for f_i, field in enumerate(subplots.fields):
            val = get_random_single_data(field.data_type)
            val = val * 0.9 + seed[s_i][f_i]
            if f_i == idx_sin:
                val *= sin(time())
            dat[field.name] = val
            dat_vals.append(val)

        subs.append(struct_pack(subplots.struct_format_string, *dat_vals))

    return b''.join(subs)


def send_package(
    serial_obj: Serial | UDPData, rx_data_struct: PlottingStruct, seed: list[list[float]]
) -> int | None:
    """Send a packet with structure as in `data_struc` and random values."""

    data = get_random_data(rx_data_struct, seed)
    bytes_to_send = cobs.encode(data) + b'\x00'

    if isinstance(serial_obj, Serial):
        return serial_obj.write(bytes_to_send)
    else:
        serial_obj.send(bytes_to_send)


BAUDRATE = 115200


def await_start_transmission(channel: socket_t) :

    print("Awaiting start transmission data...")
    prev_timout = channel.timeout
    channel.settimeout(1)
    msg = ''
    while msg != SEND_DATA_TOKEN:
        try:
            msg, addr = channel.recvfrom(1024)
            # print("rec: ", addr, msg, SEND_DATA_TOKEN)
            print("Got it!")
        except socket.timeout:
            print('.', end='')
    channel.settimeout(prev_timout)
    return addr


def main_send_test():
    """Start serial transmission to a serial port"""
    data_struct = PlottingStruct.from_yaml_file()

    print(data_struct)

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:

        sock.settimeout(3)

        PPS = 200

        do_exit = False

        # SEND_DATA_TOKEN = b'\x41'
        # while serial.read_until(b'\0x00') != SEND_DATA_TOKEN:

        #     pass

        # print('starting sending data')

        rand_seed = get_random_seed(data_struct)
        print(f"This sender address: {ip}:{port}")
        sock.bind((ip, port))

        addr = await_start_transmission(sock)

        udp_data = UDPData(sock, addr)

        t_prev = time()
        while not do_exit:
            try:
                if time() >= (t_prev + 1 / PPS):
                    # print('sending')
                    send_package(udp_data, data_struct, rand_seed)
                    t_prev = time()

            except KeyboardInterrupt:
                do_exit = True

        return 0


def main_send_receive():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        if any(ag == "-s" for ag in sys.argv):
            sock.bind((ip, port))
            # sock.connect((ip, port))

            addr = await_start_transmission(sock)

            while True:
                msg = input("Specify message: ")
                if msg:
                    print("Sending message:", msg)
                    # sock.send(bytes(msg, 'ascii'))
                    sock.sendto(bytes(msg, 'ascii'), addr)
                    # sock.sendto(bytes(msg, 'ascii'), (ip, port))
        else:
            # sock.bind((ip, port))
            sock.connect((ip, port))
            sock.settimeout(2)
            sock.sendto(SEND_DATA_TOKEN, (ip, port))

            while True:
                # buffer size is 1024 bytes
                try:
                    # data, addr = sock.recv(1024)
                    data = sock.recv(1024)
                    addr = '---'
                    # data = sock.recvfrom(1024)
                    print(f"received message: \"{data}\" from {addr}")
                except socket.timeout:
                    print('.', end="", flush=True)


# with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
#     sock.connect((ip, port))
#     # sock.sendall(bytes(message, 'ascii'))
#     response = sock.recv(1024)
#     print('Received: ', response)


if __name__ == "__main__":

    # If the program is run with "--both" keyword,
    #    then it can be run in both send and receive mode.
    if any(ag == "--both" for ag in sys.argv):
        main_send_receive()

    # raise NotImplementedError
    main_send_test()
