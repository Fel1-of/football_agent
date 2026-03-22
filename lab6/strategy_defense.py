from control_hierarchy import ControllerLayer


class DefenseStrategy(ControllerLayer):
    def __init__(self, side, home_flag, role_key="defender_center"):
        super().__init__()
        self.side = side
        self.home_flag = home_flag
        self.role_key = role_key
        self.last_mode = "hold"
        self.restart_mode = ""
        self.throw_in_prepared = False

    def process(self, input_data):
        if not input_data.get("play_on", False):
            self.last_mode = "reset"
            return {"new_action": "return_home"}

        referee_msg = str(input_data.get("referee_msg") or "")
        self._update_restart_state(referee_msg)

        is_throw = self._is_my_throw_in(referee_msg, input_data.get("side"))
        is_corner = self._is_my_corner(referee_msg, input_data.get("side"))
        if is_throw or is_corner:
            if self._am_taker(input_data):
                if input_data.get("can_kick"):
                    if is_corner:
                        return self._execute_corner(input_data)
                    return self._execute_throw_in(input_data)
                return {"new_action": "go_to_ball"}

            hold_flag = self.home_flag
            return {"new_action": {"action": "return_home", "flag": hold_flag}}

        if input_data.get("can_kick"):
            self.last_mode = "kick"
            return self._build_out(input_data)

        if input_data.get("pass_to_me"):
            self.last_mode = "receive"
            return {"new_action": "receive_pass"}

        ball = input_data.get("ball")
        home_dist = self._home_distance(input_data)

        if ball:
            ball_dist = ball.get("dist", 9999)
            ball_angle = ball.get("dir", 0)
            if self._must_press_ball(input_data, ball_dist):
                self.last_mode = "press"
                return {"new_action": "go_to_ball"}

            if ball_dist < 28 and input_data.get("teammates_closer_to_ball", 0) <= 1:
                self.last_mode = "support_press"
                return {"new_action": "go_to_ball"}

            if home_dist and home_dist > 7:
                self.last_mode = "recover"
                return {"new_action": "return_home"}

            if abs(ball_angle) > 12:
                return ("turn", str(int(ball_angle)))

            self.last_mode = "mark"
            return {"new_action": "watch_ball"}

        if home_dist and home_dist > 4:
            self.last_mode = "recover"
            return {"new_action": "return_home"}

        return ("turn", "40")

    def _must_press_ball(self, input_data, ball_dist):
        closest = input_data.get("i_am_closest_to_ball", True)
        teammate_near = input_data.get("teammate_near_ball", False)
        pressure_radius = 22 if self.role_key == "defender_sweeper" else 18
        return ball_dist <= pressure_radius and closest and not teammate_near

    def _update_restart_state(self, referee_msg):
        if referee_msg != self.restart_mode:
            self.restart_mode = referee_msg
            self.throw_in_prepared = False
            self.corner_prepared = False

    def _is_my_throw_in(self, referee_msg, side):
        if not referee_msg or not side:
            return False
        return referee_msg.startswith("kick_in_") and referee_msg.endswith(f"_{side}")

    def _is_my_corner(self, referee_msg, side):
        if not referee_msg or not side:
            return False
        return referee_msg.startswith("corner_kick_") and referee_msg.endswith(f"_{side}")

    def _am_taker(self, input_data):
        role = self.role_key
        if role.startswith("midfielder_center") or role.startswith("defender_center"):
            return True
        if role == "defender_sweeper":
            return True
        return input_data.get("i_am_closest_to_ball", True)

    def _execute_throw_in(self, input_data):
        if not self.throw_in_prepared and self._near_sideline(input_data):
            self.throw_in_prepared = True
            inward = self._inward_angle(input_data)
            return {"command": ("kick", f"20 {int(inward)}")}

        self.throw_in_prepared = False

        nearest = self._nearest_teammate(input_data)
        if nearest:
            angle = nearest.get("dir", 0)
            dist = nearest.get("dist", 10)
            power = min(80, max(35, int(16 + dist * 4)))
            return {"command": ("kick", f"{power} {int(angle)}"), "say": "pass"}

        goal_opp = input_data.get("goal_opp")
        if goal_opp:
            return {"command": ("kick", f"75 {int(goal_opp.get('dir', 0))}")}

        flags = input_data.get("flags", {})
        if "fc" in flags:
            return {"command": ("kick", f"60 {int(flags['fc'].get('dir', 0))}")}

        return {"command": ("kick", "55 0")}

    def _execute_corner(self, input_data):
        if not self.corner_prepared:
            self.corner_prepared = True
            near_post = 25 if self.side == "l" else -25
            return {"command": ("kick", f"25 {int(near_post)}")}

        self.corner_prepared = False
        mate = self._nearest_teammate(input_data)
        if mate:
            angle = mate.get("dir", 0)
            dist = mate.get("dist", 10)
            power = min(80, max(35, int(20 + dist * 3.5)))
            return {"command": ("kick", f"{power} {int(angle)}"), "say": "pass"}

        goal_opp = input_data.get("goal_opp")
        if goal_opp:
            return {"command": ("kick", f"75 {int(goal_opp.get('dir', 0))}")}

        return {"command": ("kick", "65 0")}

    def _near_sideline(self, input_data):
        flags = input_data.get("flags", {})
        for key, obj in flags.items():
            if (key.startswith("ft") or key.startswith("fb")) and obj.get("dist", 9999) < 10:
                return True
        return False

    def _inward_angle(self, input_data):
        flags = input_data.get("flags", {})
        if "fc" in flags:
            return flags["fc"].get("dir", 0)

        sideline_flag = None
        sideline_dist = 9999
        for key, obj in flags.items():
            if not (key.startswith("ft") or key.startswith("fb")):
                continue
            dist = obj.get("dist", 9999)
            if dist < sideline_dist:
                sideline_dist = dist
                sideline_flag = obj

        if sideline_flag:
            return self._normalize_angle(sideline_flag.get("dir", 0) + 180)

        return 0

    def _nearest_teammate(self, input_data):
        mates = input_data.get("teammates", [])
        nearest = None
        nearest_dist = 9999
        for mate in mates:
            dist = mate.get("dist", 9999)
            if dist < 4:
                continue
            if dist < nearest_dist:
                nearest_dist = dist
                nearest = mate
        return nearest

    def _normalize_angle(self, angle):
        while angle > 180:
            angle -= 360
        while angle < -180:
            angle += 360
        return angle

    def _home_distance(self, input_data):
        flags = input_data.get("flags", {})
        if self.home_flag in flags:
            return flags[self.home_flag].get("dist")
        return None

    def _build_out(self, input_data):
        best_target = input_data.get("best_pass_target")
        goal_opp = input_data.get("goal_opp")
        goal_own = input_data.get("goal_own")

        if best_target:
            angle = best_target.get("dir", 0)
            if not self._toward_own_goal(angle, goal_own):
                dist = best_target.get("dist", 10)
                power = min(90, int(30 + dist * 4))
                return {"command": ("kick", f"{power} {int(angle)}"), "say": "pass"}

        if goal_opp:
            return {"command": ("kick", f"85 {int(goal_opp.get('dir', 0))}")}

        if goal_own:
            safe = self._opposite_angle(goal_own.get("dir", 0))
            return {"command": ("kick", f"90 {int(safe)}")}

        return {"command": ("kick", "70 60")}

    def _toward_own_goal(self, kick_angle, goal_own):
        if not goal_own:
            return False
        diff = abs(kick_angle - goal_own.get("dir", 0))
        if diff > 180:
            diff = 360 - diff
        return diff < 60

    def _opposite_angle(self, angle):
        opposite = angle + 180
        if opposite > 180:
            opposite -= 360
        if opposite < -180:
            opposite += 360
        return opposite
