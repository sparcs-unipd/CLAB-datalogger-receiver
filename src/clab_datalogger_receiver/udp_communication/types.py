

from socket import socket as socket_t, timeout

from serial import Serial


class Meta(type):
    def __call__(cls, *args, **kw):
        print("here")
        return cls.__new__(cls, *args, **kw)


class UDPData(Serial):
    """
    Class used to make the UDP interface appear as a Serial interface.

    This lets us use all the features from the previously written code,
        and of serial.threading.
    """
    socket: socket_t
    ip = str
    _port: int
    _is_open: bool = False

    __metaclass__ = Meta
    in_waiting: bool = False

    # Used for wrapping seria.Serial, used on _close()
    _overlapped_read = None

    def __init__(self, socket, ip_port) -> None:
        self.ip, self._port = ip_port
        self.socket = socket
        # self.timeout = 0.2
        self.open()

    def open(self):
        self.is_open = True
        # self.connect()

    def connect(self):
        # TODO: Check if this can raise an error or not
        self.socket.connect((self.ip, self._port))

    def send(self, data: bytes):
        # print(f"trying to send data to {(self.ip, self._port)}")
        return self.socket.sendto(data, (self.ip, self._port))

    def write(self, data):
        return self.send(data)

    def close(self):
        print('Closing Socket')
        self.socket.close()
        self.is_open = False

    def cancel_read(self):
        self.timeout = 0.1
        self.is_open = True
        # self.cancelled_read =
        # pass

    def read(self, size=0):

        # if size == 0:
        size = 1024

        blocking = True
        while blocking:
            try:
                if not self.is_open:
                    print('Trying to read with closed connection')
                    return None
                # data, addr = self.socket.recvfrom(size)
                data = self.socket.recv(size)
                blocking = False
            except timeout:
                pass

        # print(f"received from {addr} : {data}")
        # print(f"received : {data}")
        return data

    @property
    def timeout(self):
        return self.socket.timeout

    @timeout.setter
    def timeout(self, value: float):
        self.socket.settimeout(value)

    @property
    def is_open(self):
        return self._is_open

    @is_open.setter
    def is_open(self, value: bool):
        self._is_open = value

    @property
    def port(self):
        return self._port

    @port.setter
    def port(self, value: int):
        assert isinstance(value, int)
        self._port = value

    # def port(self,value)
