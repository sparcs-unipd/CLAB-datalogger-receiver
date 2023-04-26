"""
This module is a collection of classes used by the first version of the app.

Author:
    Marco Perin

"""
from __future__ import annotations

import os
import time
from abc import abstractmethod
from dataclasses import dataclass
from queue import Empty as q_Empty
from queue import Queue
from typing import Callable

import pyqtgraph as pg
from PyQt6 import QtGui, QtWidgets
from pyqtgraph import GraphicsLayout, PlotDataItem, PlotItem, PlotWidget

from .animator import Animator
from .received_structure import PlottingStruct
from .serial_communication.communication import TurtlebotSerialConnector
from .serial_communication.packets import TimedPacketBase

from .gui.colors import get_graphs_pens, get_background_brush


class GraphicWrapperBase:
    @abstractmethod
    def __init__(
        self,
        close_callback: Callable,
        data_struct: PlottingStruct,
        Tw: float | None,
    ):
        raise NotImplementedError

    @abstractmethod
    def animate_frame(self, ax_i: int, axis, dlogger: ClabDataLoggerReceiver):
        raise NotImplementedError

    @abstractmethod
    def close(self):
        raise NotImplementedError

    @abstractmethod
    def open_window(self):
        raise NotImplementedError

    @abstractmethod
    def plt_update(self):
        raise NotImplementedError

    @abstractmethod
    def get_axes(self):
        raise NotImplementedError


@dataclass
class SubplotsReferences:
    data_struct: PlottingStruct
    axes: list[PlotItem]
    curves: list[list[PlotDataItem]]


def qt_animate_frame(
    curves: list[list[PlotDataItem]],
    time_window: float,
    ax_i: int,
    axis: PlotItem,
    x_data: list,
    y_data: list,
    data_struct: PlottingStruct,
):
    """Refresh the plot."""

    fields = data_struct.subplots[ax_i].fields

    for l_i in range(len(fields)):
        curves[ax_i][l_i].setData({'x': x_data, 'y': y_data[l_i]})

    axis.setXRange(
        max(0, x_data[-1] - time_window),
        max(time_window, x_data[-1]),
    )


def qt_animate_frame_with_ref(
    sub_ref: SubplotsReferences,
    # curves: list[list[PlotDataItem]],
    time_window: float,
    ax_i: int,
    axis: PlotItem,
    x_data: list,
    y_data: list,
):
    fields = sub_ref.data_struct.subplots[ax_i].fields

    for l_i in range(len(fields)):
        sub_ref.curves[ax_i][l_i].setData({'x': x_data, 'y': y_data[l_i]})

    axis.setXRange(
        max(0, x_data[-1] - time_window),
        max(time_window, x_data[-1]),
    )


class QTGraphicsWrapper(GraphicWrapperBase):
    """Graphic wrapper class to use QT as a plotting backend."""

    data_struct: PlottingStruct
    close_callback: Callable

    figure: PlotWidget
    # window: GraphicsLayoutWidget
    window: GraphicsLayout
    axes: list[PlotItem]
    curves: list[list[PlotDataItem]]
    app: QtWidgets.QApplication

    pens: list[QtGui.QPen] = get_graphs_pens()
    legend_backgrou_brush = get_background_brush()

    time_window: float

    def __init__(
        self,
        close_callback: Callable,
        data_struct: PlottingStruct,
        t_w: float | None = 10,
    ) -> None:
        assert t_w
        self.time_window = t_w
        self.data_struct = data_struct
        self.close_callback = close_callback

    def create_subplots(self, rx_data_format: PlottingStruct):
        """Create the subplots and data items based on the data struct \
              given as parameter."""

        res = []
        datas = []
        for i, dat_format in enumerate(rx_data_format.subplots):
            axis = self.window.addPlot(
                row=i,
                col=0,
                title=dat_format.name,
            )

            axis.showGrid(True)
            axis.enableAutoRange(x=False, y=True)
            axis.setXRange(0, self.time_window)

            axis.addLegend(offset=(-10, 10), brush=self.legend_backgrou_brush)

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

    def animate_frame(
        self,
        ax_i: int,
        axis: PlotItem,
        dlogger: ClabDataLoggerReceiver,
    ):
        """Define what to do in order to refresh the plot."""

        qt_animate_frame(
            self.curves,
            self.time_window,
            ax_i,
            axis,
            dlogger.x_data_vector,
            dlogger.y_data_vector[ax_i],
            dlogger.data_struct,
        )

    def open_window(self):
        """Opens Qt window."""
        self.app = pg.mkQApp('CLAB datalogger receiver')
        img_path = os.path.abspath(os.path.dirname(__file__))
        img_path += '/icons/SPARCS_logo_v2_nobackground.png'
        self.app.setWindowIcon(QtGui.QIcon(img_path))

        self.window = pg.GraphicsLayoutWidget()

        self.create_subplots(self.data_struct)
        self.window.closeEvent = self.close_callback

        self.window.show()

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
        self.graph_wrapper.open_window()

    def do_loop_while_true(self):
        """Execute `self.loop()` until exit is requested."""
        exit_requested = False

        while not exit_requested:
            exit_requested = self.loop()

        self.graph_wrapper.close()

    def do_loop_while_true_profiling(
        self, filename_out: str = 'profile_out.prof'
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
            self.y_data_vector[y_i] = [
                [] for _ in range(len(self.data_struct[y_i]))
            ]

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
            self.animator.animate(
                ax_i, axis, self, upd_counter=(ax_i) == len(axes) - 1
            )

        self.graph_wrapper.plt_update()
