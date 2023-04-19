# Testing

In this document some notes about development are given.

## Dev environment

To set up the dev environment it is advised to use venvs.

### Creation

```console
# Windows
py -m venv env
# Linux
python -m venv env

```

### Start

```console
# Windows
.\env\Scripts\activate
# Linux
source env/bin/activate
```
### Stop

```console
deactivate
```

## Dev install

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

## Optional dependencies ( for development )

To install optional dependency it is possible to run

```console
pip install clab-datalogger-receiver[dev]
```

## Creating `requirements.txt`

```console
pip-compile pyproject.toml
```

## Upgrading version

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

## Building

#### MISSING BUILD COMMANDS

The following command tests the files after their build

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

