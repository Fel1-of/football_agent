import time
from socket_client import SocketClient
from msg import parse_msg
from flags import FLAGS, get_visible_objects_from_see, get_visible_flags
from position import position_from_three_flags
from controller import Controller


class InitError(Exception):
    pass


class Agent:
    def __init__(self, team_name, controller: Controller, version=7, is_goalie=False):
        self.team = team_name
        self.version = version
        self.is_goalie = is_goalie
        self.side = None
        self.player_number = None
        self.game_mode = None
        self.socket = SocketClient()
        self.play_on = False
        self.running = False
        self.x = None
        self.y = None
        self.visible_objects = {}
        self.controller = controller
        self.start_pos = (-15, 0)
        self.last_heard_msg = None

    def connect(self):
        goalie_str = " (goalie)" if self.is_goalie else ""
        self.socket.send(f"(init {self.team} (version {self.version}){goalie_str})")
        deadline = time.time() + 5
        while time.time() < deadline:
            data = self.socket.receive()
            if data and self._process_init_msg(data):
                return
        self.socket.close()
        raise InitError("Нет ответа init от сервера")

    def _process_init_msg(self, data: str) -> bool:
        parsed = parse_msg(data)
        if not parsed or parsed.get("cmd") != "init":
            return False
        p = parsed.get("p") or []
        if len(p) >= 2:
            self.side = p[1] if isinstance(p[1], str) else str(p[1])
        if len(p) >= 3:
            self.player_number = p[2]
        if len(p) >= 4:
            self.game_mode = p[3]
        return True

    def move(self, x, y):
        self.socket.send(f"(move {x} {y})")

    def say(self, message):
        self.socket.send(f"(say {message})")

    def _send_command(self, cmd: str, params: str):
        self.socket.send(f"({cmd} {params})")

    def process_message(self, msg: str):
        parsed = parse_msg(msg)
        if not parsed:
            return
        cmd = parsed.get("cmd")
        if cmd == "see":
            self._process_see(parsed)
        elif cmd == "hear":
            self._process_hear(parsed)

    def _process_hear(self, parsed: dict):
        p = parsed.get("p") or []
        if len(p) < 4:
            return
        sender = p[2]
        message = p[3] if len(p) > 3 else ""
        if sender == "referee":
            msg_str = str(message)
            if msg_str == "play_on" or "play_on" in msg_str:
                self.play_on = True
            elif "kick_off" in msg_str or msg_str.startswith("goal_"):
                self.play_on = False
                if msg_str.startswith("goal_"):
                    self.controller.reset()
                    self.move(*self.start_pos)
        else:
            self.last_heard_msg = str(message).strip('"')

    def _process_see(self, parsed: dict):
        self.visible_objects = get_visible_objects_from_see(parsed)
        self._compute_my_position(parsed)

        decision = self.controller.decide(
            self.visible_objects,
            self.play_on,
            team=self.team,
            side=self.side or "",
            player_number=self.player_number or 0,
            x=self.x,
            y=self.y,
            last_heard_msg=self.last_heard_msg,
        )
        if decision:
            cmd, params = decision
            self._send_command(cmd, params)

        state = self.controller.dt.state
        if state.get("say"):
            self.say(state["say"])
            state["say"] = None
        self.last_heard_msg = None

    def _compute_my_position(self, see_res: dict):
        flags_list = get_visible_flags(see_res)
        if not flags_list:
            return
        pos = position_from_three_flags(flags_list)
        if pos:
            self.x, self.y = pos

    def run(self, start_pos: tuple):
        self.start_pos = start_pos
        self.connect()
        self.move(*start_pos)
        self.running = True
        print(f"Команда: {self.team}, номер: {self.player_number}, сторона: {self.side}, позиция: {start_pos}, вратарь: {self.is_goalie}")
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
        print("Агент остановлен")
