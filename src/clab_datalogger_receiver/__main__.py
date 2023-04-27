"""Main module, used to be able to call the package directly."""

import sys

from .qt_app_functions import main

if __name__ == '__main__':
    autoscan_pattern = 'STMicroelectronics'

    main(sys.argv)
