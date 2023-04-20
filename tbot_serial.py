"""
Serial plotting library.

Authors:
    Alberto Morato
    Marco Perin

"""


from clab_datalogger_receiver.main_functions import ClabDataLoggerReceiver, main


MAT_FILENAME = 'test_data.mat'
MAX_ACQUISITION_TIME = 100  # s

PLOT_FPS = 20

if __name__ == '__main__':
    dlogger = ClabDataLoggerReceiver(
        fps=PLOT_FPS, max_time=MAX_ACQUISITION_TIME
    )

    main(dlogger)
