"""Main widgets for the gui of the application."""
from typing import Callable

from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QPushButton,
    QWidget,
)

from serial import Serial, SerialException
from serial.tools.list_ports_common import ListPortInfo

from .serial_communication._utils import (
    get_serial_port_list,
    get_serial_port_text,
    select_serial_port_index,
)
from .serial_communication.communication import get_serial

from qdarktheme import load_stylesheet


class TopMenuWidget(QWidget):
    """
    Graphic holder of the top bar.

    Pass a callback on the constructor to be notified when \
        the serial port selection changes.
    """

    on_select: Callable[[ListPortInfo], None]
    on_connect: Callable[[Serial], None]

    disconnection_requested: Callable[[], bool]

    combo_w: QComboBox
    available_ports: list[ListPortInfo]

    selected_serial: ListPortInfo | None = None
    connected_serial: Serial | None = None
    is_connected: bool = False

    SCAN_PATTERN = 'STMicroelectronics'

    connect_btn: QPushButton
    refresh_btn: QPushButton

    def __init__(
        self,
        on_select_fcn: Callable[[ListPortInfo], None],
        on_connect_fcn: Callable[[Serial], None],
        disconnection_requested: Callable[[], bool],
    ) -> None:
        super().__init__()

        self.on_select = on_select_fcn
        self.on_connect = on_connect_fcn
        self.disconnection_requested = disconnection_requested

        layout = QHBoxLayout()

        self.combo_w = QComboBox()

        # self.combo_w.currentIndexChanged.connect(self.selection_changed)
        self.combo_w.activated.connect(self.selection_changed)

        layout.addWidget(self.combo_w, 3)
        btn = QPushButton('Refresh list')
        btn.clicked.connect(self.refresh_opts)
        layout.addWidget(btn, 1)
        self.refresh_btn = btn
        btn = QPushButton('Connect')
        btn.clicked.connect(self.try_connection)
        layout.addWidget(btn, 1)
        self.connect_btn = btn

        self.refresh_opts()

        self.setLayout(layout)

        self.original_stylesheet = load_stylesheet()

    def find_and_select_serial_port(self, pattern):
        """Finds a serial port and selects it if it matches the pattern."""

        idx = select_serial_port_index(
            self.available_ports,
            scan_pattern=pattern,
        )
        if idx is None:
            return False

        return self.select_port(idx)

    def refresh_opts(self):
        """Clear and refreshes the options in the combo box."""

        print('Refreshing ports.')
        self.available_ports = get_serial_port_list()
        self.combo_w.clear()
        self.combo_w.addItems(
            [
                get_serial_port_text(p)
                for p in self.available_ports
                if get_serial_port_text(p)
            ]
        )

        if self.selected_serial is None:
            # We probably refresh to find a new connection,
            #   so try to connect to it
            if self.find_and_select_serial_port(self.SCAN_PATTERN):
                print('Found serial port automatically!')
            else:
                print(
                    'Serial not automatically found. Selecting first available'
                )
                self.select_port(0)

    def select_port(self, idx) -> bool:
        """Return true if a selection is made."""
        if idx is None:
            return False

        self.combo_w.setCurrentIndex(idx)
        self.selection_changed(idx)

        return True

    def connected(self, serial_connection: Serial):
        self.connect_btn.setText('Disconnect')
        # self.connect_btn.setText('Connected')
        # self.connect_btn.setDisabled(True)
        self.connect_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: #333 }"
        )

        self.is_connected = True

        self.on_connect(serial_connection)
        self.connect_btn.clicked.disconnect(self.try_connection)
        self.connect_btn.clicked.connect(self.try_disconnection)

    def try_disconnection(self):
        """Try disconnecting from the serial port."""
        if self.disconnection_requested():
            self.disconnected()

    def disconnected(self):
        """Gets called when succesfully disconnected from serial."""
        self.connect_btn.setText('Connect')
        # self.connect_btn.setDisabled(True)

        # self.connect_btn.setPalette(self.original_palette)
        self.connect_btn.setStyleSheet(self.original_stylesheet)

        self.is_connected = False

        self.connect_btn.clicked.connect(self.try_connection)
        self.connect_btn.clicked.disconnect(self.try_disconnection)

    def try_connection(self):
        """
        Try connecting to the selected serial port.

        Invoke callback if connection is succesful.

        """
        assert self.selected_serial is not None
        try:
            serial_connection = get_serial(self.selected_serial.device)
            self.connected(serial_connection)

        except SerialException:
            print('Error connecting!')

    def selection_changed(self, idx):
        """Select the new port and notify callbacks."""

        print('sel changed')
        self.selected_serial = self.available_ports[idx]
        self.on_select(self.selected_serial)
