"""Main module, used to be able to call the package directly."""

from .main_functions import (
    ClabDataLoggerReceiver,
    main
)


MAT_FILENAME = 'test_data.mat'
MAX_ACQUISITION_TIME = 100  # s

PLOT_FPS = 60

TW = 10  # s, time window

if __name__ == '__main__':
    dlogger = ClabDataLoggerReceiver(
        fps=PLOT_FPS,
        max_time=MAX_ACQUISITION_TIME,
        t_w=TW
    )

    main(dlogger)
