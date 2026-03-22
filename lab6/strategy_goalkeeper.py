from control_hierarchy import ControllerLayer


class GoalkeeperStrategy(ControllerLayer):
    def __init__(self, side):
        super().__init__()
        self.side = side
        self.last_mode = "idle"
        self.rush_steps = 0
        self.max_rush_distance = 18  # метров от ворот

    def process(self, input_data):
        if not input_data.get("play_on", False):
            self.last_mode = "reset"
            return {"new_action": "return_home"}

        ball = input_data.get("ball")
        dist_home = self._distance_to_home(input_data)
        teammate_near_ball = input_data.get("teammate_near_ball", False)

        if input_data.get("can_kick"):
            self.last_mode = "kick"
            self.rush_steps = 0
            return self._clear_or_pass(input_data)

        if ball:
            ball_dist = ball.get("dist", 9999)
            ball_angle = ball.get("dir", 0)
            ball_dist_change = ball.get("dist_change", 0)

            if ball_dist < 1.0 and (dist_home is None or dist_home < 8):
                self.last_mode = "catch"
                self.rush_steps = 0
                return ("catch", str(int(ball_angle)))

            is_closest = input_data.get("i_am_closest_to_ball", True)
            close_threat = ball_dist < 10
            medium_threat = ball_dist < 14 and (dist_home is None or dist_home < 6)
            incoming_threat = ball_dist < 20 and ball_dist_change < -0.25 and (dist_home is None or dist_home < 7)
            within_box = (dist_home is None) or (dist_home <= self.max_rush_distance)
            should_rush = within_box and (close_threat or medium_threat or incoming_threat) and (is_closest or ball_dist < 8 or not teammate_near_ball)

            if should_rush:
                self.last_mode = "rush"
                self.rush_steps += 1
                if self.rush_steps > 18 and (ball_dist > 6 or not within_box):
                    self.last_mode = "recover"
                    self.rush_steps = 0
                    return {"new_action": "return_home"}
                return {"new_action": "go_to_ball"}
            self.rush_steps = 0

            if dist_home and dist_home > 4:
                self.last_mode = "recover"
                return {"new_action": "return_home"}

            if abs(ball_angle) > 6:
                return ("turn", str(int(ball_angle)))

            self.last_mode = "track"
            return {"new_action": "watch_ball"}

        if dist_home and dist_home > 4:
            self.last_mode = "recover"
            self.rush_steps = 0
            return {"new_action": "return_home"}

        self.rush_steps = 0
        return ("turn", "35")

    def _distance_to_home(self, input_data):
        home_key = "gl" if self.side == "l" else "gr"
        flags = input_data.get("flags", {})
        if home_key in flags:
            return flags[home_key].get("dist")
        goal_own = input_data.get("goal_own")
        if goal_own:
            return goal_own.get("dist")
        return None

    def _clear_or_pass(self, input_data):
        best_target = input_data.get("best_pass_target")
        goal_opp = input_data.get("goal_opp")
        goal_own = input_data.get("goal_own")
        nearest = self._nearest_teammate(input_data)

        if best_target:
            angle = best_target.get("dir", 0)
            if not self._toward_own_goal(angle, goal_own, sector=75):
                dist = best_target.get("dist", 10)
                power = min(100, max(60, int(35 + dist * 5)))
                return {"command": ("kick", f"{power} {int(angle)}"), "say": "pass"}

        if nearest:
            angle = nearest.get("dir", 0)
            if not self._toward_own_goal(angle, goal_own, sector=75):
                dist = nearest.get("dist", 10)
                power = min(95, max(58, int(30 + dist * 4)))
                return {"command": ("kick", f"{power} {int(angle)}"), "say": "pass"}

        if goal_opp:
            safe_angle = self._safe_clear_angle(goal_own, preferred=goal_opp.get("dir", 0))
            return {"command": ("kick", f"100 {int(safe_angle)}")}

        if goal_own:
            safe_angle = self._safe_clear_angle(goal_own)
            return {"command": ("kick", f"95 {int(safe_angle)}")}

        return {"command": ("kick", "95 30")}

    def _toward_own_goal(self, kick_angle, goal_own, sector=60):
        if not goal_own:
            return False
        diff = abs(kick_angle - goal_own.get("dir", 0))
        if diff > 180:
            diff = 360 - diff
        return diff < sector

    def _opposite_angle(self, angle):
        opposite = angle + 180
        if opposite > 180:
            opposite -= 360
        if opposite < -180:
            opposite += 360
        return opposite

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

    def _safe_clear_angle(self, goal_own, preferred=None):
        if not goal_own:
            if preferred is not None:
                return self._normalize_angle(preferred)
            return 30

        own_angle = goal_own.get("dir", 0)
        opposite = self._opposite_angle(own_angle)
        candidates = []
        if preferred is not None:
            candidates.append(preferred)
        candidates.extend([
            opposite,
            self._normalize_angle(opposite + 30),
            self._normalize_angle(opposite - 30),
            self._normalize_angle(opposite + 55),
            self._normalize_angle(opposite - 55),
        ])

        for angle in candidates:
            if not self._toward_own_goal(angle, goal_own, sector=75):
                return self._normalize_angle(angle)
        return self._normalize_angle(opposite)

    def _normalize_angle(self, angle):
        while angle > 180:
            angle -= 360
        while angle < -180:
            angle += 360
        return angle
