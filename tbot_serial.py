"""
Serial plotting library.

Authors:
    Alberto Morato
    Marco Perin

"""

import cProfile
import sys
import time
from queue import Empty as q_Empty
from queue import Queue

import matplotlib.pyplot as plt
from scipy.io import savemat

from robolab.animator import Animator
from robolab.received_structure import DataStruct, PlottingStruct
from robolab.serial_communication.communication import TurtlebotSerialConnector
from robolab.serial_communication.packets import TimedPacketBase

data_struct = PlottingStruct.from_string_list(['fffff'])
data_struct = PlottingStruct.from_yaml_file()


data_struct_str = data_struct.struct_format_string

closed_queue = Queue()


ser = TurtlebotSerialConnector(data_struct)


def on_fig_close(event):
    # global closed_requested
    print('Close requested')
    # print(event)
    # closed_requested = True
    closed_queue.put(True)


def create_axes(data_format: PlottingStruct):
    res = []
    for i in range(len(data_format)):
        res.append(fig.add_subplot(len(data_format), 1, i+1))
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
    return time.time() - t_0


ys = []
xs = []


ys = [[] for _ in range(len(data_struct))]

for y_i in range(len(data_struct)):
    ys[y_i] = [[] for _ in range(len(data_struct[y_i]))]


def animate_frame(x_data, y_data, data_s: DataStruct, ax):

    ax.clear()

    for i in range(len(data_s)):
        ax.plot(x_data[-100:], y_data[i][-100:])
        # ax.scatter(x_data[-100:], y_data[i][-100:])

    names = [s_i.name for s_i in data_s]

    for i, n in enumerate(names):
        if n is not None:
            names[i] = n
        else:
            names[i] = str(i)

    ax.set_title(data_s.name)
    ax.legend(names, loc='upper right')
    ax.grid(True)


anim = Animator(animate_frame, fps=10)

t_prev = currtime()


plt.ion()
plt.show()

# assert len(
#     data_struct
# ) == 1, 'data_struct with more than one plot is not yet implemented'


def manage_packet(
        packet: TimedPacketBase,
        xs, ys,
        data_struct: PlottingStruct
) -> None:
    xs.append(packet.time)
    # print(packet.time)
    for ax_i, ax in enumerate(axes):
        # print(f'data for axes {ax_i}', ax )

        for i, data_aa in enumerate(packet.data[ax_i]):
            ys[ax_i][i].append(data_aa)

        anim.animate(
            xs,
            ys[ax_i],
            data_struct[ax_i],
            ax,
            upd_counter=(ax_i) == len(axes) - 1)

    plt.draw()
    plt.pause(1/30)


ser.connect()

queue = ser.queue

max_t = 100


def loop(xs, ys):
    closed_requested = False
    while not closed_requested and currtime() < max_t:

        try:
            packet = queue.get_nowait()
            # print(packet)
            manage_packet(packet, xs, ys, data_struct)
        except q_Empty:
            pass

        try:
            closed_requested = closed_queue.get_nowait()
        except q_Empty:
            pass


# with cProfile.Profile() as pr:

def main(xs, ys):
    try:
        loop(xs, ys)
    except KeyboardInterrupt:
        print()
        print('Interrupting because of keyboard interrupt.')
        print()

    # pr.print_stats()
    # pr.dump_stats('profile_out')


def main_prof(xs, ys):
    with cProfile.Profile() as pr:
        main(xs, ys)
        pr.print_stats()
        pr.dump_stats('profile_out')


main()

ser.close()

try:
    save_data = input('Do you want to save the data? [Y/n]')
except KeyboardInterrupt:
    save_data = ''

if save_data not in 'Y\n':
    print('Exiting without saving data')
    sys.exit(0)

FILENAME = 'test_data.mat'

file_dict = {
    'turtlebot_data': {
        'time': xs,
        'data': ys
    }
}

savemat(FILENAME, mdict=file_dict)

print('Data saved')
