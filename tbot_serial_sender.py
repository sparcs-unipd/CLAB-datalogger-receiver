
from robolab.received_structure import DataStruct, PlottingStruct
from robolab.serial_communication.communication import TurtlebotSerialConnector
from robolab.serial_communication.packets import TimedPacketBase
from robolab.serial_communication._utils import get_serial, get_serial_port

from serial import Serial
from time import time
from struct import pack as struct_pack, pack_into
from cobs import cobs

from random import random

import sys

# data_struct = PlottingStruct.from_string_list(['fffff'])
data_struct = PlottingStruct.from_yaml_file()

BAUDRATE = 115200

print(data_struct)

def get_random_single_data(datatype: str):
    # print('getting rand data for type: ', datatype)

    if datatype == 'f':
        return random()
    else:
        raise NotImplementedError(
            f'random data for type {datatype} is not implemented'
            )

def get_random_data_list_of_bytes():
    
    subs = []

    for ss in data_struct.subplots:
        
        # print(ss)
        dat = {}
        dat_vals = []
        for field in ss.fields:
            val = get_random_single_data(field.data_type)
            dat[field.name] = val
            dat_vals.append(val)

        # subs.append(dat)
        # subs.append(tuple(dat_vals))
        # print('format: ', ss.struct_format_string)
        # print('dat: ', dat_vals)
        subs.append(struct_pack(ss.struct_format_string, *dat_vals))

    # print(subs)
    return subs

def get_random_data():
    return b''.join(get_random_data_list_of_bytes())

# def get_random_data():

#     data_list_tupls = 



port = get_serial_port()
# port = '\\\\.\\CNCB0'
serial = get_serial(port)

serial.write_timeout = 5
def send_package():

    data = get_random_data()
    bytes_to_send = cobs.encode(data) + b'\x00'
    # print(bytes_to_send)
    serial.write(bytes_to_send)


PPS = 20

do_exit = False

t_prev = time()

while not do_exit:
    try:
        if time() >= (t_prev + 1/PPS):
            # print('sending')
            send_package()
            t_prev = time()

    except KeyboardInterrupt:
        do_exit = True

serial.close()
