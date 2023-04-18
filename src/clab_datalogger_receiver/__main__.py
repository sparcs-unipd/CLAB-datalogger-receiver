"""Main module, used to be able to call the package directly."""

from .main_functions import (
    ClabDataLoggerReceiver,
    main
)


MAT_FILENAME = 'test_data.mat'
MAX_ACQUISITION_TIME = 100  # s

# CAUTION: do not increase too much this value ( for the time being )
PLOT_FPS = 5

if __name__ == '__main__':
    dlogger = ClabDataLoggerReceiver(
        fps=PLOT_FPS,
        max_time=MAX_ACQUISITION_TIME
    )

    main(dlogger)
