import socket


class SocketClient:
    def __init__(self, host="localhost", port=6000, timeout=3.0):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.settimeout(timeout)

    def send(self, msg):
        if isinstance(msg, str):
            msg = msg.encode("utf-8")
        self.sock.sendto(msg, (self.host, self.port))

    def receive(self, bufsize=4096):
        try:
            data, _ = self.sock.recvfrom(bufsize)
            return data.decode("utf-8") if isinstance(data, bytes) else data
        except socket.timeout:
            return None

    def close(self):
        try:
            self.sock.close()
        except Exception:
            pass
