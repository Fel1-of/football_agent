import time
from msg import parse_msg
from flags import get_visible_flags, FLAGS
from controller import Controller
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
    def __init__(self, team_name, version=7, is_goalie=False):
        self.team_name = team_name
        self.version = version
        self.is_goalie = is_goalie
        self.socket = SocketClient()
        self.play_on = False
        self.running = False
        self.rotation_speed = 0.0
        self.x = None
        self.y = None
        self.side = None
        self.controller = Controller()

    def connect(self):
        goalie_str = " (goalie)" if self.is_goalie else ""
        self.socket.send(f"(init {self.team_name} (version {self.version}){goalie_str})")
        deadline = time.time() + 5
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
            self.controller.set_actions(self._route_for_side(self.side))
        play_mode = p[3] if len(p) > 3 else None
        if isinstance(play_mode, str):
            self.play_on = (play_mode == "play_on")
        if len(p) >= 2:
            print(f"Сервер: side={p[1]}, unum={p[2] if len(p) > 2 else '?'}, play_mode={play_mode if play_mode else '?'}")
        if play_mode == "play_on":
            print("Внимание: подключение произошло во время play_on, команда move может быть проигнорирована сервером.")
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
        if len(p) >= 3 and p[2] == "referee":
            msg = p[3] if len(p) > 3 else ""
            if msg == "play_on":
                self.play_on = True
            elif str(msg).startswith("kick_off"):
                self.play_on = False
            elif str(msg).startswith("goal_"):
                self.play_on = False
                self.controller.on_goal()

    def _process_see(self, parsed):
        flags_list = get_visible_flags(parsed)
        ball = get_ball_from_see(parsed)
        pos = position_from_three_flags(flags_list)
        if pos is None:
            print("[Игрок] позиция не определена (мало ориентиров)")
            if ball:
                print(f"[Мяч][отн] dist={ball['dist']:.2f} angle={ball['angle']:.2f}")
            opp_rel = get_opponent_from_see(parsed, self.team_name)
            if opp_rel:
                print(f"[Противник][отн] dist={opp_rel['dist']:.2f} angle={opp_rel['angle']:.2f}")
            self._send_command(flags_list, ball)
            return

        self.x, self.y = pos
        print(f"[Игрок] x={self.x:.2f} y={self.y:.2f}")

        body_rad = None
        if flags_list:
            f1 = flags_list[0]
            x1, y1 = FLAGS[f1["key"]]
            body_rad = body_angle_from_flag(self.x, self.y, x1, y1, f1["dist"], f1["angle"])

        if body_rad is not None and ball:
            bx, by = object_position_global(
                self.x, self.y, body_rad, ball["dist"], ball["angle"]
            )
            print(f"[Мяч] x={bx:.2f} y={by:.2f}")

        opp = get_opponent_from_see(parsed, self.team_name)
        if body_rad is not None and opp:
            ox, oy = object_position_global(
                self.x, self.y, body_rad, opp["dist"], opp["angle"]
            )
            print(f"[Противник] x={ox:.2f} y={oy:.2f}")
        elif opp:
            print(f"[Противник][отн] dist={opp['dist']:.2f} angle={opp['angle']:.2f}")

        self._send_command(flags_list, ball)

    def on_message(self, data):
        text = data.decode("utf-8") if isinstance(data, bytes) else data
        parsed = parse_msg(text)
        if not parsed:
            return
        cmd = parsed.get("cmd")
        if cmd == "hear":
            self._process_hear(parsed)
        elif cmd == "see":
            self._process_see(parsed)

    def _send_command(self, flags_list=None, ball=None):
        if not self.play_on:
            return
        command = self.controller.decide(self.play_on, flags_list or [], ball)
        if command:
            self.socket.send(f"({command['n']} {command['v']})")
            return
        if self.rotation_speed != 0:
            self.turn(self.rotation_speed)

    def _route_for_side(self, side):
        # Маршрут зеркалится по стороне поля: слева идем к правым флагам и воротам, справа — наоборот.
        if side == "r":
            return [
                {"act": "flag", "fl": "fplb"},
                {"act": "flag", "fl": "fglb"},
                {"act": "kick", "goal": "gl"},
            ]
        return [
            {"act": "flag", "fl": "fprb"},
            {"act": "flag", "fl": "fgrb"},
            {"act": "kick", "goal": "gr"},
        ]

    def run(self, start_pos, rotation_speed=0):
        self.connect()
        self.move(*start_pos)
        self.rotation_speed = rotation_speed
        self.running = True
        print(f"Команда: {self.team_name}, позиция: {start_pos}, вращение: {rotation_speed}")

        while self.running:
            data = self.socket.receive()
            if data:
                self.on_message(data)
