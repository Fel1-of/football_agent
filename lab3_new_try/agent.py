import time
from msg import parse_msg
from flags import get_visible_flags, FLAGS, flag_key_from_see
from position import (
    position_from_three_flags,
    body_angle_from_flag,
    object_position_global,
    get_ball_from_see,
    get_opponent_from_see,
)
from socket_client import SocketClient
from controller import Controller


class InitError(Exception):
    """Не удалось получить ответ init от сервера."""


class Agent:
    def __init__(self, team_name, version=7, is_goalie=False, actions=None):
        self.team_name = team_name
        self.version = version
        self.is_goalie = is_goalie
        self.socket = SocketClient()
        self.controller = Controller(actions=actions, is_goalie=is_goalie)
        self.play_on = False
        self.running = False
        self.rotation_speed = 0.0
        self.x = None
        self.y = None
        self.side = ""
        self.unum = 0

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
        if len(p) > 1:
            self.side = p[1]
        if len(p) > 2 and isinstance(p[2], (int, float)):
            self.unum = int(p[2])
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
                self.controller.reset()
            elif str(msg).startswith("goal_"):
                self.play_on = False
                self.controller.on_goal()
                print("Гол зафиксирован: маршрут перезапущен с начала")

    def _process_see(self, parsed):
        flags_list = get_visible_flags(parsed)
        ball = get_ball_from_see(parsed)
        visible_objects = self._build_visible_objects(parsed)
        pos = position_from_three_flags(flags_list)
        if pos is None:
            self._send_command(visible_objects)
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

        self._send_command(visible_objects)

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

    def _send_command(self, visible_objects):
        command = self.controller.decide(
            visible_objects=visible_objects,
            game_on=self.play_on,
            team=self.team_name,
            side=self.side,
            player_number=self.unum,
            x=self.x,
            y=self.y,
        )
        if command:
            cmd, params = command
            self.socket.send(f"({cmd} {params})")
            return
        if self.play_on and self.rotation_speed != 0:
            self.turn(self.rotation_speed)

    def _build_visible_objects(self, parsed):
        visible = {}
        if parsed.get("cmd") != "see":
            return visible

        player_index = 0
        for ob in parsed.get("p", [])[2:]:
            if not isinstance(ob, dict) or "p" not in ob or not ob["p"]:
                continue

            raw_name = ob["p"][0]
            if isinstance(raw_name, dict) and "p" in raw_name:
                name_parts = list(raw_name["p"])
            else:
                name_parts = [raw_name]

            nums = [x for x in ob["p"] if isinstance(x, (int, float))]
            if len(nums) < 2:
                continue

            obj = {
                "name": name_parts,
                "dist": float(nums[0]),
                "dir": float(nums[1]),
            }
            if len(nums) >= 3:
                obj["dist_change"] = float(nums[2])
            if len(nums) >= 4:
                obj["dir_change"] = float(nums[3])

            first = name_parts[0]
            if first == "f":
                key = flag_key_from_see(ob)
            elif first == "g":
                key = "".join(str(int(x)) if isinstance(x, (int, float)) else str(x) for x in name_parts)
            elif first == "b":
                key = "b"
            elif first == "p":
                team = str(name_parts[1]).strip('"') if len(name_parts) > 1 else "unknown"
                number = str(int(name_parts[2])) if len(name_parts) > 2 and isinstance(name_parts[2], (int, float)) else str(player_index)
                key = f"p_{team}_{number}_{player_index}"
                player_index += 1
            else:
                key = "".join(str(int(x)) if isinstance(x, (int, float)) else str(x) for x in name_parts)

            if key:
                visible[key] = obj

        return visible

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
