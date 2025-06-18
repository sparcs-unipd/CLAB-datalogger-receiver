"""
Module that manages the main application window.
"""
from __future__ import annotations

import os
import sys

from queue import Queue
from typing import Callable, Type

from datetime import datetime
import qdarktheme

from pyqtgraph import (
    GraphicsLayoutWidget as pg_GraphicsLayoutWidget,
    PlotDataItem,
)
from numpy import array as np_array
from numpy import concatenate as np_concatenate
from numpy import ndarray as np_ndarray
from numpy.typing import NDArray

from PySide6.QtCore import QThread
from PySide6.QtCore import Signal as pyqtSignal
from PySide6.QtGui import QIcon, QPen
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QMessageBox,
    QFileDialog,
)
from serial import Serial
from serial.tools.list_ports_common import ListPortInfo


from .base.common import resource_path
from .gui.base_widgets import BoxButtonsWidget
from .gui.colors import get_background_brush, get_graphs_pens
from .received_structure import PlottingStruct
from .saver import save_as_mat, save_as_pandas_dataframe
from .serial_communication.communication import (
    ManualPortTurtlebotSerialConnector,
)
from .serial_communication.packets import TimedPacketBase
from .simple_console_main_classes import (
    SubplotsReferences,
)
from .udp_communication.types import UDPData
from .widgets import TopMenuWidget
from .workers import DequeueAndPlotterWorker

from .struct_editor import StructConfigEditor


class MainWindow(QMainWindow):
    """Main Application window."""

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

    data_saved: bool = True
    # Vectors containing the data seen in the plots
    x_data: np_ndarray
    y_data: list[list[np_ndarray]]
    # y_data: list[list[Any]]

    # Vectors used to cache the entire data, later saved in the .mat file
    x_data_vectors: np_ndarray
    y_data_vectors: list[list[np_ndarray]]
    # y_data_vectors: list[list[Any]]

    # Time of connection interruption
    t_interruption: float | datetime | None = None
    # Package type
    p_type: Type[TimedPacketBase] | None = None

    def __init__(
        self,
        data_struct: PlottingStruct,
        time_window: float,
        app: QApplication,
        min_plot_points: int = 2000,
        max_plot_points: int = 3000,
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

        # Put a size to the queue, so an error is risen if the dequeuing
        #   is not fast enough
        self.rx_queue = Queue(maxsize=100)

        self.rx_thread = QThread()

        self.rx_worker = DequeueAndPlotterWorker(
            self.rx_queue, self.subplots_reference
        )

        self.rx_thread.setObjectName('Dequeuer thread')

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

    def append_data(self, x_new: np_ndarray, y_new: list[list[np_ndarray]]):
        """
        Append new data to the plotted vectors.

        Used when new data arrives from the communication channel.
        """
        self.data_saved = False
        self.x_data = np_concatenate((self.x_data, x_new))

        for y_i, (y_s, y_n) in enumerate(zip(self.y_data, y_new)):
            for y_ii, (y_s_i, y_n_i) in enumerate(zip(y_s, y_n)):
                self.y_data[y_i][y_ii] = np_concatenate((y_s_i, y_n_i))

        self.update_axis()

        self.do_cache_if_needed()

    def do_cache_if_needed(self):
        """Cache the data vectors, if needed."""

        if self.x_data.size > self.max_plot_points:
            self.do_cache()

    def do_cache(self):
        """
        Cache the plotted data to a larger vector.

        Used to keep the plotted data smaller, thus lighter
        """
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
        """Update all the axis according to `self.x_data` and `self.y_data`."""
        axes = self.subplots_reference.axes
        curves = self.subplots_reference.curves

        for ax_i, axis in enumerate(axes):
            for l_i, curve_i in enumerate(curves[ax_i]):
                curve_i.setData(x=self.x_data, y=self.y_data[ax_i][l_i])
            if len(self.x_data) == 0:
                # If no data, set the x range to 0
                axis.setXRange(0, self.time_window)
            else:
                axis.setXRange(
                    max(0, self.x_data[-1] - self.time_window),
                    max(self.time_window, self.x_data[-1]),
                )

    def get_time_after_reconnection(self):
        """
        Get the time after a reconnection occurs.

        Used to keep data consistent after a reconnection.
        """
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

    def connect(self, connection: Serial | UDPData):
        """Connects to the serial port."""

        self.serial_connection = ManualPortTurtlebotSerialConnector(
            self.data_struct,
            connection=connection,
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
                names=['Edit Config', 'Save', 'Exit'], fcns=[self.open_struct_editor, self.save, self.close]
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
            axis: PlotDataItem = self.graph_widget.addPlot(
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
            axis.setDownsampling(True)
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
        print(selected_port)
        # TODO: Why was this function here?

        # if self.selected_port is not None and is_curr_device:
        # is_curr_device = self.selected_port.device == selected_port.device
        #     return

        # Else selection changed prev selected port.

    def port_selected(self, connection: Serial | UDPData):
        """
        Create the connection channel after the channel selection.

        Depending on the connection channel, this happens when:
        - serial.Serial: selecting the port and pressing "Serial Connect".
        - UDPData : the IP:PORT is insertede and pressing "Network Connect".
        """
        if isinstance(connection, Serial):
            print('Connected to serial', connection.port)
        else:
            print('Connected to UDP', (connection.ip, connection.port))

        self.connect(connection)

    def close(self, force: bool = False):
        if self.data_saved or force:
            super().close()
        else:
            close_btn = QMessageBox.StandardButton.No
            cancel_btn = QMessageBox.StandardButton.Cancel
            save_btn = QMessageBox.StandardButton.Yes
            warning_text = (
                "You are about to exit without saving all the data.\n"
                "Do you want to save before closing?"
            )
            ret = QMessageBox.warning(
                self,
                "Attention, you could lose data",
                warning_text,
                save_btn | cancel_btn | close_btn,
                save_btn,
            )

            if ret == save_btn:
                self.save()
                self.close(True)
            elif ret == close_btn:
                self.close(True)

    def save(self):
        """Save all the captured data to a `.mat` file."""
        self.do_cache()

        if self.x_data_vectors.size == 0:
            QMessageBox.information(self, "No Data", "There is no data to save.")
            return
        
        file_dialog = QFileDialog(self)
        file_dialog.setAcceptMode(QFileDialog.AcceptSave)
        file_dialog.setWindowTitle("Save Data")
        
        # Suggest initial directory (User's Documents or Home folder)
        docs_dir = os.path.join(os.path.expanduser("~"), "Documents")
        default_save_dir = docs_dir if os.path.isdir(docs_dir) else os.path.expanduser("~")
        file_dialog.setDirectory(default_save_dir)
        
        default_filename = f"sparcs_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        file_dialog.selectFile(default_filename) 

        filters = [
            "MAT files (*.mat)",
            "CSV files (*.csv)",
            "Pandas Parquet files (*.parquet)",
            "Pandas Pickle files (*.pkl)",
        ]
        file_dialog.setNameFilters(filters)
        #file_dialog.setDefaultSuffix("mat") # Default for typing name without extension

        if file_dialog.exec():
            selected_file_path = file_dialog.selectedFiles()[0]
            selected_filter = file_dialog.selectedNameFilter()
            
            try:
                print(f"Saving data to {selected_file_path} with filter {selected_filter}")
                if "MAT files" in selected_filter:
                    selected_file_path += ".mat" if not selected_file_path.endswith(".mat") else ""
                    save_as_mat(
                        self.data_struct,
                        self.x_data_vectors,
                        self.y_data_vectors,
                        mat_filename=selected_file_path,
                    )
                elif "CSV files" in selected_filter:
                    selected_file_path += ".csv" if not selected_file_path.endswith(".csv") else ""
                    save_as_pandas_dataframe(
                        self.data_struct,
                        self.x_data_vectors,
                        self.y_data_vectors,
                        filepath=selected_file_path,
                        file_format='csv'
                    )
                elif "Pandas Parquet files" in selected_filter:
                    selected_file_path += ".parquet" if not selected_file_path.endswith(".parquet") else ""
                    save_as_pandas_dataframe(
                        self.data_struct,
                        self.x_data_vectors,
                        self.y_data_vectors,
                        filepath=selected_file_path,
                        file_format='parquet'
                    )
                elif "Pandas Pickle files" in selected_filter:
                    selected_file_path += ".pkl" if not selected_file_path.endswith(".pkl") else ""
                    save_as_pandas_dataframe(
                        self.data_struct,
                        self.x_data_vectors,
                        self.y_data_vectors,
                        filepath=selected_file_path,
                        file_format='pickle'
                    )
                else: # Should not happen with defined filters
                    QMessageBox.warning(self, "Unknown Filter", "Selected file type filter is not recognized.")
                    self.data_saved = False 
                    return

                self.data_saved = True
                QMessageBox.information(self, "Success", f"Data saved to {selected_file_path}")

            except Exception as e:
                self.data_saved = False 
                QMessageBox.critical(self, "Error Saving File", 
                                     f"Could not save file '{selected_file_path}':\n{type(e).__name__}: {e}")
        else:
            # User cancelled the dialog
            print("Save operation cancelled by user.")
            # self.data_saved status remains unchanged from before save attempt


    def open_struct_editor(self):
        yaml_path = "struct_cfg.yaml"  # FIXME: Make this configurable or use a default path
        dlg = StructConfigEditor(yaml_path, self)
        dlg.yaml_saved.connect(self.on_struct_yaml_saved)  # Connect signal
        dlg.exec()


    def on_struct_yaml_saved(self):
        # Reload YAML and update UI
        self.data_struct = PlottingStruct.from_yaml_file("struct_cfg.yaml")
        self.init_data_cache()
        self.init_data_vectors()

        # Explicitly clear existing plots from the graphics layout
        if hasattr(self, 'graph_widget') and self.graph_widget is not None:
            self.graph_widget.clear()
            # self.subplots_reference will be updated by create_subplots

        self.create_subplots()  # Re-creates plots and updates self.subplots_reference
        self.update_axis()
        self.rx_worker.update_plot_structs(self.subplots_reference)


def get_app_and_window(
    data_struct,
    time_window=10,
    sys_argv=None,
):
    """
    Create the QApplication and QMainWindow for the application.

    Called when invoking the module's __main__ script.
    """
    if sys_argv:
        app = QApplication(sys_argv)
    else:
        app = QApplication()
    window = MainWindow(data_struct, time_window, app)

    return app, window
