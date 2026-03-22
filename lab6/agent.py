# ===== FILE: src/agent.py =====

import time
from socket_client import SocketClient
from flags import FLAGS, obj_name_to_key
from msg_parser import MsgParser
from geometry import (
    compute_position_two_flags,
    compute_position_three_flags,
)


class InitError(Exception):
    pass


class Agent:
    def __init__(self, team_name, controllers, version=7, is_goalie=False,
                 role="forward", home_flag="fc"):
        self.team = team_name
        self.version = version
        self.is_goalie = is_goalie
        self.role = role
        self.home_flag = home_flag
        self.side = None
        self.player_number = None
        self.game_mode = None
        self.socket = SocketClient()
        self.play_on = False
        self.running = False
        self.visible_objects = {}
        self.controllers = controllers
        self.start_pos = (-15, 0)
        self.last_heard_msg = None
        self.referee_msg = None
        self.current_play_mode = None

    def connect(self):
        goalie_str = " (goalie)" if self.is_goalie else ""
        cmd = f"(init {self.team} (version {self.version}){goalie_str})"
        self.socket.send(cmd)

        start = time.time()
        while time.time() - start < 5:
            data = self.socket.receive()
            if data and self._process_init_msg(data):
                break
        else:
            self.stop()
            raise InitError("Не удалось получить init от сервера")

    def _process_init_msg(self, data: str) -> bool:
        parsed = MsgParser.parse_msg(data)
        if not parsed or parsed[0] != "init":
            return False
        self.side = parsed[1]
        self.player_number = parsed[2]
        self.game_mode = parsed[3] if len(parsed) > 3 else None
        self._update_controllers_side()
        return True

    def _update_controllers_side(self):
        if self.controllers:
            low = self.controllers[0]
            low.side = self.side
            low.team = self.team
            low.player_number = self.player_number
            low.role_key = self.role
            for ctrl in self.controllers:
                if hasattr(ctrl, 'side'):
                    ctrl.side = self.side

    def move(self, x, y):
        self.socket.send(f"(move {x} {y})")

    def say(self, message):
        self.socket.send(f"(say {message})")

    def _send_command(self, cmd: str, params: str):
        """Отправка команды серверу. Поддерживает kick, dash, turn, catch."""
        self.socket.send(f"({cmd} {params})")

    def process_message(self, msg: str):
        parsed = MsgParser.parse_msg(msg)
        if not parsed:
            return
        msg_type = parsed[0]
        if msg_type == "see":
            self._process_see(parsed)
        elif msg_type == "hear":
            self._process_hear(parsed)

    def _process_hear(self, parsed: list):
        if len(parsed) < 4:
            return
        sender = parsed[2]
        message = parsed[3] if len(parsed) > 3 else ""
        if sender == "referee":
            msg_str = str(message)
            self.referee_msg = msg_str
            self.current_play_mode = msg_str
            self.play_on = self._is_active_mode(msg_str)

            if msg_str.startswith("goal_"):
                self.play_on = False
                self.move(*self.start_pos)
                if len(self.controllers) > 1:
                    mid = self.controllers[1]
                    mid.action = "go_to_flag"
                    mid.target_flag = mid.home_flag
        else:
            self.last_heard_msg = str(message)

    def _is_active_mode(self, mode: str) -> bool:
        if not mode:
            return False

        if mode in ("play_on", "drop_ball"):
            return True

        if mode.startswith(("before_kick_off", "time_over", "goal_", "half_time")):
            return False

        my_suffix = f"_{self.side}" if self.side else ""

        my_set_play_prefixes = (
            "kick_off_",
            "kick_in_",
            "corner_kick_",
            "free_kick_",
            "goal_kick_",
            "indirect_free_kick_",
            "back_pass_",
            "catch_fault_",
            "foul_",
        )
        if mode.startswith(my_set_play_prefixes):
            return bool(my_suffix and mode.endswith(my_suffix))

        if mode.startswith("offside_"):
            if not my_suffix:
                return False
            return not mode.endswith(my_suffix)

        return False

    def _process_see(self, parsed: list):
        if len(parsed) < 2:
            return

        self.visible_objects = {}

        for i in range(2, len(parsed)):
            obj_info = parsed[i]
            if not isinstance(obj_info, list) or len(obj_info) < 2:
                continue
            obj_name_raw = obj_info[0]
            params = obj_info[1:]
            if not isinstance(obj_name_raw, list):
                continue

            key = obj_name_to_key(obj_name_raw)
            entry = {"name": obj_name_raw, "dist": float(params[0])}
            if len(params) >= 2:
                entry["dir"] = float(params[1])
            if len(params) >= 3:
                entry["dist_change"] = float(params[2])
            if len(params) >= 4:
                entry["dir_change"] = float(params[3])
            if len(params) >= 5:
                entry["body_facing_dir"] = float(params[4])
            if len(params) >= 6:
                entry["head_facing_dir"] = float(params[5])

            self.visible_objects[key] = entry

        if not self.play_on:
            self.last_heard_msg = None
            return

        input_data = {
            "visible": self.visible_objects,
            "play_on": self.play_on,
            "last_heard_msg": self.last_heard_msg,
            "referee_msg": self.current_play_mode,
        }

        low = self.controllers[0]
        upper = self.controllers[1:]
        result = low.execute(input_data, upper)

        if result and isinstance(result, tuple) and len(result) == 2:
            cmd, params = result
            self._send_command(cmd, params)
        elif result and isinstance(result, dict):
            if "command" in result:
                cmd_tuple = result["command"]
                if cmd_tuple and isinstance(cmd_tuple, tuple) and len(cmd_tuple) == 2:
                    self._send_command(cmd_tuple[0], cmd_tuple[1])
            if "say" in result:
                self.say(result["say"])

        self.last_heard_msg = None

    def run(self, start_pos: tuple):
        self.start_pos = start_pos
        self.connect()
        self.move(*start_pos)
        self.running = True
        print(
            f"[{self.team}] #{self.player_number} side={self.side} "
            f"role={self.role} home_flag={self.home_flag} "
            f"pos={start_pos} goalie={self.is_goalie}"
        )
        while self.running:
            data = self.socket.receive()
            if data:
                self.process_message(data)

    def stop(self):
        self.running = False
        try:
            self.socket.send("(bye)")
            self.socket.close()
        except Exception:
            pass
        print(f"Агент {self.role}#{self.player_number} остановлен")
