"""
General utilities module for the `robolab` package.

Author:
    Marco Perin

"""
from serial import Serial

from serial.tools.list_ports_common import ListPortInfo
from serial.tools.list_ports import comports


def get_serial_port_text(port_info: ListPortInfo) -> str:
    return f'{port_info.device} [{port_info.description}]'


def get_serial_port_list() -> list[ListPortInfo]:
    """
    Returns the available ports.

    This is just a wrapper around pyserial's `comport()` function.
    """
    return comports()


def select_serial_port_index(
    available_ports: list[ListPortInfo],
    scan_pattern: str = 'STMicroelectronics',
) -> int | None:
    """
    Selects the best fitting comports given the search pattern.

    For now, it returns the first that has a substring matcing the given one.
    """

    p_s = None
    for port_idx, port in enumerate(available_ports):
        if scan_pattern in port.description:
            p_s = port_idx
            break

    return p_s


def get_serial_port_from_console_if_needed(
    autoscan_port: bool = True,
    autoscan_port_pattern: str = 'STMicroelectronics',
) -> str | None:
    """Get a serial port.

    If `autoscan_port==True`, then the `autoscan_port_pattern` is checked \
        and the first port matching with the pattern is selected.

    If more than one is available or  `autoscan_port == False`, \
        a prompt is presented to select which one to use.

    """

    available_ports = get_serial_port_list()

    assert len(available_ports) > 0, 'No serial ports found!'

    p_s: int | None = 0  # Select first by default

    st_port_not_found = True

    if autoscan_port and len(available_ports) > 1:
        p_s = select_serial_port_index(available_ports, autoscan_port_pattern)
        st_port_not_found = p_s is None

    if st_port_not_found:
        print('Automatic port found!')

    if len(available_ports) > 1 and st_port_not_found:
        print('Available serial ports:')
        print(
            '\n'.join(
                [
                    f' [{i}] | {get_serial_port_text(p)}'
                    for i, p in enumerate(available_ports)
                ]
            )
        )
        p_s_in = None
        try:
            p_s_in = input('Select serial port index: ')
        except EOFError:
            print('Hello user you have pressed ctrl-c button.')
        except KeyboardInterrupt:
            print('Hello user you have pressed ctrl-c button.')

        if p_s_in is not None and p_s_in.isnumeric():
            p_s = int(p_s_in)
        else:
            raise ValueError('The provied value is not an integer.')

    assert p_s is not None

    print(
        (
            f'Selected device {available_ports[p_s].device}'
            f'[{available_ports[p_s].description}]...'
        ),
        end='',
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
