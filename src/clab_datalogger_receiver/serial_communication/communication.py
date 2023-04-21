"""
Test.

Author:
    Marco Perin

"""

from queue import Queue
from typing import Self, cast

from serial import Serial
from serial.threaded import ReaderThread

from ._packetizers import TurtlebotThreadedConnection
from ._utils import get_serial, get_serial_port_from_console_if_needed
from .packets import TimedPacketBase
from ..received_structure import PlottingStruct


class TurtlebotReaderThread(ReaderThread):
    """Class to represent the thread responsible\
        of communicating with the STM."""

    def __init__(
        self,
        serial_instance: Serial,
        rx_packet_spec: PlottingStruct,
        rx_queue: Queue,
    ) -> None:
        """
        Create a thread to connect to the turtlebot in a separate thread.

        It uses the `TurtlebotThreadedConnection` as a base protocol
        """

        def __get_tbot_protocol() -> TurtlebotThreadedConnection:
            return TurtlebotThreadedConnection(rx_packet_spec, rx_queue)

        super().__init__(serial_instance, __get_tbot_protocol)

    def connect(self) -> tuple[Self, TurtlebotThreadedConnection]:
        """
        Init serial connection.

        This is a wrapper of the `ReaderThread.connect()` method, used\
            to cast the protocol to the turtlebot one
        """
        trans, prot = super().connect()

        prot = cast(TurtlebotThreadedConnection, prot)
        return trans, prot


class ManualPortTurtlebotSerialConnector:
    """Class representing the turtlebot asinc serial communication."""

    serial: Serial
    queue: Queue[TimedPacketBase]
    __thread: TurtlebotReaderThread
    __protocol: TurtlebotThreadedConnection
    __transport: TurtlebotReaderThread
    __packet_spec: PlottingStruct

    def __init__(
        self,
        rx_packet_spec: PlottingStruct,
        serial: Serial,
        existing_queue: Queue | None,
    ) -> None:
        """Init the connection class to manage the connection to the STM."""

        if existing_queue is None:
            self.queue = Queue()
        else:
            self.queue = existing_queue

        self.__packet_spec = rx_packet_spec

        self.serial = serial

        self.__thread = TurtlebotReaderThread(
            self.serial, self.__packet_spec, self.queue
        )

        self.__thread.name = 'Serial comm Thread'

    def _start(self):
        """Start the underlying thread."""
        self.__thread.start()

    def connect(self):
        """Connect to the STM32."""
        self._start()
        self.__transport, self.__protocol = self.__thread.connect()
        self.__protocol.signal_start_communication()

    def close(self):
        """Close the connection to the STM32 serial port."""
        self.__protocol.signal_stop_communication()
        # TODO: test this
        # self.serial.close()
        self.__thread.close()


class TurtlebotSerialConnector(ManualPortTurtlebotSerialConnector):
    """Class representing the turtlebot asinc serial communication."""

    def __init__(
        self,
        rx_packet_spec: PlottingStruct,
        baudrate=115200,
        autoscan_port: bool = True,
        autoscan_port_pattern: str = 'STMicroelectronics',
    ) -> None:
        """Init the connection class to manage the connection to the STM."""
        self.port = get_serial_port_from_console_if_needed(
            autoscan_port=autoscan_port,
            autoscan_port_pattern=autoscan_port_pattern,
        )

        super().__init__(
            rx_packet_spec,
            serial=get_serial(self.port, baudrate),
        )


if __name__ == '__main__':
    # pylint: disable=wrong-import-position,ungrouped-imports
    import time
    from queue import Empty as q_Empty

    packet_spec = PlottingStruct.from_yaml_file()

    conn = TurtlebotSerialConnector(packet_spec)
    conn.connect()
    queue = conn.queue

    t_0 = time.time()

    T = 5  # s

    while time.time() < t_0 + T:
        try:
            d = queue.get(timeout=T)
            print('received: ', d)
        except q_Empty:
            print('No data received')
            break

    conn.close()
