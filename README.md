# CLAB-datalogger-receiver
This repo is a reimplementation of the MATLAB datalogger project in python.

This is to prevent some errors occurring during the ERTC course due MATLAB's serial interface that was not working properly, and also to increase code portability.

## How-to

The main script of this project is `tbot_serial.py`.

On launch, it will connect to the serial port,
( asking whuch one, if multiple are available),
and send the `START_TRANSMISSION` token to the datalogger.

It is possible to stop the data recording both by pressing `CTRL+C` or by closing the plot window.

The script will then ask if it should save the data (default is yes).


## Testing

To test the program it is possible to use the script `tbot_serial_sender.py`,
after having installed a program like [com0com](https://com0com.sourceforge.net/).

In particular:

In one terminal:

    # Start the serial receiver
    python tbot_serial.py
    # Select one serial port

Then, in another

    # Start the serial sender
    python tbot_serial_sender.py
    # Select another serial port

From now on, data should start to populate the plots of `tbot_serial.py`.

