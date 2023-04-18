# CLAB-datalogger-receiver
This repo is a reimplementation of the MATLAB datalogger project in python.

This is to prevent some errors occurring during the ERTC course due MATLAB's serial interface that was not working properly, and also to increase code portability.

## How-to

This is a runnable package, meaning that it is possible to run

```console
python -m clab_datalogger_receiver
```

or by launching the `run_receiver.bat` file.

Notice that the package needs first to be installed.

This can be done by running `install_package.bat`

On launch, it will connect to the serial port,
( asking whuch one, if multiple are available),
and send the `START_TRANSMISSION` token to the datalogger.

It is possible to stop the data recording both by pressing `CTRL+C` or by closing the plot window.

The script will then ask if it should save the data (default is yes).

## Packets configuration

It is possible to configure the serial data format in (mainly) two ways:

- By editing the file `struct_cfg.yaml`, that is loaded by the function call `PlottingStruct.from_yaml_file()`
- By calling the function `PlottingStruct.from_string_list(formats list)`, where formats is a list of format string that follows the convention of python's `struct`, as in [here](https://docs.python.org/3/library/struct.html#format-characters)


## PIP

### Dev environment

To set up the dev environment it is advised to use venvs.

#### Creation

```console
# Windows
py -m venv env
# Linux
python -m venv env

```

#### Start

```console
# Windows
.\env\Scripts\activate
# Linux
source env/bin/activate
```
#### Stop

```console
deactivate
```

### Dev install

In order to install the package for local development it is sufficient to run

```console
pip install -e .
```

where the `-e` flag stands for `--editable`,
reflecting the changes made locally to the package
without needing to reinstall it.

And finally, to check the information of the package

```console
pip show clab-datalogger-receiver 
```

### Optional dependencies ( for development )

To install optional dependency it is possible to run

```console
pip install clab-datalogger-receiver[dev]
```

### Creating `requirements.txt`

```console
pip-compile pyproject.toml
```

### Upgrading version

To update the version, `bumpver` is used 
(it is installed with the dev dependencies).

```console
# 0.1.0 -> 1.0.0
bumpver update --major
# 0.1.0 -> 0.2.0
bumpver update --minor
# 0.1.0 -> 0.1.1
bumpver update --patch
```

### Building

The following command creates the files needed for publishing in PyPI

```console
twine check dist/*
```

### Test upload

```console
twine upload -r testpypi dist/*
```

## Testing

To test the program it is possible to use the script `tbot_serial_sender.py`,
after having installed a program (like [com0com](https://com0com.sourceforge.net/)) that creates a virtual COM port.

In particular:

- In one terminal:
```console
# Start the serial receiver
python tbot_serial.py
# Select one serial port
```

- Then, in another
```console
# Start the serial sender
python tbot_serial_sender.py
# Select another serial port
```

- From now on, random data should start to populate the plots of `tbot_serial.py`.

