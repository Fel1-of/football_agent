from control_hierarchy import ControllerLayer


class MotionLayer(ControllerLayer):
    """
    Тактический слой:
    - перевод стратегической цели в примитивные команды;
    - удержание внутреннего action-state.
    """

    def __init__(self, home_flag, role, side):
        super().__init__()
        self.home_flag = home_flag
        self.role = role
        self.side = side
        self.action = "go_to_flag"
        self.target_flag = home_flag
        self.scan_order = ["ft0", "fb0"]
        self.scan_index = 0

    def process(self, input_data):
        result = dict(input_data)
        result["cmd"] = self._command_for_action(input_data)
        result["mid_action"] = self.action
        result["at_home"] = self._is_at_home(input_data)
        result["memory"].update(self.memory)
        return result

    def merge(self, own_result, upper_result):
        if isinstance(upper_result, tuple):
            return upper_result

        if isinstance(upper_result, dict):
            if "command" in upper_result:
                if "say" in upper_result:
                    return {"command": upper_result["command"], "say": upper_result["say"]}
                return {"command": upper_result["command"]}

            if "new_action" in upper_result:
                self._apply_action_update(upper_result["new_action"])
                cmd = self._command_for_action(own_result)
                if "say" in upper_result:
                    if cmd:
                        return {"command": cmd, "say": upper_result["say"]}
                    return {"say": upper_result["say"]}
                return cmd

            if "say" in upper_result:
                if own_result.get("cmd"):
                    return {"command": own_result["cmd"], "say": upper_result["say"]}
                return {"say": upper_result["say"]}

        return own_result.get("cmd")

    def _apply_action_update(self, action_data):
        if isinstance(action_data, dict):
            next_action = action_data.get("action", "go_to_flag")
            if "flag" in action_data:
                self.target_flag = action_data["flag"]
            self.action = next_action
            if self.action == "return_home":
                self.target_flag = self.home_flag
            return

        self.action = str(action_data)
        if self.action == "return_home":
            self.target_flag = self.home_flag

    def _command_for_action(self, data):
        if self.action == "go_to_flag":
            return self._go_to_named_flag(data, self.target_flag, base=35, scale=2.4)
        if self.action == "return_home":
            return self._go_to_named_flag(data, self.home_flag, base=45, scale=3.2)
        if self.action == "go_to_ball":
            return self._go_to_ball(data)
        if self.action == "receive_pass":
            return self._receive_pass(data)
        if self.action == "watch_ball":
            return self._watch_ball(data)
        if self.action == "scan_field":
            return self._scan_field(data)

        self.action = "scan_field"
        return self._scan_field(data)

    def _is_at_home(self, data):
        flags = data.get("flags", {})
        if self.home_flag not in flags:
            return False
        return flags[self.home_flag].get("dist", 9999) < 3

    def _go_to_named_flag(self, data, flag_name, base, scale):
        flags = data.get("flags", {})
        target = flags.get(flag_name)
        if not target:
            return ("turn", "55")

        dist = target.get("dist", 9999)
        angle = target.get("dir", 0)

        if dist < 3:
            ball = data.get("ball")
            if ball:
                ball_angle = ball.get("dir", 0)
                if abs(ball_angle) > 6:
                    return ("turn", str(int(ball_angle)))
            return ("turn", "20")

        if abs(angle) > 10:
            return ("turn", str(int(angle)))

        power = min(100, int(base + dist * scale))
        return ("dash", str(power))

    def _go_to_ball(self, data):
        ball = data.get("ball")
        if not ball:
            self.action = "scan_field"
            return ("turn", "60")

        dist = ball.get("dist", 9999)
        angle = ball.get("dir", 0)

        if dist < 0.7:
            return None

        if abs(angle) > 6:
            return ("turn", str(int(angle)))

        return ("dash", str(min(100, int(40 + dist * 8))))

    def _receive_pass(self, data):
        ball = data.get("ball")
        if not ball:
            return ("turn", "45")

        dist = ball.get("dist", 9999)
        angle = ball.get("dir", 0)

        if dist < 0.7:
            self.action = "scan_field"
            return None

        if abs(angle) > 6:
            return ("turn", str(int(angle)))

        return ("dash", str(min(100, int(50 + dist * 9))))

    def _watch_ball(self, data):
        ball = data.get("ball")
        if not ball:
            return ("turn", "35")
        angle = ball.get("dir", 0)
        if abs(angle) > 6:
            return ("turn", str(int(angle)))
        return None

    def _scan_field(self, data):
        ball = data.get("ball")
        if ball:
            ball_angle = ball.get("dir", 0)
            if abs(ball_angle) > 6:
                return ("turn", str(int(ball_angle)))
            return ("turn", "15")

        flags = data.get("flags", {})
        target_flag = self.scan_order[self.scan_index]
        target = flags.get(target_flag)

        if target and abs(target.get("dir", 0)) <= 8:
            self.scan_index = (self.scan_index + 1) % len(self.scan_order)

        if target:
            angle = target.get("dir", 0)
            if abs(angle) > 8:
                return ("turn", str(int(angle)))

        if target_flag == "ft0":
            return ("turn", "-30" if self.side == "l" else "30")
        return ("turn", "30" if self.side == "l" else "-30")
