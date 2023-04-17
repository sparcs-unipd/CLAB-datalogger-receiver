"""

Serial interface manager for the connection with the turtlebot.

Authors:
    Alberto Morato
    Marco Perin

"""

from queue import Empty as q_Empty
from queue import Queue

from robolab.received_structure import PlottingStruct

from .serial_communication.communication import TurtlebotReaderThread
from .serial_communication._utils import get_serial, get_serial_port

if __name__ == '__main__':
    # pylint: disable=wrong-import-position
    # import sys
    import time
    # import traceback

    # ~ PORT = 'spy:///dev/ttyUSB0'
    # PORT = 'loop://'

    port = get_serial_port()

    serial_obj = get_serial(port)

    packet_spec = PlottingStruct.from_yaml_file()

    queue = Queue()

    thread = TurtlebotReaderThread(serial_obj, packet_spec, queue)

    thread.start()

    trans, prot = thread.connect()

    prot.signal_start_communication()

    t_0 = time.time()

    T = 10  # s

    while time.time() < t_0 + T:
        try:
            d = queue.get(timeout=T)
            print('received: ', d)
        except q_Empty:
            print('No data received')
            break

        if not thread.alive:
            print('THREAD_DEAD')
            break

    prot.signal_stop_communication()

    thread.close()
