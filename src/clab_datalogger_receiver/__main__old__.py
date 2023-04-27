"""Main module, used to be able to call the package directly."""

import sys

from .main_functions import ClabDataLoggerReceiver, main


MAT_FILENAME = 'test_data.mat'
MAX_ACQUISITION_TIME = 100  # s

PLOT_FPS = 60

TW = 10  # s, time window

if __name__ == '__main__':
    autoscan_pattern = 'STMicroelectronics'

    if len(sys.argv) > 1:
        # print(sys.argv)
        autoscan_pattern = sys.argv[1]

    print(f'using {autoscan_pattern} as a pattern to look for the serial port')

    dlogger = ClabDataLoggerReceiver(
        fps=PLOT_FPS,
        max_time=MAX_ACQUISITION_TIME,
        t_w=TW,
        autoscan_port=True,
        autoscan_port_pattern=autoscan_pattern,
    )

    main(dlogger)
