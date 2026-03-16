import argparse
import sys
import time
from socket_client import SocketClient
from msg import parse_msg


class StaticDefender:
    """Статичный защитник: занимает позицию, при play_on держится dash 0."""

    def __init__(self, team_name, pos_x, pos_y, version=7):
        self.team = team_name
        self.version = version
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.socket = SocketClient()
        self.running = False
        self.player_number = None
        self.side = None
        self.play_on = False

    def connect(self):
        self.socket.send(f"(init {self.team} (version {self.version}))")
        deadline = time.time() + 15
        while time.time() < deadline:
            data = self.socket.receive()
            if data and self._process_init_msg(data):
                return
        self.socket.close()
        raise Exception("Не удалось получить подтверждение инициализации от сервера")

    def _process_init_msg(self, data: str) -> bool:
        parsed = parse_msg(data)
        if not parsed or parsed.get("cmd") != "init":
            return False
        p = parsed.get("p") or []
        if len(p) >= 2:
            self.side = p[1]
        if len(p) >= 3:
            self.player_number = p[2]
        return True

    def move(self, x, y):
        self.socket.send(f"(move {x} {y})")

    def dash(self, power):
        self.socket.send(f"(dash {power})")

    def run(self):
        self.connect()
        self.move(self.pos_x, self.pos_y)
        print(f"Защитник {self.team} #{self.player_number}: цель ({self.pos_x}, {self.pos_y})")
        self.running = True
        while self.running:
            data = self.socket.receive()
            if not data:
                continue
            parsed = parse_msg(data)
            if not parsed:
                continue
            cmd = parsed.get("cmd")
            if cmd == "see":
                if self.play_on:
                    self.dash(0)
            elif cmd == "hear":
                p = parsed.get("p") or []
                if len(p) >= 4 and p[2] == "referee":
                    msg = str(p[3])
                    if "play_on" in msg:
                        self.play_on = True
                        self.move(self.pos_x, self.pos_y)
                    elif msg.startswith("goal_") or "kick_off" in msg:
                        self.play_on = False
                        self.move(self.pos_x, self.pos_y)

    def stop(self):
        self.running = False
        try:
            self.socket.send("(bye)")
            self.socket.close()
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser(description="Lab 4: Static Defender")
    parser.add_argument("--team", type=str, default="teamB")
    parser.add_argument("--x", type=float, default=-48)
    parser.add_argument("--y", type=float, default=5)
    args = parser.parse_args()

    agent = StaticDefender(team_name=args.team, pos_x=args.x, pos_y=args.y)
    try:
        agent.run()
    except KeyboardInterrupt:
        agent.stop()
    except Exception as e:
        print(e, file=sys.stderr)
        agent.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()
