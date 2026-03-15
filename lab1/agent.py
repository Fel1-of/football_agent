import time
from msg import parse_msg, parse_all_msgs
from flags import get_visible_flags, FLAGS
from config import (
    MOVE_X_MIN,
    MOVE_X_MAX,
    MOVE_Y_MIN,
    MOVE_Y_MAX,
)
from position import (
    position_from_three_flags,
    body_angle_from_flag,
    object_position_global,
    get_ball_from_see,
    get_opponent_from_see,
)
from socket_client import SocketClient


class InitError(Exception):
    """Не удалось получить ответ init от сервера."""


class Agent:
    def __init__(self, team_name, version=19, is_goalie=False, host="127.0.0.1", port=6000):
        self.team_name = team_name
        self.version = version
        self.is_goalie = is_goalie
        self.socket = SocketClient(host=host, port=port)
        self.play_on = False
        self.running = False
        self.rotation_speed = 0.0
        self.x = None
        self.y = None
        self.side = None

    def connect(self):
        goalie_str = " (goalie)" if self.is_goalie else ""
        self.socket.send(f"(init {self.team_name} (version {self.version}){goalie_str})")
        deadline = time.time() + 15
        while time.time() < deadline:
            data = self.socket.receive()
            if data and self._process_init(data):
                return
        self.socket.close()
        raise InitError("Нет ответа init от сервера")

    def _process_init(self, data):
        parsed = parse_msg(data)
        if not parsed or parsed.get("cmd") != "init":
            return False
        p = parsed.get("p") or []
        if len(p) > 1 and isinstance(p[1], str):
            self.side = p[1]
        if len(p) >= 2:
            print(f"Сервер: side={p[1]}, unum={p[2] if len(p) > 2 else '?'}, play_mode={p[3] if len(p) > 3 else '?'}")
        return True

    def move(self, x, y):
        self.socket.send(f"(move {x} {y})")

    def turn(self, moment):
        self.socket.send(f"(turn {moment})")

    def stop(self):
        self.running = False
        try:
            self.socket.send("(bye)")
            self.socket.close()
        except Exception:
            pass
        print("Агент остановлен")

    def _process_hear(self, parsed):
        p = parsed.get("p") or []
        # (hear Time Sender Message) -> p = [hear, time, sender, message]
        raw = str(parsed.get("msg", ""))
        if "play_on" in raw and "referee" in raw:
            self.play_on = True
            print(f"[{self.team_name}] Play on! Игрок может выполнять команды.")
            return
        if len(p) < 4:
            return
        sender = p[2]
        msg = str(p[3]) if len(p) > 3 else ""
        if sender != "referee":
            return
        if msg == "play_on" or "play_on" in msg:
            self.play_on = True
            print(f"[{self.team_name}] Play on! Игрок может выполнять команды.")
        elif "kick_off" in msg or str(msg).startswith("goal_"):
            self.play_on = False

    def _process_see(self, parsed):
        if not self.play_on:
            return
        flags_list = get_visible_flags(parsed)
        pos = position_from_three_flags(flags_list)
        if pos is None:
            return
        self.x, self.y = pos
        print(f"[Игрок] x={self.x:.2f} y={self.y:.2f}")

        body_rad = None
        if flags_list:
            f1 = flags_list[0]
            x1, y1 = FLAGS[f1["key"]]
            body_rad = body_angle_from_flag(self.x, self.y, x1, y1, f1["dist"], f1["angle"])

        if body_rad is None:
            return

        ball = get_ball_from_see(parsed)
        if ball:
            bx, by = object_position_global(
                self.x, self.y, body_rad, ball["dist"], ball["angle"]
            )
            print(f"[Мяч] x={bx:.2f} y={by:.2f}")

        opp = get_opponent_from_see(parsed, self.team_name)
        if opp:
            ox, oy = object_position_global(
                self.x, self.y, body_rad, opp["dist"], opp["angle"]
            )
            print(f"[Противник] x={ox:.2f} y={oy:.2f}")

    def on_message(self, data):
        text = data.decode("utf-8") if isinstance(data, bytes) else data
        for parsed in parse_all_msgs(text):
            if not parsed:
                continue
            cmd = parsed.get("cmd")
            if cmd == "hear":
                self._process_hear(parsed)
            elif cmd == "init":
                self._process_init(parsed)
            elif cmd == "see":
                self._process_see(parsed)
                if self.play_on and self.rotation_speed != 0:
                    self.turn(self.rotation_speed)

    def run(self, start_pos, rotation_speed=0):
        self.connect()
        # Стартовая позиция — строго внутри поля (протокол: x in [-54,54], y in [-32,32])
        x, y = start_pos
        x = max(MOVE_X_MIN, min(MOVE_X_MAX, x))
        y = max(MOVE_Y_MIN, min(MOVE_Y_MAX, y))
        self.move(x, y)
        self.rotation_speed = rotation_speed
        self.running = True
        print(f"Команда: {self.team_name}, позиция: {start_pos}, вращение: {rotation_speed}")
        print(">>> В мониторе нажмите KICK OFF — тогда игроки начнут двигаться!")

        while self.running:
            data = self.socket.receive()
            if data:
                self.on_message(data)
