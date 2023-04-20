"""
Module to implement the custom packetizers for the communication with the \
 sender in another thread.

These implements the `serial.threaded.Packetizer` classes.

Author:
    Marco Perin

"""

from datetime import datetime
from queue import Queue
from struct import unpack as struct_unpack
from typing import List, Tuple, Type

from cobs import cobs

from serial.threaded import Packetizer

from .packets import TimedPacket, TimedPacketBase
from ..received_structure import PlottingStruct


class SerialThreadedRecv(Packetizer):
    """Threaded receiver class."""

    def _validate_package(self, packet: bytes) -> Tuple[bool, bytes | None]:
        """
        Validate the packet given.

        Additionally returs the decoded cobs package if it is so
        """
        data_raw = packet
        try:
            data = cobs.decode(data_raw)
        except cobs.DecodeError:
            print('Decode Error with', data_raw)
            return False, None
        if len(data) == 0:
            return False, None
        if not data:
            return False, None

        return True, data

    def handle_packet(self, packet: bytes) -> None:
        """Call `handle_valid_data` after validating the received bytes."""
        valid, data = self._validate_package(packet)

        if not valid:
            return

        assert data, '`data` is None even if it should not be as such'

        self.handle_valid_data(data)

    def handle_valid_data(self, data: bytes):
        """
        Handle packet assuming it is valid.

        Override this to manage the packet after it has been validated.
        """
        raise NotImplementedError


class SerialThreadedRecvTx(SerialThreadedRecv):
    """Extension of `SerialThreadedRecv` to include send_data method."""

    def send_data(self, data):
        """Send data to the receiver via `self.transport`."""
        assert self.transport is not None

        # TODO: check if flush is needed or not
        return self.transport.write(data)

    def handle_valid_data(self, data: bytes):
        """
        Handle packet assuming it is valid.

        Override this to manage the packet after it has been validated.
        """
        raise NotImplementedError


class TurtlebotThreadedConnection(SerialThreadedRecvTx):
    """
    Used to manage serial connection with turtlebots.

    Class managed to communicate with the turtlebots' \
        STM with thread-based serial communication

    Remember to call `signal_start()` for signalling \
        the STM to start transmitting
    """

    SEND_DATA_TOKEN = b'\x41\x00'
    STOP_DATA_TOKEN = b'\x42\x00'

    packet_spec: PlottingStruct
    rx_queue: Queue

    packet_type: Type[TimedPacketBase]

    t_0: None | float | datetime = None

    def __init__(
        self,
        packet_spec: PlottingStruct,
        rx_queue: Queue,
        packet_type: Type[TimedPacketBase] = TimedPacket
        # packet_type: Type[Packet] = DateTimedPacket
    ) -> None:
        """Init the class to communicate with the turtlebot."""
        super().__init__()

        assert packet_spec, 'packet_spec is mandatory'

        self.packet_spec = packet_spec
        self.queue = rx_queue
        self.packet_type = packet_type

        # if isinstance(packet_type, TimedPacketBase):
        # self.t0 = packet_type.get_time()
        self.t_0 = None

    def signal_start_communication(self):
        """Instruct the STM to start sendind data."""
        return self.send_data(self.SEND_DATA_TOKEN)

    def signal_stop_communication(self):
        """Instruct the STM to start sendind data."""
        return self.send_data(self.STOP_DATA_TOKEN)

    def _validate_package(self, packet: bytes) -> Tuple[bool, bytes | None]:
        valid, data = super()._validate_package(packet)

        if not valid:
            return False, None

        assert data

        if len(data) != self.packet_spec.struct_byte_size:
            return False, None
            # raise ValueError(('ERR: data size != packet size '
            #                   f'({len(data)} vs '
            #                   f'{self.packet_spec.struct_byte_size})'
            #                   ))

        return True, data

    def handle_valid_data(self, data: bytes) -> None:
        """Overload `handle_valid_data` to put in the queue the parsed data."""
        self.queue.put(self.parse_data(data))

    def parse_data(self, data: bytes):
        """Parse the data according to `self.packet_spec`."""
        packets: List = []

        data_i = 0
        for packet in self.packet_spec.subplots:
            data_packet = data[data_i : (data_i + packet.struct_byte_size)]

            packets.append(
                struct_unpack(packet.struct_format_string, data_packet)
            )
            data_i += packet.struct_byte_size

        pck = self.packet_type.from_data(data=packets)
        # if issubclass(type(pck), TimedPacketBase):

        if self.t_0 is None:
            self.t_0 = pck.time

        assert isinstance(pck.time, type(self.t_0))

        # Ignore warning as asserted previously that types match
        pck.time -= self.t_0  # type: ignore

        # print(pck)
        return pck
