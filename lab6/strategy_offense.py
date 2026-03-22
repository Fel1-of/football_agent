from control_hierarchy import ControllerLayer


SUPPORT_FLAGS = {
    "forward_top": {"l": "frt10", "r": "flt10"},
    "forward_center": {"l": "fprc", "r": "fplc"},
    "forward_bottom": {"l": "frb10", "r": "flb10"},
    "midfielder_top": {"l": "fct", "r": "fct"},
    "midfielder_center": {"l": "fc", "r": "fc"},
    "midfielder_bottom": {"l": "fcb", "r": "fcb"},
}


class OffenseStrategy(ControllerLayer):
    def __init__(self, side, home_flag, attack_flag, role_key="forward_center"):
        super().__init__()
        self.side = side
        self.home_flag = home_flag
        self.attack_flag = attack_flag
        self.role_key = role_key
        self.last_mode = "shape"
        self.restart_mode = ""
        self.throw_in_prepared = False
        self.corner_prepared = False

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

            target_flag = self._support_flag() if is_throw else self._box_support_flag()
            return {"new_action": {"action": "go_to_flag", "flag": target_flag}}

        if input_data.get("can_kick"):
            self.last_mode = "kick"
            return self._attack_with_ball(input_data)

        if input_data.get("pass_to_me"):
            self.last_mode = "receive"
            return {"new_action": "receive_pass"}

        ball = input_data.get("ball")
        if not ball:
            if self.last_mode in ("kick", "press", "receive"):
                self.last_mode = "shape"
                return {"new_action": {"action": "go_to_flag", "flag": self.attack_flag}}
            return {"new_action": "return_home"}

        ball_dist = ball.get("dist", 9999)
        closest = input_data.get("i_am_closest_to_ball", True)
        teammate_near = input_data.get("teammate_near_ball", False)
        teammates_closer = input_data.get("teammates_closer_to_ball", 0)
        can_second_press = teammates_closer <= 1 and ball_dist <= 45

        if teammates_closer >= 3 or (teammate_near and teammates_closer >= 2 and not closest):
            self.last_mode = "support"
            return self._support_movement(ball)

        if self.role_key.startswith("midfielder"):
            if (closest and ball_dist <= 30 and teammates_closer == 0) or can_second_press:
                self.last_mode = "press"
                return {"new_action": "go_to_ball"}
            self.last_mode = "support"
            return self._support_movement(ball)

        if (closest and ball_dist <= 40) or can_second_press:
            self.last_mode = "press"
            return {"new_action": "go_to_ball"}

        if ball_dist > 30:
            self.last_mode = "support"
            return self._support_movement(ball)

        self.last_mode = "press"
        return {"new_action": "go_to_ball"}

    def _support_movement(self, ball):
        if abs(ball.get("dir", 0)) > 18:
            return ("turn", str(int(ball.get("dir", 0))))

        support_flag = self._support_flag()
        return {"new_action": {"action": "go_to_flag", "flag": support_flag}}

    def _support_flag(self):
        per_side = SUPPORT_FLAGS.get(self.role_key)
        if not per_side:
            return self.attack_flag
        return per_side.get(self.side, self.attack_flag)

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
        if role.startswith("midfielder_center") or role == "forward_center":
            return True
        if role.startswith("midfielder") and "center" not in role:
            return True
        # fallback: тот, кто ближе всех к мячу
        ball = input_data.get("ball")
        return bool(ball and input_data.get("i_am_closest_to_ball", True))

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
            power = min(85, max(35, int(18 + dist * 4)))
            return {"command": ("kick", f"{power} {int(angle)}"), "say": "pass"}

        goal_opp = input_data.get("goal_opp")
        if goal_opp:
            angle = goal_opp.get("dir", 0)
            return {"command": ("kick", f"80 {int(angle)}")}

        flags = input_data.get("flags", {})
        if "fc" in flags:
            return {"command": ("kick", f"65 {int(flags['fc'].get('dir', 0))}")}

        return {"command": ("kick", "60 0")}

    def _execute_corner(self, input_data):
        if not self.corner_prepared:
            self.corner_prepared = True
            near_post = 25 if self.side == "l" else -25
            return {"command": ("kick", f"30 {int(near_post)}")}

        self.corner_prepared = False
        target = self._best_box_target(input_data)
        if target:
            angle = target.get("dir", 0)
            dist = target.get("dist", 12)
            power = min(95, max(40, int(28 + dist * 4)))
            return {"command": ("kick", f"{power} {int(angle)}"), "say": "pass"}

        goal_opp = input_data.get("goal_opp")
        if goal_opp:
            angle = goal_opp.get("dir", 0)
            return {"command": ("kick", f"85 {int(angle)}")}

        return {"command": ("kick", "70 0")}

    def _best_box_target(self, input_data):
        mates = input_data.get("teammates", [])
        best = None
        best_score = -9999
        for m in mates:
            dist = m.get("dist", 9999)
            if dist < 4 or dist > 25:
                continue
            angle = m.get("dir", 0)
            score = 50 - abs(dist - 12) - abs(angle) * 0.5
            if score > best_score:
                best_score = score
                best = m
        return best

    def _box_support_flag(self):
        # Простое распределение точек в штрафной соперника
        if self.side == "l":
            near = "fprc"
            far = "fprb"
            top = "fprt"
        else:
            near = "fplc"
            far = "fplb"
            top = "fplt"

        role = self.role_key
        if role.startswith("forward_top"):
            return top
        if role.startswith("forward_bottom"):
            return far
        if role.startswith("forward_center") or role.startswith("midfielder_center"):
            return near
        if role.startswith("midfielder_top"):
            return top
        if role.startswith("midfielder_bottom"):
            return far
        return near

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

    def _attack_with_ball(self, input_data):
        goal_opp = input_data.get("goal_opp")
        goal_own = input_data.get("goal_own")
        best_target = input_data.get("best_pass_target")

        if goal_opp:
            dist = goal_opp.get("dist", 9999)
            direction = goal_opp.get("dir", 0)

            if dist <= 24:
                power = min(100, int(65 + dist))
                return {"command": ("kick", f"{power} {int(direction)}")}

            if best_target:
                t_dir = best_target.get("dir", 0)
                t_dist = best_target.get("dist", 10)
                if not self._toward_own_goal(t_dir, goal_own):
                    power = min(95, int(28 + t_dist * 4))
                    return {"command": ("kick", f"{power} {int(t_dir)}"), "say": "pass"}

            power = min(100, int(40 + dist))
            return {"command": ("kick", f"{power} {int(direction)}")}

        if best_target:
            t_dir = best_target.get("dir", 0)
            t_dist = best_target.get("dist", 10)
            if not self._toward_own_goal(t_dir, goal_own):
                power = min(90, int(24 + t_dist * 4))
                return {"command": ("kick", f"{power} {int(t_dir)}"), "say": "pass"}

        if goal_own:
            safe = self._opposite_angle(goal_own.get("dir", 0))
            return {"command": ("kick", f"35 {int(safe)}")}

        return {"command": ("kick", "25 40")}

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
