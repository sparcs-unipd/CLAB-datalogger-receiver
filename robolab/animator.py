
from typing import Callable
from time import time as currtime


class Animator():
    '''
    Class used to ensure a method is called at (almost) a constant interval
    '''

    __fps: float
    __t_s: float

    __t_prev: float
    __func: Callable

    def __init__(self, func: Callable, fps: float = 10) -> None:

        self.fps = fps
        self.__func = func
        self.__t_prev = currtime()

    def animate(self, *args, upd_counter: bool = True,  **kwargs) -> None:
        '''Calls a function with the class fps'''

        t_now = currtime()
        if t_now < self.__t_prev + self.__t_s:
            return

        if upd_counter:
            self.__t_prev = t_now
        self.__func(*args, **kwargs)

    @property
    def fps(self) -> float:
        return self.__fps

    @fps.setter
    def fps(self, fps) -> None:

        assert fps > 0, "FPS should be positive"

        self.__fps = fps
        self.__t_s = 1/fps
