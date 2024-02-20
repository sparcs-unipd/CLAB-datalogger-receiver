"""Main widgets for the gui of the application."""
from socket import socket, AF_INET, SOCK_DGRAM
from os import error
from typing import Callable

from PySide6.QtWidgets import (
    QComboBox,
    QInputDialog,
    QHBoxLayout,
    QPushButton,
    QWidget,
)
from qdarktheme import load_stylesheet
from serial import Serial, SerialException
from serial.tools.list_ports_common import ListPortInfo

from clab_datalogger_receiver.udp_communication.types import UDPData

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
    on_connect: Callable[[Serial | UDPData], None]

    disconnection_requested: Callable[[], bool]

    combo_w: QComboBox
    available_ports: list[ListPortInfo]

    selected_serial: ListPortInfo | None = None
    connected_serial: UDPData | Serial | None = None
    is_connected: bool = False

    SCAN_PATTERN = 'STMicroelectronics'

    connect_serial_btn: QPushButton
    refresh_btn: QPushButton

    def __init__(
        self,
        on_select_fcn: Callable[[ListPortInfo], None],
        on_connect_fcn: Callable[[Serial | UDPData], None],
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

        btn = QPushButton('Serial Connect')
        btn.clicked.connect(self.try_connection_serial)
        layout.addWidget(btn, 1)
        self.connect_serial_btn = btn

        btn = QPushButton('Network Connect')
        btn.clicked.connect(self.try_connection_network)
        layout.addWidget(btn, 1)
        self.connect_network_btn = btn

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
                if len(self.available_ports) == 0:
                    error("No available serial ports")
                else:
                    self.select_port(0)

    def select_port(self, idx) -> bool:
        """Return true if a selection is made."""
        if idx is None:
            return False

        self.combo_w.setCurrentIndex(idx)
        self.selection_changed(idx)

        return True

    def connected(self, serial_connection: Serial | UDPData):
        """
        Set button styles and call the callback when connection happens.

        Changes properties of the button corresponding to the connection type,
         and disables the other.
        Also calls self.on_connect after this.

        """

        if isinstance(serial_connection, UDPData):
            btn = self.connect_network_btn
            btn2 = self.connect_serial_btn
            btn.clicked.disconnect(self.try_connection_network)
            btn.clicked.connect(self.try_disconnection)
        else:
            btn = self.connect_serial_btn
            btn2 = self.connect_network_btn
            btn.clicked.disconnect(self.try_connection_serial)
            btn.clicked.connect(self.try_disconnection)

        btn.setText('Disconnect')
        btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: #333 }"
        )
        btn2.setDisabled(True)
        self.is_connected = True

        self.on_connect(serial_connection)

    def try_disconnection(self):
        """Try disconnecting from the serial port."""
        if self.disconnection_requested():
            print('Disconnection is requested')
            self.disconnected()

    def disconnected(self):
        """Gets called when succesfully disconnected from serial."""

        if isinstance(self.connected_serial, UDPData):
            connect_btn = self.connect_network_btn
            btn_text = 'Network Connect'
            connect_event = self.try_connection_network
        else:
            connect_btn = self.connect_serial_btn
            btn_text = 'Serial Connect'
            connect_event = self.try_connection_serial

        connect_btn.setText(btn_text)
        # self.connect_btn.setDisabled(True)

        # self.connect_btn.setPalette(self.original_palette)
        connect_btn.setStyleSheet(self.original_stylesheet)

        self.is_connected = False

        connect_btn.clicked.connect(connect_event)
        connect_btn.clicked.disconnect(self.try_disconnection)

    def try_connection_network(self):
        """
        Try connecting to the ip:port UDP socket.

        Invoke callback if connection is succesful.
        """

        # assert self.connected is False

        sock = socket(AF_INET, SOCK_DGRAM)

        ok = False
        numtries = 6
        while not ok and numtries > 0:
            numtries = numtries - 1
            text, ok = QInputDialog.getText(
                self,
                'Insert Connection data',
                'IP:port',
                text='localhost:42069',
            )
            if not ok or not text:
                break

            print(text)
            splitted = text.split(':')

            if len(splitted) != 2:
                ok = False
                continue

            ip, port = splitted
            try:
                port = int(port)
            except ValueError:
                ok = False
                continue
            # This does not fail if the connection is not found,
            #   but the sock.read() will, and that is managed.
            sock.connect((ip, port))

            self.connected_serial = UDPData(sock, (ip, port))
            ok = True

        if self.connected_serial is not None:
            if ok:
                # Connection succeeded
                self.connected(self.connected_serial)
            else:
                self.connected_serial.close()
                self.connected_serial = None

    def try_connection_serial(self):
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
