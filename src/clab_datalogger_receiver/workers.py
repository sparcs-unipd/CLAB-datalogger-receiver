from queue import Queue
from typing import Tuple

from numpy import array as np_array

from PySide6.QtCore import QObject
from PySide6.QtCore import Signal as pyqtSignal
from PySide6.QtCore import Slot as pyqtSlot
from PySide6.QtWidgets import QApplication

from .received_structure import PlottingStruct
from .serial_communication.packets import TimedPacketBase
from .simple_console_main_classes import (
    SubplotsReferences,
)

import time


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

            QApplication.processEvents()

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

    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''
        while self.working:
            new = False
            packages = []

            try:
                # Block for a short time to wait for new data
                package = self.rx_queue.get(block=True, timeout=0.1)
                packages.append(package)
                new = True

                # Drain the rest of the queue
                while not self.rx_queue.empty():
                    packages.append(self.rx_queue.get(block=False))
            except Exception:
                pass  # Timeout occurred, no data available

            QApplication.processEvents()

            if not new:
                # Introduce a small sleep to avoid busy-waiting
                time.sleep(0.01)
                continue

            x_new, y_new = self.get_data_from_packages(packages)

            self.got_new_data.emit(x_new, y_new)

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
