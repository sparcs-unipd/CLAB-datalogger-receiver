"""
Script used to test the `tbot_serial.py` script.

Author:
    Marco Perin

"""

import sys
from random import random
from struct import pack as struct_pack
from time import time

from cobs import cobs

from serial import Serial

from clab_datalogger_receiver.received_structure import PlottingStruct
from clab_datalogger_receiver.serial_communication._utils import (
    get_serial,
    get_serial_port,
)


def get_random_single_data(datatype: str):
    """Return a random value of type given y datatype."""
    if datatype == 'f':
        return random()

    raise NotImplementedError(f'random data for type {datatype} is not implemented')


def get_random_seed(rx_data_struct: PlottingStruct) -> list[list[float]]:
    ret = []

    for subplots in rx_data_struct.subplots:
        ret_i = []
        for field in subplots.fields:
            ret_i.append(get_random_single_data(field.data_type) * 10)

        ret.append(ret_i)
    return ret


def get_random_data(rx_data_struct: PlottingStruct, seed: list[list[float]]) -> bytes:
    """Return data representing the packet specified by `data_struct`."""
    subs = []

    for s_i, subplots in enumerate(rx_data_struct.subplots):
        dat = {}
        dat_vals = []
        for f_i, field in enumerate(subplots.fields):
            val = get_random_single_data(field.data_type) * 0.2 + seed[s_i][f_i]
            dat[field.name] = val
            dat_vals.append(val)

        subs.append(struct_pack(subplots.struct_format_string, *dat_vals))

    return b''.join(subs)


def send_package(
    serial_obj: Serial, rx_data_struct: PlottingStruct, seed: list[list[float]]
) -> int | None:
    """Send a packet with structure as in `data_struc` and random values."""

    data = get_random_data(rx_data_struct, seed)
    bytes_to_send = cobs.encode(data) + b'\x00'
    return serial_obj.write(bytes_to_send)


if __name__ == '__main__':
    data_struct = PlottingStruct.from_yaml_file()

    autoscan = False
    autoscan_pattern = 'STMicroelectronics'

    if len(sys.argv) > 1:
        autoscan = True
        autoscan_pattern = sys.argv[1]

    BAUDRATE = 115200

    print(data_struct)

    port = get_serial_port(
        autoscan_port=autoscan, autoscan_port_pattern=autoscan_pattern
    )
    serial = get_serial(port)

    serial.write_timeout = 5

    PPS = 200

    do_exit = False

    # SEND_DATA_TOKEN = b'\x41'
    # while serial.read_until(b'\0x00') != SEND_DATA_TOKEN:
    #     pass

    # print('starting sending data')

    rand_seed = get_random_seed(data_struct)

    t_prev = time()
    while not do_exit:
        try:
            if time() >= (t_prev + 1 / PPS):
                # print('sending')
                send_package(serial, data_struct, rand_seed)
                t_prev = time()

        except KeyboardInterrupt:
            do_exit = True

    serial.close()

    sys.exit(0)
