"""
This module is made in order to provide a general entrypoint to \
    the package functions.

Author:
    Marco Perin

"""


import sys

from .saver import save_data_clab_datalogger
from .simple_console_main_classes import ClabDataLoggerReceiver


def main(dlogger: ClabDataLoggerReceiver | None = None):
    """Run an example of a main function."""

    if dlogger is None:
        dlogger = ClabDataLoggerReceiver()

    dlogger.connect()

    dlogger.do_loop_while_true()

    dlogger.serial_conn.close()

    save_data_clab_datalogger(dlogger)

    sys.exit(0)


if __name__ == '__main__':
    main()
