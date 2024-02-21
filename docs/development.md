# Testing

In this document some notes about development are given.

## Dev environment

To set up the dev environment it is advised to use venvs.

### Creation

```console
# Windows
py -m venv venv
# Linux
python -m venv venv

```

### Start

```console
# Windows
.\venv\Scripts\activate
# Linux
source venv/bin/activate
```
### Stop

```console
deactivate
```

## Dev install

In order to install the package for local development it is sufficient to run

```console
pip install -e .[dev]
```

where the `-e` flag stands for `--editable`,
reflecting the changes made locally to the package
without needing to reinstall it.

And finally, to check the information of the package

```console
pip show clab-datalogger-receiver 
```

## Optional dependencies (for development)

To install optional dependencies it is possible to run

```console
pip install clab-datalogger-receiver[dev]
```

## Creating `requirements.txt`

```console
pip-compile pyproject.toml
```

## Upgrading version

To update the version, `bumpver` is used 
(installed with the dev dependencies).

```console
# 0.1.0 -> 1.0.0
bumpver update --major
# 0.1.0 -> 0.2.0
bumpver update --minor
# 0.1.0 -> 0.1.1
bumpver update --patch
```

## Building

### Build commands

The program build into an executable, happens via [Nuitka](https://nuitka.net/).

To build the application, a convenience script is provided under `./scripts/build.bat`.
Every argument passed to that script is provided to Nuitka,
together with the others in the script


### Build test

#### **NOT WORKING RIGHT NOW, NEEDS MAINTENANCE** 

The following command tests the files after their build

```console
twine check dist/*
```

### Test upload

```console
twine upload -r testpypi dist/*
```

## Testing

### Serial Data

To test the program it is possible to use the script `tbot_serial_sender.py`,
after having installed a program (like [com0com](https://com0com.sourceforge.net/)) that creates a virtual COM port.

In particular:

- In one terminal:
```bash
# Start the serial receiver
python -m clab_datalogger_receiver
# Select one serial port
#  (If a port matching the name `STMicrocontroller` is found, 
#    it should be automatically selected)
# Press `Serial Connect`
```

- Then, in another
```bash
# Start the serial sender
python tbot_serial_sender.py
# Select another serial port
```

- From now on, random data should start to populate the plots of `tbot_serial.py`.

### UDP Data

To test the UDP Protocol part, another script is provided to send the data,
namely `test_udp.py`.


In particular:


- In one terminal:
```bash
# Start the serial sender
python test_udp.py
```

- Then, in another, launch the main application
```bash
# Start the serial receiver
python -m clab_datalogger_receiver
# Select one serial port
# Press `Network Connect`
```

- This should start the data stream using the UDP socket connection

