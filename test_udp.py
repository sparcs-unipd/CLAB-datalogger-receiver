"""
Script used to test the `tbot_serial.py` script.

Author:
    Marco Perin

"""
import sys
import socket

# Used for help message
from shutil import get_terminal_size
from socket import socket as socket_t
from math import sin
from random import random
from struct import pack as struct_pack
from time import time
from typing import List


from cobs import cobs
from serial import Serial

from clab_datalogger_receiver.received_structure import PlottingStruct
from clab_datalogger_receiver.udp_communication.types import UDPData

# TODO: set these in a config file somewhere, maybe
SEND_DATA_TOKEN = b'\x41'
STOP_DATA_TOKEN = b'\x42'

# ip = '147.162.118.154'
# ip = '127.0.0.1'
IP = 'localhost'
PORT = 42069
PPS = 200


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
    serial_obj: Serial | UDPData,
    rx_data_struct: PlottingStruct,
    seed: list[list[float]],
) -> int | None:
    """Send a packet with structure as in `data_struc` and random values."""

    data = get_random_data(rx_data_struct, seed)
    bytes_to_send = cobs.encode(data) + b'\x00'

    if isinstance(serial_obj, Serial):
        return serial_obj.write(bytes_to_send)

    return serial_obj.send(bytes_to_send)


BAUDRATE = 115200


def await_start_transmission(channel: socket_t):
    """Wait for the START_DATA_TOKEN to be received, blocking."""
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

    do_exit = False

    while not do_exit:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(3)

            sock.settimeout(1 / (PPS * 1.1))

            rand_seed = get_random_seed(data_struct)
            print(f"This sender address: {IP}:{PORT}")
            sock.bind((IP, PORT))

            addr = await_start_transmission(sock)

            udp_data = UDPData(sock, addr)
            do_exit_receive = False
            t_prev = time()

            while not do_exit_receive:
                try:
                    if time() >= (t_prev + 1 / PPS):
                        # print('sending')
                        send_package(udp_data, data_struct, rand_seed)
                        t_prev = time()
                    data = sock.recv(1024)

                    if data == STOP_DATA_TOKEN:
                        print('Stopping requested.')
                        do_exit_receive = True

                except socket.timeout:
                    pass
                except ConnectionResetError:
                    print('Connection reset.')
                    do_exit_receive = True

                except KeyboardInterrupt:
                    do_exit = True

        if not do_exit:
            # Disconnection occured
            #  recreate socket and wait for START_DATA_TOKEN
            print('Recreating socket!')

    return 0


def print_help_msg():
    """Prints the instructions on how to use this script."""

    cmd_len = 30
    desc_len = get_terminal_size().columns - cmd_len - 2  # 2 for the 2 spaces
    format_str = '  {:<' + str(cmd_len) + '}{:<' + str(desc_len) + '}'

    def get_cmd_desc_line(line: str, cmd=''):
        return [
            format_str.format(cmd, line[i : i + desc_len])
            for i in range(0, len(line), desc_len)
        ]

    def print_cmd_desc(cmd: str, desc_lines: str | List[str]):
        if isinstance(desc_lines, str):
            lines = get_cmd_desc_line(desc_lines, cmd)
        else:
            # desc_lines is List[str]
            lines = []
            for i, line in enumerate(desc_lines):
                lines.extend(get_cmd_desc_line(line, cmd if i == 0 else ''))

        for line in lines:
            print(line)

    print()
    print('Usage:')
    print('  python test_udp.py [options]')
    print()
    print('Options:')
    print_cmd_desc('-h, --help', 'Test desc')
    print_cmd_desc(
        '--both <mode>',
        [
            'Use this to run both sender and receiver from command line.',
            '  mode="-r" runs in receiver mode',
            '  mode="-s" in server mode',
        ],
    )
    print()


def main_send_receive():
    """
    CLI simple interface for testing the send and receive by UDP.

    Used if this script is run with argument --both.

    in particular:

        `python test_udp.py --both -r` runs the receiver

        `python test_udp.py --both -s` runs the sender


    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        if any(ag == "-s" for ag in sys.argv):
            sock.bind((IP, PORT))

            addr = await_start_transmission(sock)

            while True:
                msg = input("Specify message: ")
                if msg:
                    print("Sending message:", msg)
                    sock.sendto(bytes(msg, 'ascii'), addr)
        else:
            sock.connect((IP, PORT))
            sock.settimeout(2)
            sock.sendto(SEND_DATA_TOKEN, (IP, PORT))

            while True:
                # buffer size is 1024 bytes
                try:
                    data = sock.recv(1024)
                    addr = '---'
                    print(f"received message: \"{data}\" from {addr}")
                except socket.timeout:
                    print('.', end="", flush=True)


if __name__ == "__main__":
    # If the program is run with "--both" keyword,
    #    then it can be run in both send and receive mode.
    if any(ag == "--help" for ag in sys.argv):
        print_help_msg()
        sys.exit(0)
    if any(ag == "--both" for ag in sys.argv):
        main_send_receive()

    # raise NotImplementedError
    sys.exit(main_send_test())
