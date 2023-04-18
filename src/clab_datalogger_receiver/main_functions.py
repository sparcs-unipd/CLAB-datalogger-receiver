"""
This module is made in order to provide a general entrypoint to \
    the package functions.

Author:
    Marco Perin

"""


import time
import sys
from queue import Empty as q_Empty, Queue
from matplotlib.axes import Axes


import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from scipy.io import savemat

from .animator import Animator
from .received_structure import PlottingStruct
from .serial_communication.communication import TurtlebotSerialConnector
from .serial_communication.packets import TimedPacketBase


class ClabDataLoggerReceiver:
    """Main class for managing the datalogging task."""

    data_struct: PlottingStruct
    closed_queue: Queue[bool]
    figure: Figure
    axes: list[Axes]

    t_0: float

    y_data_vector = []
    x_data_vector = []

    animator: Animator

    t_prev: float

    serial_conn: TurtlebotSerialConnector

    rx_queue: Queue[TimedPacketBase]

    max_time: float = -1

    def __init__(self, fps: int = 10, max_time: float = -1) -> None:
        """Initialize the class."""
        self.data_struct = PlottingStruct.from_yaml_file()
        self.closed_queue = Queue()
        self.figure = plt.figure()
        self.figure.canvas.mpl_connect(
            'close_event',
            self.on_fig_close
        )
        self.max_time = max_time

        self.axes = self.create_axes()

        self.t_0 = time.time()

        self.init_data_vectors()

        self.animator = Animator(
            self.animate_frame,
            fps=fps
        )

        self.t_prev = self.currtime()

        plt.ion()
        plt.show()

    def connect(self):
        """Establish connection."""
        self.serial_conn = TurtlebotSerialConnector(self.data_struct)
        self.rx_queue = self.serial_conn.queue
        self.serial_conn.connect()

    def do_loop_while_true(self):
        """Execute `self.loop()` until exit is requested."""
        exit_requested = False

        while not exit_requested:
            exit_requested = self.loop()

        plt.close()

    def do_loop_while_true_profiling(
        self,
        filename_out: str = 'profile_out.prof'
    ):
        """Execute the loop_while_true function while also profiling."""
        # pylint: disable=import-outside-toplevel
        import cProfile
        # pylint: enable=import-outside-toplevel

        with cProfile.Profile() as profiler:

            self.do_loop_while_true()
            profiler.print_stats()
            profiler.dump_stats(filename_out)

    def loop(self) -> bool:
        """
        Execute the loop checking for keybard interrupts.

        Returns `True` if exit is requested.

        """
        try:
            return self.__loop()
        except KeyboardInterrupt:
            print('Interrupting because of keyboard interrupt.')
            return True

    def __loop(self) -> bool:
        """
        Execute the main loop.

        Returns `True` if exit is requested.

        """
        closed_requested = False

        try:
            packet = self.rx_queue.get_nowait()
            # print(packet)
            self.manage_packet(packet)
        except q_Empty:
            pass

        try:
            closed_requested = self.closed_queue.get_nowait()
        except q_Empty:
            closed_requested = False

        if self.max_time != -1 and not closed_requested:
            closed_requested = self.currtime() > self.max_time

        return closed_requested

    def on_fig_close(self, _):
        """Signal that the plot is closed."""
        print('Close requested')

        self.closed_queue.put(True)

    def create_axes(self):
        """Create image axis based on the data struct."""
        rx_data_format = self.data_struct
        res = []
        for i in range(len(rx_data_format)):
            res.append(
                self.figure.add_subplot(
                    len(rx_data_format), 1, i+1)  # type: ignore
            )
            plt.grid(True)

        return res

    def currtime(self) -> float:
        """Return time elapsed since initialization."""
        return time.time() - self.t_0

    def init_data_vectors(self) -> None:
        """Initialize `self.y_data_vector` according to `self.data_struct`."""
        self.y_data_vector = [[] for _ in range(len(self.data_struct))]

        for y_i in range(len(self.data_struct)):
            self.y_data_vector[y_i] = [[]
                                       for _ in
                                       range(len(
                                           self.data_struct[y_i]
                                       ))]

    def animate_frame(
        self,
        ax_i: int,
        axis: Axes
    ):
        """Define what to do in order to refresh the plot."""
        axis.clear()

        data_s = self.data_struct[ax_i]
        x_data = self.x_data_vector
        y_data = self.y_data_vector[ax_i]

        for i in range(len(data_s)):
            axis.plot(x_data[-100:], y_data[i][-100:])
            # ax.scatter(x_data[-100:], y_data[i][-100:])

        names = [s_i.name for s_i in data_s]

        for i, name in enumerate(names):
            if name is not None:
                names[i] = name
            else:
                names[i] = str(i)

        if data_s.name is not None:
            axis.set_title(data_s.name)
        else:
            axis.set_title('received data')

        axis.legend(names, loc='upper right')
        axis.grid(True)

    def manage_packet(
            self,
            packet: TimedPacketBase
    ) -> None:
        """
        Manage a packet received from serial reader queue.

        It is expected that the packet is a subclass of `TimedPacketBase`.

        """
        self.x_data_vector.append(packet.time)

        for ax_i, axis in enumerate(self.axes):

            for i, data_aa in enumerate(packet.data[ax_i]):
                self.y_data_vector[ax_i][i].append(data_aa)

            self.animator.animate(
                ax_i,
                axis,
                upd_counter=(ax_i) == len(self.axes) - 1
            )

        plt.draw()
        plt.pause(1/30)


def save_data(
        datalogger: ClabDataLoggerReceiver,
        mat_filename: str = 'out_data.mat'
):
    """Save the data of datalogger."""
    save_data_in = ''
    try:
        save_data_in = input('Do you want to save the data? [Y/n]')
    except KeyboardInterrupt:
        # Treat `CTRL+C` as a no
        pass

    if save_data_in not in 'Y\n':
        print('Exiting without saving data')
        sys.exit(0)

    file_dict = {
        'turtlebot_data': {
            'time': datalogger.x_data_vector,
            'data': datalogger.y_data_vector
        }
    }

    savemat(mat_filename, mdict=file_dict)

    print('Data saved.')


def main(dlogger: ClabDataLoggerReceiver | None = None):
    """Run an example of a main function."""
    if dlogger is None:
        dlogger = ClabDataLoggerReceiver()

    dlogger.connect()

    dlogger.do_loop_while_true()

    dlogger.serial_conn.close()

    save_data(dlogger)

    sys.exit(0)


if __name__ == '__main__':

    main()
