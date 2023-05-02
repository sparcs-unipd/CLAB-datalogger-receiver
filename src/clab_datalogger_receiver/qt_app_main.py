from __future__ import annotations

import os
from queue import Queue
from typing import Callable, Tuple, Type

from datetime import datetime
import qdarktheme

from pyqtgraph import GraphicsLayoutWidget as pg_GraphicsLayoutWidget

from numpy import array as np_array
from numpy import concatenate as np_concatenate
from numpy import ndarray as np_ndarray

from PySide6.QtCore import QObject, QThread
from PySide6.QtCore import Signal as pyqtSignal
from PySide6.QtCore import Slot as pyqtSlot
from PySide6.QtGui import QIcon, QPen
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from serial import Serial
from serial.tools.list_ports_common import ListPortInfo

from .base.common import resource_path
from .gui.base_widgets import BoxButtonsWidget
from .gui.colors import get_background_brush, get_graphs_pens
from .received_structure import PlottingStruct
from .saver import save_data_raw
from .serial_communication.communication import (
    ManualPortTurtlebotSerialConnector,
)
from .serial_communication.packets import TimedPacketBase
from .simple_console_main_classes import (
    SubplotsReferences,
)
from .widgets import TopMenuWidget


class DequeueWorker(QObject):
    got_new_packages = pyqtSignal(object)

    rx_queue: Queue[TimedPacketBase]
    working: bool

    loopdone = pyqtSignal()
    finished = pyqtSignal()

    def __init__(self, rx_queue: Queue[TimedPacketBase]):
        super().__init__()

        self.rx_queue = rx_queue
        self.working = True
        # self.got_new_packages
        # self.started.emit()

    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''
        # debugpy.debug_this_thread()

        while self.working:
            new = False
            data = []
            while not self.rx_queue.empty():
                data.append(self.rx_queue.get(block=False))
                new = True
            if new:
                self.got_new_packages.emit(data)

        self.finished.emit()

    # def loop(self):
    #     self.manage_packet()

    # def append_data(self, packet: TimedPacketBase):
    #     """Appends the new packet to the data"""

    #     self.x_data_vector.append(packet.time)

    #     for ax_i in range(len(self.data_struct)):
    #         for i, data_aa in enumerate(packet.data[ax_i]):
    #             self.y_data_vector[ax_i][i].append(data_aa)


class DequeueAndPlotterWorker(QObject):
    # update_axis = pyqtSignal(tuple[PlotDataItem, dict, PlotItem])
    update_axis = pyqtSignal(tuple)
    got_new_packages = pyqtSignal(object)
    got_new_data = pyqtSignal(object, object)
    update_ui = pyqtSignal()

    rx_queue: Queue[TimedPacketBase]
    working: bool

    loopdone = pyqtSignal()
    finished = pyqtSignal()

    subplots_ref: SubplotsReferences
    data_struct: PlottingStruct

    time_window: float

    def __init__(
        self,
        rx_queue: Queue[TimedPacketBase],
        subplots_ref: SubplotsReferences,
        time_window: float = 10,
    ):
        super().__init__()

        self.rx_queue = rx_queue
        self.data_struct = subplots_ref.data_struct
        self.subplots_ref = subplots_ref

        self.init_data()
        self.working = True
        self.time_window = time_window
        # self.got_new_packages
        # self.started.emit()

    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''
        while self.working:
            new = False
            packages = []

            while not self.rx_queue.empty():
                packages.append(self.rx_queue.get(block=False))
                new = True

            if not new:
                self.update_ui.emit()
                continue

            # self.got_new_packages.emit(packages)

            x_new, y_new = self.get_data_from_packages(packages)

            self.got_new_data.emit(x_new, y_new)

            # self.update_axis.emit()

            # for package in packages:
            #     self.x_data_vector.append(package.time)
            #     for ax_i in range(len(self.data_struct)):
            #         for i, data_aa in enumerate(package.data[ax_i]):
            #             self.y_data_vector[ax_i][i].append(data_aa)

            # x_data = self.x_data_vector
            # for ax_i, axis in enumerate(self.subplots_ref.axes):
            #     y_data = self.y_data_vector[ax_i]
            #     curve = self.subplots_ref.curves[ax_i]
            #     self.update_axis.emit((curve, x_data, y_data, axis))

    def init_data(self) -> None:
        """Initialize `self.y_data_vector` according to `self.data_struct`."""

        assert self.data_struct, (
            'self.data_struct must be assigned ' ' before initializing data'
        )

        self.x_data_vector = []
        self.y_data_vector = [
            [[] for _ in range(len(sp))] for sp in self.data_struct.subplots
        ]

    def get_data_from_packages(
        self, packages: list[TimedPacketBase]
    ) -> Tuple[list, list[list]]:
        x = [p.time for p in packages]

        y = [[[] for _ in range(len(sp))] for sp in self.data_struct.subplots]

        num_subplots: int = len(self.data_struct)

        for package in packages:
            for ax_i in range(num_subplots):
                for i, data_aa in enumerate(package.data[ax_i]):
                    y[ax_i][i].append(data_aa)

        for y_i, yy in enumerate(y):
            for y_ii, yyy in enumerate(yy):
                y[y_i][y_ii] = np_array(yyy)  # type: ignore

        return x, y


class MainWindow(QMainWindow):
    connected: pyqtSignal

    app: QApplication

    close_callback: Callable

    selected_port: ListPortInfo | None = None

    pens: list[QPen] = get_graphs_pens()

    legend_background_brush = get_background_brush()

    rx_worker: DequeueAndPlotterWorker
    rx_thread: QThread

    subplots_reference: SubplotsReferences
    serial_connection: ManualPortTurtlebotSerialConnector | None

    def __init__(
        self,
        data_struct: PlottingStruct,
        time_window: float,
        app: QApplication,
        min_plot_points: int = 2000,
        max_plot_points: int = 4000,
    ) -> None:
        super().__init__()

        self.data_struct = data_struct
        self.max_plot_points = max_plot_points
        self.min_plot_points = min_plot_points

        self.time_window = time_window
        self.app = app

        self.init_data_cache()
        self.init_data_vectors()

        self.create_window()
        self.create_subplots()

        # Put a size to the queue, so
        self.rx_queue = Queue(maxsize=100)

        self.rx_thread = QThread()

        self.rx_worker = DequeueAndPlotterWorker(
            self.rx_queue, self.subplots_reference
        )

        self.rx_thread.setObjectName('test thread')

        self.rx_thread.started.connect(self.rx_worker.run)
        self.rx_worker.finished.connect(self.rx_thread.quit)
        self.rx_worker.finished.connect(self.rx_worker.deleteLater)
        self.rx_thread.finished.connect(self.rx_thread.deleteLater)

        self.rx_worker.got_new_data.connect(self.append_data)

        self.rx_worker.moveToThread(self.rx_thread)

        # Start the dequeuing thread.
        self.rx_thread.start()

    def closeEvent(self, event):
        # Stop the worker and the thread
        self.rx_worker.working = False
        self.rx_thread.exit()

        super().closeEvent(event)

    x_data: np_ndarray
    y_data: list[list[np_ndarray]]

    def append_data(self, x_new: np_ndarray, y_new: list[list[np_ndarray]]):
        self.x_data = np_concatenate((self.x_data, x_new))

        for y_i, (y_s, y_n) in enumerate(zip(self.y_data, y_new)):
            for y_ii, (y_s_i, y_n_i) in enumerate(zip(y_s, y_n)):
                self.y_data[y_i][y_ii] = np_concatenate((y_s_i, y_n_i))

        self.update_axis()

        self.do_cache_if_needed()

    def do_cache_if_needed(self):
        if self.x_data.size > self.max_plot_points:
            self.do_cache()

    def do_cache(self):
        self.x_data_vectors = np_concatenate(
            (self.x_data_vectors, self.x_data[: self.min_plot_points])
        )
        self.x_data = self.x_data[-self.min_plot_points :]

        for y_i, y_s in enumerate(self.y_data):
            for y_ii, y_s_i in enumerate(y_s):
                self.y_data_vectors[y_i][y_ii] = np_concatenate(
                    (
                        self.y_data_vectors[y_i][y_ii],
                        y_s_i[: self.min_plot_points],
                    )
                )
                self.y_data[y_i][y_ii] = self.y_data[y_i][y_ii][
                    -self.min_plot_points :
                ]

    def init_data_cache(self) -> None:
        """Initialize `self.y_data_vector` according to `self.data_struct`."""
        self.x_data_vectors = np_array([])

        self.y_data_vectors = [
            [np_array([]) for _ in range(len(sp))]
            for sp in self.data_struct.subplots
        ]

    def init_data_vectors(self) -> None:
        """Initialize `self.y_data_vector` according to `self.data_struct`."""
        self.x_data = np_array([])

        self.y_data = [
            [np_array([]) for _ in range(len(sp))]
            for sp in self.data_struct.subplots
        ]

    def update_axis(self):
        axes = self.subplots_reference.axes
        curves = self.subplots_reference.curves

        for ax_i, axis in enumerate(axes):
            for l_i, curve_i in enumerate(curves[ax_i]):
                curve_i.setData(x=self.x_data, y=self.y_data[ax_i][l_i])

            axis.setXRange(
                max(0, self.x_data[-1] - self.time_window),
                max(self.time_window, self.x_data[-1]),
            )

    # t_0: float | datetime | None = None
    t_interruption: float | datetime | None = None
    p_type: Type[TimedPacketBase] | None = None

    def get_time_after_reconnection(self):
        if self.t_interruption is None:
            return None

        # assert self.p_type is not None

        # res = self.p_type.from_data(None).get_time()
        res = self.t_interruption
        # print('t_after_reconnection: ', res)
        return res

    def calc_interruption_time(self):
        """
        Return the time of the interruption of the connection.

        The return type depends on the the packet time type
        """

        assert self.serial_connection is not None

        t_0 = self.serial_connection.get_t_0()

        return t_0

    def connect(self, connection: Serial):
        """Connects to the serial port."""

        self.serial_connection = ManualPortTurtlebotSerialConnector(
            self.data_struct,
            serial=connection,
            existing_queue=self.rx_queue,
            t_0=self.get_time_after_reconnection(),
        )

        self.serial_connection.connect()

    def disconnect(self):
        """Close the serial connection."""
        assert self.serial_connection is not None
        print('Disconnecting.')

        self.t_interruption = self.calc_interruption_time()
        self.serial_connection.close()

        self.serial_connection = None

        return True

    def create_window(self):
        """Opens Qt window."""

        # img_path = os.path.abspath(os.path.dirname(__file__))
        # img_path += '/icons/SPARCS_logo_v2_nobackground.png'
        img_path_folder = os.path.abspath(os.path.dirname(__file__))

        # img_path += '/icons/SPARCS_logo_v2_nobackground.png'
        img_path = './icons/SPARCS_logo_v2_nobackground.png'
        img_path = resource_path(img_path, img_path_folder)
        print(img_path)
        qdarktheme.setup_theme()

        self.setWindowIcon(QIcon(img_path))
        self.setWindowTitle("SPARCS datalogger receiver")

        self.graph_widget = pg_GraphicsLayoutWidget()

        layout = QVBoxLayout()
        self.main_layout = layout

        layout.addWidget(
            TopMenuWidget(
                on_select_fcn=self.sel_changed,
                on_connect_fcn=self.port_selected,
                disconnection_requested=self.disconnect,
            )
        )

        layout.addWidget(self.graph_widget)
        layout.addWidget(
            BoxButtonsWidget(
                names=['Save', 'Exit'], fcns=[self.save, self.close]
            )
        )

        self.main_widget = QWidget()
        self.main_widget.setLayout(layout)

        self.setCentralWidget(self.main_widget)

    def create_subplots(self):
        """Create the subplots and data items based on the data struct \
              given as parameter."""
        rx_data_format = self.data_struct
        axes = []
        datas = []
        for i, dat_format in enumerate(rx_data_format.subplots):
            axis = self.graph_widget.addPlot(
                row=i,
                col=0,
                title=dat_format.name,
                enableMouse=False,
            )

            axis.showGrid(True)
            # axis.enableAutoRange(x=False, y=True)
            axis.setMouseEnabled(x=False, y=False)
            axis.enableAutoRange(x=False, y=True)
            axis.setXRange(0, self.time_window)
            # axis
            axis.addLegend(
                offset=(-10, 10),
                brush=self.legend_background_brush,
            )

            data_plots = [
                axis.plot(pen=self.pens[f_i], name=n.name)
                for f_i, n in enumerate(dat_format.fields)
            ]

            axes.append(axis)
            datas.append(data_plots)

        self.subplots_reference = SubplotsReferences(
            self.data_struct, axes, datas
        )

    def sel_changed(self, selected_port: ListPortInfo):
        # print('sel changed in MainWindow')
        print(selected_port)

        if (
            self.selected_port is not None
            and self.selected_port.device == selected_port.device
        ):
            return

        # Else selection changed prev selected port.

    def port_selected(self, serial_connection: Serial):
        print('Connected to serial', serial_connection.port)
        self.connect(serial_connection)

    def save(self):
        self.do_cache()
        # print('saving requested.')
        save_data_raw(
            self.data_struct,
            self.x_data_vectors,
            self.y_data_vectors,
        )


def get_app_and_window(
    data_struct,
    time_window=10,
    sys_argv=[],
):
    app = QApplication(sys_argv)
    window = MainWindow(data_struct, time_window, app)

    return app, window
