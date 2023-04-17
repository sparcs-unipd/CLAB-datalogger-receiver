
from serial import Serial
from serial.tools.list_ports import comports


def get_serial_port() -> str | None:
    """Get a serial port.

    If more than one is available, \
        a prompt is presented to select which one to use.

    """
    pps = comports()

    assert len(pps) > 0, 'No serial ports found!'

    p_s: int = 0

    if len(pps) > 1:
        print('Select serial port')
        print('\n'.join(
            [
                f' [{i}] | {p.name} | [{p.description}]'
                for i, p in enumerate(pps)])
              )
        p_s_in = input()
        p_s = int(p_s_in)

    print(
        f'Connecting to {pps[p_s].name} [{pps[p_s].description}]...',
        end=''
    )
    # interface = SerialCommunicationInterface(pps[p_s].name, baudrate)
    print('done')

    # return interface
    return pps[p_s].name


def get_serial(port, baudrate=115200):
    """Build serial object with params for turtlebot."""
    return Serial(
        port=port,
        baudrate=baudrate,
        bytesize=8,
        timeout=1,
    )
