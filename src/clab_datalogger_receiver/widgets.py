"""Main widgets for the gui of the application."""
from typing import Callable

from PyQt6.QtWidgets import (
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


class TopMenuWidget(QWidget):
    """
    Graphic holder of the top bar.

    Pass a callback on the constructor to be notified when \
        the serial port selection changes.
    """

    on_select: Callable[[ListPortInfo], None]
    on_connect: Callable[[Serial], None]

    combo_w: QComboBox
    available_ports: list[ListPortInfo]

    selected_serial: ListPortInfo | None = None

    SCAN_PATTERN = 'STMicroelectronics'

    def __init__(
        self,
        on_select_fcn: Callable[[ListPortInfo], None],
        on_connect_fcn: Callable[[Serial], None],
    ) -> None:
        super().__init__()

        self.on_select = on_select_fcn
        self.on_connect = on_connect_fcn

        layout = QHBoxLayout()

        self.combo_w = QComboBox()

        # self.combo_w.currentIndexChanged.connect(self.selection_changed)
        self.combo_w.activated.connect(self.selection_changed)

        layout.addWidget(self.combo_w, 3)
        btn = QPushButton('Refresh list')
        btn.clicked.connect(self.refresh_opts)
        layout.addWidget(btn, 1)
        btn = QPushButton('Connect')
        btn.clicked.connect(self.try_connection)
        layout.addWidget(btn, 1)

        self.refresh_opts()

        self.setLayout(layout)

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
            self.find_and_select_serial_port(self.SCAN_PATTERN)
            print('Found serial port automatically!')

    def select_port(self, idx) -> bool:
        """Return true if a selection is made."""
        if idx is None:
            return False

        self.combo_w.setCurrentIndex(idx)
        self.selection_changed(idx)

        return True

    def try_connection(self):
        """
        Try connecting to the selected serial port.

        Invoke callback if connection is succesful.

        """
        assert self.selected_serial is not None
        try:
            serial_connection = get_serial(self.selected_serial.device)
            self.on_connect(serial_connection)
        except SerialException:
            print('Error connecting!')

    def selection_changed(self, idx):
        """Select the new port and notify callbacks."""

        print('sel changed')
        self.selected_serial = self.available_ports[idx]
        self.on_select(self.selected_serial)
