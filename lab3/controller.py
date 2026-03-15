import copy


def _clone_tree(tree):
    return copy.deepcopy(tree)


class DecisionTreeManager:
    def __init__(self):
        self.p = {}

    def set_perception(self, perception):
        self.p = perception or {}

    def get_visible(self, key):
        return self.get_object(key) is not None

    def get_distance(self, key):
        obj = self.get_object(key)
        return None if obj is None else float(obj["dist"])

    def get_angle(self, key):
        obj = self.get_object(key)
        return None if obj is None else float(obj["angle"])

    def get_object(self, key):
        if key == "b":
            return self.p.get("ball")
        for item in self.p.get("flags", []):
            if item.get("key") == key:
                return item
        for item in self.p.get("teammates", []):
            if item.get("key") == key:
                return item
        return None

    def get_teammates(self):
        return list(self.p.get("teammates", []))

    def get_action(self, dt, perception):
        self.set_perception(perception)

        def execute(title):
            node = dt[title]
            if callable(node.get("exec")):
                node["exec"](self, dt["state"])
                return execute(node["next"])
            if callable(node.get("condition")):
                branch = node["trueCond"] if node["condition"](self, dt["state"]) else node["falseCond"]
                return execute(branch)
            if callable(node.get("command")):
                return node["command"](self, dt["state"])
            raise RuntimeError(f"Unexpected node in DT: {title}")

        return execute("root")


class Controller:
    """Контроллер на деревьях решений для полевого игрока и вратаря."""

    def __init__(self, actions=None, is_goalie=False, squad_size=2):
        self.actions = list(actions or [])
        self.is_goalie = is_goalie
        self.squad_size = max(2, min(3, int(squad_size)))
        self.unum = None
        self.manager = DecisionTreeManager()
        self.player_tree = _clone_tree(self._build_player_tree())
        self.goalie_tree = _clone_tree(self._build_goalie_tree())
        self._sync_actions()

    def set_unum(self, unum):
        self.unum = unum

    def on_goal(self):
        self.player_tree["state"]["next"] = 0
        self.goalie_tree["state"]["command"] = None

    def set_actions(self, actions, reset_index=True):
        self.actions = list(actions or [])
        self._sync_actions()
        if reset_index:
            self.player_tree["state"]["next"] = 0

    def decide(self, play_on, flags_list, ball, teammates=None):
        if not play_on:
            return None

        perception = {
            "flags": list(flags_list or []),
            "ball": ball,
            "teammates": list(teammates or []),
        }
        tree = self.goalie_tree if self.is_goalie else self.player_tree
        return self.manager.get_action(tree, perception)

    def _sync_actions(self):
        self.player_tree["state"]["sequence"] = list(self.actions)

    def _build_player_tree(self):
        return {
            "state": {
                "next": 0,
                "sequence": [],
                "command": None,
                "action": None,
                "role": "leader",
                "mate": None,
                "desired_angle": 30.0,
            },
            "root": {
                "exec": self._player_root_exec,
                "next": "formationCheck",
            },
            "formationCheck": {
                "condition": lambda mgr, state: state["role"] == "leader" or state["mate"] is None,
                "trueCond": "routeGoalVisible",
                "falseCond": "mateTooClose",
            },
            "mateTooClose": {
                "condition": lambda mgr, state: state["mate"]["dist"] < 1.0 and abs(state["mate"]["angle"]) < 40.0,
                "trueCond": "avoidMate",
                "falseCond": "mateFar",
            },
            "avoidMate": {
                "exec": lambda mgr, state: self._set_command(state, "turn", "30"),
                "next": "sendCommand",
            },
            "mateFar": {
                "condition": lambda mgr, state: state["mate"]["dist"] > 10.0,
                "trueCond": "mateFarTurn",
                "falseCond": "mateAngleAdjust",
            },
            "mateFarTurn": {
                "condition": lambda mgr, state: abs(state["mate"]["angle"]) > 5.0,
                "trueCond": "turnToMate",
                "falseCond": "fastDashToMate",
            },
            "turnToMate": {
                "exec": lambda mgr, state: self._set_command(state, "turn", f"{state['mate']['angle']:.2f}"),
                "next": "sendCommand",
            },
            "fastDashToMate": {
                "exec": lambda mgr, state: self._set_command(state, "dash", "80"),
                "next": "sendCommand",
            },
            "mateAngleAdjust": {
                "condition": self._follower_needs_angle_adjustment,
                "trueCond": "turnToFormationSlot",
                "falseCond": "followDash",
            },
            "turnToFormationSlot": {
                "exec": self._turn_to_slot,
                "next": "sendCommand",
            },
            "followDash": {
                "exec": self._follow_dash,
                "next": "sendCommand",
            },
            "routeGoalVisible": {
                "condition": self._current_target_visible,
                "trueCond": "routeActionType",
                "falseCond": "searchRouteTarget",
            },
            "searchRouteTarget": {
                "exec": lambda mgr, state: self._set_command(state, "turn", "90"),
                "next": "sendCommand",
            },
            "routeActionType": {
                "condition": lambda mgr, state: state["action"] is not None and state["action"]["act"] == "flag",
                "trueCond": "flagSeek",
                "falseCond": "ballSeek",
            },
            "flagSeek": {
                "condition": lambda mgr, state: mgr.get_distance(state["action"]["fl"]) < 3.0,
                "trueCond": "closeFlag",
                "falseCond": "routeFarGoal",
            },
            "closeFlag": {
                "exec": self._advance_route,
                "next": "routeGoalVisible",
            },
            "routeFarGoal": {
                "condition": lambda mgr, state: abs(mgr.get_angle(state["action"]["fl"])) > 5.0,
                "trueCond": "rotateToRouteTarget",
                "falseCond": "runToRouteTarget",
            },
            "rotateToRouteTarget": {
                "exec": self._rotate_to_route_target,
                "next": "sendCommand",
            },
            "runToRouteTarget": {
                "exec": self._run_to_route_target,
                "next": "sendCommand",
            },
            "ballSeek": {
                "condition": lambda mgr, state: mgr.get_distance("b") is not None and mgr.get_distance("b") <= 0.7,
                "trueCond": "closeBall",
                "falseCond": "routeFarGoal",
            },
            "closeBall": {
                "condition": lambda mgr, state: mgr.get_visible(state["action"]["goal"]),
                "trueCond": "kickToGoal",
                "falseCond": "kickToSearchAngle",
            },
            "kickToGoal": {
                "exec": self._kick_to_goal,
                "next": "sendCommand",
            },
            "kickToSearchAngle": {
                "exec": lambda mgr, state: self._set_command(state, "kick", "15 45"),
                "next": "sendCommand",
            },
            "sendCommand": {
                "command": lambda mgr, state: state["command"],
            },
        }

    def _build_goalie_tree(self):
        return {
            "state": {
                "command": None,
            },
            "root": {
                "exec": lambda mgr, state: state.__setitem__("command", None),
                "next": "ballClose",
            },
            "ballClose": {
                "condition": lambda mgr, state: mgr.get_distance("b") is not None and mgr.get_distance("b") <= 2.0,
                "trueCond": "canCatchBall",
                "falseCond": "ballNear",
            },
            "canCatchBall": {
                "condition": lambda mgr, state: mgr.get_angle("b") is not None and abs(mgr.get_angle("b")) <= 25.0,
                "trueCond": "catchBall",
                "falseCond": "kickBallAway",
            },
            "catchBall": {
                "exec": lambda mgr, state: self._set_command(state, "catch", f"{mgr.get_angle('b'):.2f}"),
                "next": "sendCommand",
            },
            "kickBallAway": {
                "exec": self._goalie_kick_ball,
                "next": "sendCommand",
            },
            "ballNear": {
                "condition": lambda mgr, state: mgr.get_distance("b") is not None and mgr.get_distance("b") <= 15.0,
                "trueCond": "approachBall",
                "falseCond": "returnToGoal",
            },
            "approachBall": {
                "condition": lambda mgr, state: abs(mgr.get_angle("b")) > 7.0,
                "trueCond": "turnToBall",
                "falseCond": "dashToBall",
            },
            "turnToBall": {
                "exec": lambda mgr, state: self._set_command(state, "turn", f"{mgr.get_angle('b'):.2f}"),
                "next": "sendCommand",
            },
            "dashToBall": {
                "exec": lambda mgr, state: self._set_command(state, "dash", f"{min(90.0, max(40.0, mgr.get_distance('b') * 12.0)):.2f}"),
                "next": "sendCommand",
            },
            "returnToGoal": {
                "condition": lambda mgr, state: mgr.get_visible("gr") and mgr.get_distance("gr") > 5.0,
                "trueCond": "moveToGoalCenter",
                "falseCond": "alignPenaltyCenter",
            },
            "moveToGoalCenter": {
                "exec": self._move_to_goal_center,
                "next": "sendCommand",
            },
            "alignPenaltyCenter": {
                "condition": lambda mgr, state: mgr.get_visible("fprc"),
                "trueCond": "adjustPenaltyCenter",
                "falseCond": "searchBall",
            },
            "adjustPenaltyCenter": {
                "condition": self._goalie_needs_penalty_adjustment,
                "trueCond": "movePenaltyCenter",
                "falseCond": "faceBall",
            },
            "movePenaltyCenter": {
                "exec": self._move_penalty_center,
                "next": "sendCommand",
            },
            "faceBall": {
                "condition": lambda mgr, state: mgr.get_visible("b"),
                "trueCond": "turnToBall",
                "falseCond": "searchBall",
            },
            "searchBall": {
                "exec": lambda mgr, state: self._set_command(state, "turn", "60"),
                "next": "sendCommand",
            },
            "sendCommand": {
                "command": lambda mgr, state: state["command"],
            },
        }

    def _player_root_exec(self, mgr, state):
        state["command"] = None
        state["action"] = self._current_action(state)
        state["role"], state["mate"], state["desired_angle"] = self._resolve_role(mgr.get_teammates())

    def _resolve_role(self, teammates):
        visible = [mate for mate in teammates if mate.get("unum") is not None]
        if self.unum is None or not visible:
            return "leader", None, 30.0

        ordered = sorted([self.unum] + [mate["unum"] for mate in visible])
        rank = ordered.index(self.unum)
        if rank == 0:
            return "leader", None, 30.0

        leader_candidates = [mate for mate in visible if mate["unum"] < self.unum]
        mate = min(leader_candidates or visible, key=lambda item: item["dist"])
        if self.squad_size == 2 or rank == 1:
            return "support_left", mate, 30.0
        return "support_right", mate, -30.0

    def _current_action(self, state):
        sequence = state["sequence"]
        if not sequence:
            return None
        return sequence[state["next"] % len(sequence)]

    def _current_target_visible(self, mgr, state):
        action = state["action"]
        if action is None:
            return False
        return mgr.get_visible(action["fl"])

    def _advance_route(self, mgr, state):
        if not state["sequence"]:
            return
        state["next"] = (state["next"] + 1) % len(state["sequence"])
        state["action"] = self._current_action(state)

    def _rotate_to_route_target(self, mgr, state):
        angle = mgr.get_angle(state["action"]["fl"])
        self._set_command(state, "turn", f"{angle:.2f}")

    def _run_to_route_target(self, mgr, state):
        dist = mgr.get_distance(state["action"]["fl"])
        if state["action"]["act"] == "kick":
            power = max(20.0, min(60.0, dist * 18.0))
        else:
            power = max(40.0, min(100.0, dist * 10.0))
        self._set_command(state, "dash", f"{power:.2f}")

    def _kick_to_goal(self, mgr, state):
        angle = mgr.get_angle(state["action"]["goal"])
        self._set_command(state, "kick", f"100 {angle:.2f}")

    def _follower_needs_angle_adjustment(self, mgr, state):
        angle = state["mate"]["angle"]
        desired = state["desired_angle"]
        return angle > desired + 10.0 or angle < desired - 5.0

    def _turn_to_slot(self, mgr, state):
        delta = state["mate"]["angle"] - state["desired_angle"]
        self._set_command(state, "turn", f"{delta:.2f}")

    def _follow_dash(self, mgr, state):
        power = 20 if state["mate"]["dist"] < 7.0 else 40
        self._set_command(state, "dash", str(power))

    def _move_to_goal_center(self, mgr, state):
        angle = mgr.get_angle("gr")
        dist = mgr.get_distance("gr")
        if abs(angle) > 5.0:
            self._set_command(state, "turn", f"{angle:.2f}")
            return
        self._set_command(state, "dash", f"{min(80.0, max(30.0, dist * 10.0)):.2f}")

    def _goalie_needs_penalty_adjustment(self, mgr, state):
        dist = mgr.get_distance("fprc")
        return dist < 12.0 or dist > 16.0 or abs(mgr.get_angle("fprc")) > 7.0

    def _move_penalty_center(self, mgr, state):
        angle = mgr.get_angle("fprc")
        dist = mgr.get_distance("fprc")
        if abs(angle) > 7.0:
            self._set_command(state, "turn", f"{angle:.2f}")
            return
        if dist < 12.0:
            self._set_command(state, "dash", "-20")
            return
        self._set_command(state, "dash", "40")

    def _goalie_kick_ball(self, mgr, state):
        for target in ("gl", "flt", "flb"):
            if mgr.get_visible(target):
                self._set_command(state, "kick", f"100 {mgr.get_angle(target):.2f}")
                return
        if abs(mgr.get_angle("b")) > 10.0:
            self._set_command(state, "turn", f"{mgr.get_angle('b'):.2f}")
            return
        self._set_command(state, "kick", "40 135")

    @staticmethod
    def _set_command(state, name, value):
        state["command"] = {"n": name, "v": value}
