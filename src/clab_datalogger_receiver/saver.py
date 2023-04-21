"""
Module to save the data of a `ClabDataloggerReceiver` session.

Author:
    Marco Perin

"""

import sys
from scipy.io import savemat, loadmat

from .simple_console_main_classes import ClabDataLoggerReceiver


def check_saved_data(test_data, loaded_data) -> bool:
    raise NotImplementedError


def save_data_clab_datalogger(
    datalogger: ClabDataLoggerReceiver,
    mat_filename: str = 'out_data.mat',
    check_data: bool = False,
):
    """Save the data of datalogger."""
    save_data_in = ''

    try:
        save_data_in = input('Do you want to save the data? [Y/n]')
    except EOFError:
        save_data_in = 'n'
    except KeyboardInterrupt:
        # Treat `CTRL+C` as a no
        save_data_in = 'n'

    if save_data_in not in 'Y\n':
        print('Exiting without saving data')
        sys.exit(0)

    file_dict = {
        'turtlebot_data': {'time': datalogger.x_data_vector, 'field_names': {}}
    }

    for idx, (sp, y_data) in enumerate(
        zip(datalogger.data_struct.subplots, datalogger.y_data_vector)
    ):
        name = sp.name

        if name is None:
            name = f'data_struct_{idx}'

        file_dict['turtlebot_data'][name] = y_data

        file_dict['turtlebot_data']['field_names'][name] = [
            f.name for f in sp.fields
        ]

    savemat(mat_filename, mdict=file_dict)

    print('Data saved.')

    if check_data:
        print('Checking data...')

        loaded_data = loadmat(mat_filename)

        if check_saved_data(file_dict, loaded_data):
            print('Data is ok')
        else:
            raise RuntimeError('The saved file is corrupted')


def save_data_raw(
    data_struct,
    x_data,
    y_data,
    mat_filename: str = 'out_data.mat',
    check_data: bool = False,
):
    file_dict = {'turtlebot_data': {'time': x_data, 'field_names': {}}}

    print('x_data:', x_data.shape)
    for idx, (sp, y_data) in enumerate(zip(data_struct.subplots, y_data)):
        name = sp.name

        if name is None:
            name = f'data_struct_{idx}'

        file_dict['turtlebot_data'][name] = y_data

        file_dict['turtlebot_data']['field_names'][name] = [
            f.name for f in sp.fields
        ]
    print('turtlebot_data:', file_dict['turtlebot_data'])

    savemat(mat_filename, mdict=file_dict)

    print('Data saved.')

    if check_data:
        print('Checking data...')

        loaded_data = loadmat(mat_filename)

        if check_saved_data(file_dict, loaded_data):
            print('Data is ok')
        else:
            raise RuntimeError('The saved file is corrupted')
