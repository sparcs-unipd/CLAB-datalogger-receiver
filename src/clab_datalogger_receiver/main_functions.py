"""
This module is made in order to provide a general entrypoint to \
    the package functions.

Author:
    Marco Perin

"""
from __future__ import annotations

import os
import sys
import time
from abc import abstractmethod
from queue import Empty as q_Empty
from queue import Queue
from typing import Callable

import matplotlib.pyplot as plt
import pyqtgraph as pg
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from PyQt6 import QtGui, QtWidgets
from pyqtgraph import GraphicsLayout, PlotDataItem, PlotItem, PlotWidget
from scipy.io import savemat

from .animator import Animator
from .received_structure import PlottingStruct
from .serial_communication.communication import TurtlebotSerialConnector
from .serial_communication.packets import TimedPacketBase


class GraphicWrapperBase:
    @abstractmethod
    def __init__(
        self, close_callback: Callable, data_struct: PlottingStruct, Tw: float | None
    ):
        raise NotImplementedError

    @abstractmethod
    def animate_frame(self, ax_i: int, axis: Axes, dlogger: ClabDataLoggerReceiver):
        raise NotImplementedError

    @abstractmethod
    def close(self):
        raise NotImplementedError

    @abstractmethod
    def plt_update(self):
        raise NotImplementedError

    @abstractmethod
    def get_axes(self):
        raise NotImplementedError


class GraphicsWrapper(GraphicWrapperBase):
    figure: Figure
    axes: list[Axes]
    data_struct: PlottingStruct

    def __init__(
        self,
        close_callback: Callable,
        data_struct: PlottingStruct,
        Tw: float | None = None,
    ) -> None:
        self.figure = plt.figure()

        self.figure.canvas.mpl_connect('close_event', close_callback)

        self.create_subplots(data_struct)

        plt.ion()
        plt.show()

    def create_subplots(self, rx_data_format: PlottingStruct):
        res = []
        for i in range(len(rx_data_format)):
            res.append(
                self.figure.add_subplot(len(rx_data_format), 1, i + 1)  # type: ignore
            )
            plt.grid(True)

        self.axes = res

    def animate_frame(self, ax_i: int, axis: Axes, dlogger: ClabDataLoggerReceiver):
        """Define what to do in order to refresh the plot."""
        axis.clear()

        data_s = dlogger.data_struct[ax_i]
        x_data = dlogger.x_data_vector
        y_data = dlogger.y_data_vector[ax_i]

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

    def close(self):
        plt.close()

    def plt_update(self):
        plt.draw()
        plt.pause(1 / 1000)

    def get_axes(self):
        return self.axes


class QTGraphicsWrapper(GraphicWrapperBase):
    """Graphic wrapper class to use QT as a plotting backend."""

    figure: PlotWidget
    # window: GraphicsLayoutWidget
    window: GraphicsLayout
    axes: list[PlotItem]
    curves: list[PlotDataItem]
    app: QtWidgets.QApplication

    pens: list[QtGui.QPen] = [
        pg.mkPen(color=color, width=2)
        for color in [
            '#0072BD',
            '#D95319',
            '#EDB120',
            '#7E2F8E',
            '#77AC30',
            '#4DBEEE',
            '#A2142F',
            # 'red',
            # 'green',
            # 'blue'
        ]
    ]

    Tw: float

    def __init__(
        self,
        close_callback: Callable,
        data_struct: PlottingStruct,
        t_w: float | None = 10,
    ) -> None:
        self.app = pg.mkQApp('CLAB datalogger Receiver')
        img_path = os.path.abspath(os.path.dirname(__file__))
        img_path += '/icons/SPARCS_logo_v2_nobackground.png'
        self.app.setWindowIcon(QtGui.QIcon(img_path))

        self.window = pg.GraphicsLayoutWidget()

        assert t_w
        self.Tw = t_w

        self.create_subplots(data_struct)
        self.window.closeEvent = close_callback

        self.window.show()

    def create_subplots(self, rx_data_format: PlottingStruct):
        res = []
        datas = []
        for i, dat_format in enumerate(rx_data_format.subplots):
            axis = self.window.addPlot(
                row=i,
                col=0,
                rowspan=len(rx_data_format) - 1,
                colspan=1,
                title=dat_format.name,
            )

            axis.showGrid(True)
            axis.enableAutoRange(x=False, y=True)
            axis.setXRange(0, self.Tw)

            axis.addLegend(offset=(-10, 10), brush=pg.mkBrush('#22222255'))

            data_plots = [
                axis.plot(pen=self.pens[f_i], name=n.name)
                for f_i, n in enumerate(dat_format.fields)
            ]

            res.append(axis)
            datas.append(data_plots)

        self.axes = res
        self.curves = datas

    def plt_update(self):
        # TODO: check why CTRL+C does not raise properly exception here
        self.app.processEvents()

    def animate_frame(self, ax_i: int, axis: PlotItem, dlogger: ClabDataLoggerReceiver):
        """Define what to do in order to refresh the plot."""

        # print('x_size: ', len(dlogger.x_data_vector))

        x_data = dlogger.x_data_vector
        y_data = dlogger.y_data_vector[ax_i]

        # self.curves[ax_i].setData(x_data, y_data[0])

        fields = dlogger.data_struct.subplots[ax_i].fields

        for l_i in range(len(fields)):
            self.curves[ax_i][l_i].setData({'x': x_data, 'y': y_data[l_i]})

        axis.setXRange(max(0, x_data[-1] - self.Tw), max(self.Tw, x_data[-1]))

    def get_axes(self):
        return self.axes

    def close(self):
        return self.window.close()


class ClabDataLoggerReceiver:
    """Main class for managing the datalogging task."""

    autoscan_port: bool
    autoscan_port_pattern: str

    data_struct: PlottingStruct
    closed_queue: Queue[bool]

    graph_wrapper: GraphicWrapperBase

    t_0: float

    y_data_vector = []
    x_data_vector = []

    animator: Animator

    t_prev: float

    serial_conn: TurtlebotSerialConnector

    rx_queue: Queue[TimedPacketBase]

    max_time: float = -1

    def __init__(
        self,
        fps: int = 10,
        max_time: float = -1,
        t_w: float = 10,
        autoscan_port: bool | None = True,
        autoscan_port_pattern: str = 'STMicroelectronics',
    ) -> None:
        """Initialize the class."""
        if autoscan_port is None:
            autoscan_port = True
        self.autoscan_port = autoscan_port
        self.autoscan_port_pattern = autoscan_port_pattern

        self.data_struct = PlottingStruct.from_yaml_file()
        self.closed_queue = Queue()

        self.max_time = max_time

        self.t_0 = time.time()

        self.init_data_vectors()

        # self.graph_wrapper = GraphicsWrapper(
        self.graph_wrapper = QTGraphicsWrapper(
            self.on_fig_close, self.data_struct, t_w=t_w
        )

        self.animator = Animator(self.graph_wrapper.animate_frame, fps=fps)

        self.t_prev = self.currtime()

    def connect(self):
        """Establish connection."""
        self.serial_conn = TurtlebotSerialConnector(
            self.data_struct,
            autoscan_port=self.autoscan_port,
            autoscan_port_pattern=self.autoscan_port_pattern,
        )
        self.rx_queue = self.serial_conn.queue
        self.serial_conn.connect()

    def do_loop_while_true(self):
        """Execute `self.loop()` until exit is requested."""
        exit_requested = False

        while not exit_requested:
            exit_requested = self.loop()

        self.graph_wrapper.close()

    def do_loop_while_true_profiling(self, filename_out: str = 'profile_out.prof'):
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

        new = False
        while self.rx_queue.qsize() > 0:
            self.append_data(self.rx_queue.get_nowait())
            new = True

        if new:
            self.manage_packet()

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

    def currtime(self) -> float:
        """Return time elapsed since initialization."""
        return time.time() - self.t_0

    def init_data_vectors(self) -> None:
        """Initialize `self.y_data_vector` according to `self.data_struct`."""
        self.y_data_vector = [[] for _ in range(len(self.data_struct))]

        for y_i in range(len(self.data_struct)):
            self.y_data_vector[y_i] = [[] for _ in range(len(self.data_struct[y_i]))]

    def append_data(self, packet: TimedPacketBase):
        """Appends the new packet to the data"""

        self.x_data_vector.append(packet.time)

        for ax_i in range(len(self.data_struct)):
            for i, data_aa in enumerate(packet.data[ax_i]):
                self.y_data_vector[ax_i][i].append(data_aa)

    def manage_packet(self) -> None:
        """
        Manage a packet received from serial reader queue.

        It is expected that the packet is a subclass of `TimedPacketBase`.


        """
        axes = self.graph_wrapper.get_axes()
        for ax_i, axis in enumerate(axes):
            self.animator.animate(ax_i, axis, self, upd_counter=(ax_i) == len(axes) - 1)

        self.graph_wrapper.plt_update()


def save_data(datalogger: ClabDataLoggerReceiver, mat_filename: str = 'out_data.mat'):
    """Save the data of datalogger."""
    save_data_in = ''

    try:
        save_data_in = input('Do you want to save the data? [Y/n]')
    except KeyboardInterrupt:
        # Treat `CTRL+C` as a no
        save_data_in = 'n'

    if save_data_in not in 'Y\n':
        print('Exiting without saving data')
        sys.exit(0)

    file_dict = {
        'turtlebot_data': {'time': datalogger.x_data_vector, 'field_names': {}}
    }

    for idx, (sp, y_data) in enumerate(
        zip(datalogger.data_struct.subplots, datalogger.y_data_vector)
    ):
        name = sp.name

        if name is None:
            name = f'data_struct_{idx}'

        file_dict['turtlebot_data'][name] = y_data

        file_dict['turtlebot_data']['field_names'][name] = [f.name for f in sp.fields]

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
