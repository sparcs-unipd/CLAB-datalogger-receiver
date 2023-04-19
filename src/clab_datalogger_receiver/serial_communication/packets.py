"""
Define various packet types.

Author:
    Marco Perin
"""

from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime

# from time import process_time as time

# from time import thread_time
from time import perf_counter as time_now
from typing import Any


@dataclass
class Packet:
    """Base packet class."""

    data: Any

    @classmethod
    @abstractmethod
    def from_data(cls, data: Any):
        """
        Build the packet considering only data.

        Must be implemented in all subclasses.
        """
        return cls(data)


@dataclass
class TimedPacketBase(Packet):
    """Base class for a packet with a time field."""

    time: float | datetime

    @classmethod
    def from_data(cls, data: Any):
        """
        Construct this package from data.

        To be implemented by the deriving class.
        """
        return cls(data, cls.get_time())

    @staticmethod
    @abstractmethod
    def get_time() -> float | datetime:
        """
        Return the time with the same type as `self.time`.

        To be implemented by the deriving class.

        """
        raise NotImplementedError


@dataclass
class DateTimedPacket(TimedPacketBase):
    """Data class representing a packet with timestamp."""

    time: datetime

    # @classmethod
    # def from_data(cls, data: Any):
    #     """Build a timed packet with `datetime.now()` as timestamp."""
    #     return cls(data, datetime.now())

    @staticmethod
    def get_time():
        """Return current time as a datetime."""
        return datetime.now()


@dataclass
class TimedPacket(TimedPacketBase):
    """Data class representing a packet with timestamp."""

    time: float

    # @classmethod
    # def from_data(cls, data: Any):
    #     """Build a timed packet with `thread_time()` as timestamp."""
    #     # return cls(data, thread_time())
    #     return cls(data, time_now())

    @staticmethod
    def get_time():
        """Return the current time as a float."""
        return time_now()


if __name__ == '__main__':
    p0 = Packet([0, 1, 2])
    p1 = TimedPacket.from_data([4, 5, 6])
    p2 = DateTimedPacket.from_data([7, 8, 9])

    print('p0: ', p0)
    print('p1: ', p1)
    print('p2: ', p2)

    P2Type = type(p2)
    p3 = P2Type.from_data('CIAO')

    print(p3)
