import socket


class SocketClient:
    def __init__(self, host: str = "localhost", port: int = 6000):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(3.0)

    def send(self, msg: str) -> None:
        self.sock.sendto(msg.encode(), (self.host, self.port))

    def receive(self, bufsize: int = 8192) -> str | None:
        try:
            data, _ = self.sock.recvfrom(bufsize)
            return data.decode()
        except socket.timeout:
            return None

    def close(self) -> None:
        self.sock.close()
