"""
This script is mainly used to implement the `Animator.animate(..)` function.

What that does, is that that function call rate is not called more than \
    `fps` times a second, making it a simple tool for animating plots.

Author:
    Marco Perin

"""

from time import time as currtime
from typing import Callable


class Animator:
    """This class is used to ensure that a method is called at an \
          (almost) constant frequency."""

    __fps: float
    __t_s: float

    __t_prev: float
    __func: Callable

    def __init__(self, func: Callable, fps: float = 10) -> None:
        """Init the class by passing the `func` to wrap and optionally \
            the `fps` parameter."""
        self.fps = fps
        self.__func = func
        self.__t_prev = currtime()

    def animate(self, *args, upd_counter: bool = True, **kwargs) -> None:
        """Call a function with the class fps."""
        t_now = currtime()
        if t_now < self.__t_prev + self.__t_s:
            return

        if upd_counter:
            self.__t_prev = t_now
        self.__func(*args, **kwargs)

    @property
    def fps(self) -> float:
        """Return `self.__fps`."""
        return self.__fps

    @fps.setter
    def fps(self, fps) -> None:
        """Set `self.__fps` taking care also of updating other parameters."""
        assert fps > 0, 'FPS should be positive'

        self.__fps = fps
        self.__t_s = 1 / fps
