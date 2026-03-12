class Controller:
    """Маршрутный контроллер"""

    def __init__(self, actions=None):
        self.actions = list(actions or [])
        self.index = 0
        self.close_flag_dist = 3.0
        self.close_ball_dist = 0.5
        self.turn_tolerance = 5.0
        self.search_turn = 90.0

    def on_goal(self):
        """После гола маршрут повторяется с начала."""
        self.index = 0

    def set_actions(self, actions, reset_index=True):
        self.actions = list(actions or [])
        if reset_index:
            self.index = 0

    def decide(self, play_on, flags_list, ball):
        """
        Возвращает команду словарем: {"n": "turn|dash|kick", "v": "..."} или None.
        Решение принимается только после play_on.
        """
        if not play_on or not self.actions:
            return None

        # Если текущий шаг уже достигнут, переходим дальше и пробуем выбрать команду снова.
        for _ in range(len(self.actions)):
            action = self.actions[self.index]
            kind = action.get("act")
            if kind == "flag":
                command, reached = self._for_flag(action, flags_list)
                if reached:
                    self._next_action()
                    continue
                return command
            if kind == "kick":
                return self._for_kick(action, flags_list, ball)
            return {"n": "turn", "v": str(self.search_turn)}

        return None

    def _for_flag(self, action, flags_list):
        target = self._find_visible(flags_list, action.get("fl"))
        if not target:
            return {"n": "turn", "v": str(self.search_turn)}, False

        dist = float(target["dist"])
        angle = float(target["angle"])
        if dist < self.close_flag_dist:
            return None, True
        if abs(angle) > self.turn_tolerance:
            return {"n": "turn", "v": f"{angle:.2f}"}, False
        return {"n": "dash", "v": f"{self._dash_power(dist):.2f}"}, False

    def _for_kick(self, action, flags_list, ball):
        if not ball:
            return {"n": "turn", "v": str(self.search_turn)}

        ball_dist = float(ball["dist"])
        ball_angle = float(ball["angle"])
        if ball_dist > self.close_ball_dist:
            if abs(ball_angle) > self.turn_tolerance:
                return {"n": "turn", "v": f"{ball_angle:.2f}"}
            return {"n": "dash", "v": f"{self._ball_dash_power(ball_dist):.2f}"}

        goal = self._find_visible(flags_list, action.get("goal"))
        if goal:
            return {"n": "kick", "v": f"100 {float(goal['angle']):.2f}"}
        return {"n": "kick", "v": "10 45"}

    def _dash_power(self, dist):
        return max(30.0, min(100.0, dist * 12.0))

    def _ball_dash_power(self, dist):
        # К мячу подходим мягче, чтобы не пролетать точку удара.
        return max(8.0, min(50.0, dist * 20.0))

    def _find_visible(self, flags_list, key):
        if not key:
            return None
        for item in flags_list:
            if item.get("key") == key:
                return item
        return None

    def _next_action(self):
        self.index = (self.index + 1) % len(self.actions)
