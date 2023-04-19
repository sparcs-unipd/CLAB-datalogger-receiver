"""
General utilities module for the `robolab` package.

Author:
    Marco Perin

"""
from serial import Serial
from serial.tools.list_ports import comports


def get_serial_port(
        autoscan_port: bool = True,
        autoscan_port_pattern: str = 'STMicroelectronics'
) -> str | None:
    """Get a serial port.

    If `autoscan_port==True`, then the `autoscan_port_pattern` is checked \
        and the first port matching with the pattern is selected.

    If more than one is available or  `autoscan_port == False`, \
        a prompt is presented to select which one to use.

    """
    available_ports = comports()

    assert len(available_ports) > 0, 'No serial ports found!'

    p_s: int = 0

    st_port_not_found = True

    if autoscan_port and len(available_ports) > 1:
        for port_idx, port in enumerate(available_ports):
            if autoscan_port_pattern in port.description:
                print('Automatic port found!')
                st_port_not_found = False
                p_s = port_idx
                break

    if len(available_ports) > 1 and st_port_not_found:
        print('Select serial port')
        print('\n'.join(
            [
                f' [{i}] | {p.name} | [{p.description}]'
                for i, p in enumerate(available_ports)])
              )
        p_s_in = input()

        if p_s_in.isnumeric():
            p_s = int(p_s_in)
        else:
            raise ValueError('The provied value is not an integer.')

    print(
        (
            f'Selected device {available_ports[p_s].device}'
            '[{available_ports[p_s].description}]...'
        ),
        end=''
    )

    return available_ports[p_s].device


def get_serial(port, baudrate=115200):
    """Build serial object with params for turtlebot."""

    return Serial(
        port=port,
        baudrate=baudrate,
        bytesize=8,
        timeout=1,
    )
