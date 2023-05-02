"""
Test.

Author:
    Marco Perin

"""

from queue import Queue

try:
    from typing import Self  # type: ignore
except ImportError:
    from typing_extensions import Self

from typing import Type, cast

from datetime import datetime

from serial import Serial
from serial.threaded import ReaderThread

from ._packetizers import TurtlebotThreadedConnection
from ._utils import get_serial, get_serial_port_from_console_if_needed
from .packets import TimedPacket, TimedPacketBase
from ..received_structure import PlottingStruct


class TurtlebotReaderThread(ReaderThread):
    """Class to represent the thread responsible\
        of communicating with the STM."""

    packet_type: Type[TimedPacketBase]

    def __init__(
        self,
        serial_instance: Serial,
        rx_packet_spec: PlottingStruct,
        rx_queue: Queue,
        t_0: float | datetime | None = None,
        packet_type: Type[TimedPacketBase] = TimedPacket,
    ) -> None:
        """
        Create a thread to connect to the turtlebot in a separate thread.

        It uses the `TurtlebotThreadedConnection` as a base protocol
        """

        self.packet_type = packet_type

        def __get_tbot_protocol() -> TurtlebotThreadedConnection:
            return TurtlebotThreadedConnection(
                rx_packet_spec,
                rx_queue,
                packet_type=packet_type,
                t_0=t_0,
            )

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
    transport: TurtlebotReaderThread
    __thread: TurtlebotReaderThread
    __protocol: TurtlebotThreadedConnection
    __transport: TurtlebotReaderThread
    __packet_spec: PlottingStruct

    t_0: float | datetime | None

    def __init__(
        self,
        rx_packet_spec: PlottingStruct,
        serial: Serial,
        existing_queue: Queue | None,
        t_0: float | datetime | None = None,
    ) -> None:
        """Init the connection class to manage the connection to the STM."""

        if existing_queue is None:
            self.queue = Queue(100)
        else:
            self.queue = existing_queue

        self.__packet_spec = rx_packet_spec

        self.serial = serial

        self.t_0 = t_0

        self.__thread = TurtlebotReaderThread(
            self.serial, self.__packet_spec, self.queue, t_0=self.t_0
        )

        self.__thread.name = 'Serial comm Thread'

    def get_packet_type(self):
        """Return the type of timed packet used in the thread."""
        return self.__thread.packet_type

    # def get_t_0(self):
    #     """
    #     Return the t_0 at which the data has been instantiated.

    #     Used for future reconnections
    #     """

    #     return self.t_0

    def _start(self):
        """Start the underlying thread."""
        self.__thread.start()

    def connect(self):
        """Connect to the STM32."""
        self._start()

        transport, self.__protocol = self.__thread.connect()

        assert isinstance(transport, TurtlebotReaderThread)

        self.__transport = transport
        self.__protocol.signal_start_communication()
        self.transport = self.__transport

    def get_transport(self):
        return self.__transport

    def get_t_0(self):
        return self.__protocol.t_0

    def close(self):
        """Close the connection to the STM32 serial port."""
        self.__protocol.signal_stop_communication()

        # TODO: test if this is needed
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
        t_0: float | datetime | None = None,
    ) -> None:
        """Init the connection class to manage the connection to the STM."""
        self.port = get_serial_port_from_console_if_needed(
            autoscan_port=autoscan_port,
            autoscan_port_pattern=autoscan_port_pattern,
        )

        super().__init__(
            rx_packet_spec,
            serial=get_serial(self.port, baudrate),
            existing_queue=None,
            t_0=t_0,
        )


if __name__ == '__main__':
    # pylint: disable=wrong-import-position,ungrouped-imports
    import time
    from queue import Empty as q_Empty

    packet_spec = PlottingStruct.from_yaml_file()

    conn = TurtlebotSerialConnector(packet_spec)
    conn.connect()
    queue = conn.queue

    start_time = time.time()

    T = 5  # s

    while time.time() < start_time + T:
        try:
            d = queue.get(timeout=T)
            print('received: ', d)
        except q_Empty:
            print('No data received')
            break

    conn.close()
