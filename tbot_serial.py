"""
Serial plotting library.

Authors:
    Alberto Morato
    Marco Perin

"""

import sys
import time
from queue import Empty as q_Empty, Queue

import matplotlib.pyplot as plt

from clab_datalogger_receiver.animator import Animator
from clab_datalogger_receiver.received_structure import DataStruct, PlottingStruct
from clab_datalogger_receiver.serial_communication.communication import TurtlebotSerialConnector
from clab_datalogger_receiver.serial_communication.packets import TimedPacketBase

from scipy.io import savemat

MAT_FILENAME = 'test_data.mat'
MAX_ACQUISITION_TIME = 100  # s


# Data struct from format string list examples
# data_struct = PlottingStruct.from_string_list(['fffff'])
# data_struct = PlottingStruct.from_string_list(['fff'],['ff'])

# Data struct from yaml configuration file
data_struct = PlottingStruct.from_yaml_file()

data_struct_str = data_struct.struct_format_string

# Queue to signal when the plot is closed
#  (or when, in general, a 'close' event occurs)
closed_queue = Queue()

ser = TurtlebotSerialConnector(data_struct)


def on_fig_close(_):
    """Signal that the plot is closed."""
    print('Close requested')

    closed_queue.put(True)


def create_axes(data_format: PlottingStruct):
    """Create image axis based on the data struct."""
    res = []
    for i in range(len(data_format)):
        res.append(fig.add_subplot(len(data_format), 1, i+1))  # type: ignore
        plt.grid(True)

    return res


fig = plt.figure()
fig.canvas.mpl_connect('close_event', on_fig_close)

axes = create_axes(data_struct)


# ax = fig.add_subplot(1, 1, 1)

# if data_struct[0].name is None:
plt.title('Received data')
# else:
#     plt.title(data_struct[0].name)

t_0 = time.time()


def currtime():
    """Return the time since `t_0`."""
    return time.time() - t_0


y_data_vector = []
x_data_vector = []


y_data_vector = [[] for _ in range(len(data_struct))]

for y_i in range(len(data_struct)):
    y_data_vector[y_i] = [[] for _ in range(len(data_struct[y_i]))]


def animate_frame(x_data, y_data, data_s: DataStruct, axis):
    """Define what to do in order to refresh the plot."""
    axis.clear()

    for i in range(len(data_s)):
        axis.plot(x_data[-100:], y_data[i][-100:])
        # ax.scatter(x_data[-100:], y_data[i][-100:])

    names = [s_i.name for s_i in data_s]

    for i, name in enumerate(names):
        if name is not None:
            names[i] = name
        else:
            names[i] = str(i)

    axis.set_title(data_s.name)
    axis.legend(names, loc='upper right')
    axis.grid(True)


anim = Animator(animate_frame, fps=10)

t_prev = currtime()

plt.ion()
plt.show()


def manage_packet(
        packet: TimedPacketBase,
        x_data,
        y_data,
        rx_data_struct: PlottingStruct
) -> None:
    """
    Manage a packet received from serial reader queue.

    It is expected that the packet is a subclass of `TimedPacketBase`.

    """
    x_data.append(packet.time)

    for ax_i, axis in enumerate(axes):

        for i, data_aa in enumerate(packet.data[ax_i]):
            y_data[ax_i][i].append(data_aa)

        anim.animate(
            x_data,
            y_data[ax_i],
            rx_data_struct[ax_i],
            axis,
            upd_counter=(ax_i) == len(axes) - 1)

    plt.draw()
    plt.pause(1/30)


ser.connect()

rx_queue = ser.queue


def loop(x_data, y_data):
    """Execute main loop."""
    closed_requested = False
    while not closed_requested and currtime() < MAX_ACQUISITION_TIME:

        try:
            packet = rx_queue.get_nowait()
            # print(packet)
            manage_packet(packet, x_data, y_data, data_struct)
        except q_Empty:
            pass

        try:
            closed_requested = closed_queue.get_nowait()
        except q_Empty:
            pass


def main(x_data, y_data):
    """Execute the loop checking for keybard interrupts."""
    try:
        loop(x_data, y_data)
    except KeyboardInterrupt:
        print()
        print('Interrupting because of keyboard interrupt.')
        print()


def main_prof(x_data, y_data):
    """Execute the main function while also executing the profiler."""
    # pylint: disable=import-outside-toplevel
    import cProfile
    # pylint: enable=import-outside-toplevel

    with cProfile.Profile() as profiler:

        main(x_data, y_data)

        profiler.print_stats()
        profiler.dump_stats('profile_out')


if __name__ == '__main__':

    main(x_data_vector, y_data_vector)

    ser.close()
    save_data = ''

    try:
        save_data = input('Do you want to save the data? [Y/n]')
    except KeyboardInterrupt:
        # Treat `CTRL+C` as a no
        pass

    if save_data not in 'Y\n':
        print('Exiting without saving data')
        sys.exit(0)

    file_dict = {
        'turtlebot_data': {
            'time': x_data_vector,
            'data': y_data_vector
        }
    }

    savemat(MAT_FILENAME, mdict=file_dict)

    print('Data saved')
