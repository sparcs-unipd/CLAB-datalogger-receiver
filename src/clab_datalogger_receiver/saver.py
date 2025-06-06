"""
Module to save the data of a `ClabDataloggerReceiver` session.

Author:
    Marco Perin

"""

import sys
from scipy.io import savemat, loadmat
import pandas as pd
import numpy

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


def save_as_mat(
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
        

import numpy

def prepare_dataframe_dict(data_struct, x_data, y_data) -> dict:
    df_dict = {'time': x_data}
    reference_length = len(x_data)

    for i, subplot_struct in enumerate(data_struct.subplots):
        subplot_prefix = subplot_struct.name.replace(" ", "_").replace("-", "_")
        for j, field_struct in enumerate(subplot_struct.fields):
            field_suffix = field_struct.name.replace(" ", "_").replace("-", "_")
            col_name = f"{subplot_prefix}_{field_suffix}"
            
            k = 1
            base_col_name = col_name
            while col_name in df_dict:  # Handle potential column name collisions
                col_name = f"{base_col_name}_{k}"
                k += 1

            signal_data = y_data[i][j]
            if len(signal_data) != reference_length:
                print(f"Warning: Data length mismatch for column '{col_name}'. "
                      f"Expected {reference_length}, got {len(signal_data)}. Padding with NaNs.")
                padded_signal = numpy.full(reference_length, numpy.nan)
                min_len = min(len(signal_data), reference_length)
                padded_signal[:min_len] = signal_data[:min_len]
                df_dict[col_name] = padded_signal
            else:
                df_dict[col_name] = signal_data
    return df_dict

def save_as_pandas_dataframe(data_struct, x_data, y_data, filepath: str, file_format: str = 'parquet'):
    df_dict = prepare_dataframe_dict(data_struct, x_data, y_data)
    df = pd.DataFrame(df_dict)
    if file_format == 'parquet':
        try:
            df.to_parquet(filepath, index=False, engine='pyarrow')
        except ImportError:
            print("Warning: pyarrow not installed. Trying with default engine for Parquet.")
            df.to_parquet(filepath, index=False)
    elif file_format == 'csv':
        df.to_csv(filepath, index=False)
    elif file_format == 'pickle':
        df.to_pickle(filepath)
    else:
        raise ValueError(f"Unsupported file format: {file_format}. Supported formats are 'parquet', 'csv', and 'pickle'.")
