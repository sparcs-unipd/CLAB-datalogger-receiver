"""
General utilities module for the `robolab` package.

Author:
    Marco Perin

"""
from serial import Serial
from serial.tools.list_ports import comports


def get_serial_port(autoscan_st_port: bool = True) -> str | None:
    """Get a serial port.

    If more than one is available, \
        a prompt is presented to select which one to use.

    """
    available_ports = comports()

    assert len(available_ports) > 0, 'No serial ports found!'

    p_s: int = 0

    st_port_not_found = True

    if autoscan_st_port and len(available_ports) > 1:
        for port_idx, port in enumerate(available_ports):
            if 'STMicroelectronics' in port.description:
                print('ST port found!')
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
        p_s = int(p_s_in)

    print(
        f'Connecting to {available_ports[p_s].name} [{available_ports[p_s].description}]...',
        end=''
    )
    # interface = SerialCommunicationInterface(pps[p_s].name, baudrate)
    print('done')

    # return interface
    return available_ports[p_s].name


def get_serial(port, baudrate=115200):
    """Build serial object with params for turtlebot."""
    return Serial(
        port=port,
        baudrate=baudrate,
        bytesize=8,
        timeout=1,
    )
