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

from robolab.received_structure import PlottingStruct
from robolab.serial_communication._utils import get_serial, get_serial_port


def get_random_single_data(datatype: str):
    """Return a random value of type given y datatype."""
    if datatype == 'f':
        return random()

    raise NotImplementedError(
        f'random data for type {datatype} is not implemented'
    )


def get_random_data(
    rx_data_struct: PlottingStruct
) -> bytes:
    """Return data representing the packet specified by `data_struct`."""
    subs = []

    for subplots in rx_data_struct.subplots:

        dat = {}
        dat_vals = []
        for field in subplots.fields:
            val = get_random_single_data(field.data_type)
            dat[field.name] = val
            dat_vals.append(val)

        subs.append(struct_pack(subplots.struct_format_string, *dat_vals))

    return b''.join(subs)


def send_package(
    serial_obj: Serial,
        rx_data_struct: PlottingStruct
) -> int | None:
    """Send a packet with structure as in `data_struc` and random values."""
    data = get_random_data(rx_data_struct)
    bytes_to_send = cobs.encode(data) + b'\x00'
    return serial_obj.write(bytes_to_send)


if __name__ == '__main__':

    data_struct = PlottingStruct.from_yaml_file()

    BAUDRATE = 115200

    print(data_struct)

    port = get_serial_port()
    serial = get_serial(port)

    serial.write_timeout = 5

    PPS = 20

    do_exit = False

    t_prev = time()

    while not do_exit:
        try:
            if time() >= (t_prev + 1/PPS):
                # print('sending')
                send_package(serial, data_struct)
                t_prev = time()

        except KeyboardInterrupt:
            do_exit = True

    serial.close()

    sys.exit(0)
