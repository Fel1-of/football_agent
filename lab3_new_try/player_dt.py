FL = "flag"
KI = "kick"


def create_player_tree(actions):
    return {
        "state": {
            "next": 0,
            "sequence": list(actions or []),
            "action": None,
            "command": None,
            "teammate_dist": 9999,
            "teammate_angle": 0,
        },
        "root": {
            "exec": lambda mgr, state: _root_exec(mgr, state),
            "next": "checkTeammates",
        },
        "checkTeammates": {
            "condition": lambda mgr, state: mgr.getTeammateCount() == 0,
            "trueCond": "leaderGoalVisible",
            "falseCond": "followerInit",
        },
        "leaderGoalVisible": {
            "condition": lambda mgr, state: mgr.getVisible(state["action"]["fl"]),
            "trueCond": "leaderRootNext",
            "falseCond": "leaderRotate",
        },
        "leaderRotate": {
            "exec": lambda mgr, state: state.__setitem__("command", ("turn", "90")),
            "next": "sendCommand",
        },
        "leaderRootNext": {
            "condition": lambda mgr, state: state["action"]["act"] == FL,
            "trueCond": "flagSeek",
            "falseCond": "ballSeek",
        },
        "flagSeek": {
            "condition": lambda mgr, state: mgr.getDistance(state["action"]["fl"]) < 3,
            "trueCond": "closeFlag",
            "falseCond": "farGoal",
        },
        "closeFlag": {
            "exec": lambda mgr, state: _advance_target(state),
            "next": "leaderRootNext",
        },
        "farGoal": {
            "condition": lambda mgr, state: abs(mgr.getAngle(state["action"]["fl"])) > 4,
            "trueCond": "rotateToGoal",
            "falseCond": "runToGoal",
        },
        "rotateToGoal": {
            "exec": lambda mgr, state: state.__setitem__(
                "command", ("turn", str(int(mgr.getAngle(state["action"]["fl"]))))
            ),
            "next": "sendCommand",
        },
        "runToGoal": {
            "exec": lambda mgr, state: state.__setitem__("command", ("dash", "70")),
            "next": "sendCommand",
        },
        "ballSeek": {
            "condition": lambda mgr, state: mgr.getDistance(state["action"]["fl"]) < 0.7,
            "trueCond": "closeBall",
            "falseCond": "farGoal",
        },
        "closeBall": {
            "condition": lambda mgr, state: mgr.getVisible(state["action"].get("goal", "gr")),
            "trueCond": "ballGoalVisible",
            "falseCond": "ballGoalInvisible",
        },
        "ballGoalVisible": {
            "exec": lambda mgr, state: state.__setitem__(
                "command", ("kick", f"100 {int(mgr.getAngle(state['action'].get('goal', 'gr')))}")
            ),
            "next": "sendCommand",
        },
        "ballGoalInvisible": {
            "exec": lambda mgr, state: state.__setitem__("command", ("kick", "10 45")),
            "next": "sendCommand",
        },
        "followerInit": {
            "exec": lambda mgr, state: _compute_follower_vars(mgr, state),
            "next": "followerTooClose",
        },
        "followerTooClose": {
            "condition": lambda mgr, state: state["teammate_dist"] < 1 and abs(state["teammate_angle"]) < 40,
            "trueCond": "followerAvoidCollision",
            "falseCond": "followerCheckFar",
        },
        "followerAvoidCollision": {
            "exec": lambda mgr, state: state.__setitem__("command", ("turn", "30")),
            "next": "sendCommand",
        },
        "followerCheckFar": {
            "condition": lambda mgr, state: state["teammate_dist"] > 10,
            "trueCond": "followerFarApproach",
            "falseCond": "followerCheckAngle",
        },
        "followerFarApproach": {
            "condition": lambda mgr, state: abs(state["teammate_angle"]) > 5,
            "trueCond": "followerFarTurn",
            "falseCond": "followerFarDash",
        },
        "followerFarTurn": {
            "exec": lambda mgr, state: state.__setitem__(
                "command", ("turn", str(int(state["teammate_angle"])))
            ),
            "next": "sendCommand",
        },
        "followerFarDash": {
            "exec": lambda mgr, state: state.__setitem__("command", ("dash", "90")),
            "next": "sendCommand",
        },
        "followerCheckAngle": {
            "condition": lambda mgr, state: state["teammate_angle"] > 40 or state["teammate_angle"] < 25,
            "trueCond": "followerAdjustAngle",
            "falseCond": "followerCheckDist",
        },
        "followerAdjustAngle": {
            "exec": lambda mgr, state: state.__setitem__(
                "command", ("turn", str(int(state["teammate_angle"] - 30)))
            ),
            "next": "sendCommand",
        },
        "followerCheckDist": {
            "condition": lambda mgr, state: state["teammate_dist"] < 7,
            "trueCond": "followerSlowDash",
            "falseCond": "followerMediumDash",
        },
        "followerSlowDash": {
            "exec": lambda mgr, state: state.__setitem__("command", ("dash", "50")),
            "next": "sendCommand",
        },
        "followerMediumDash": {
            "exec": lambda mgr, state: state.__setitem__("command", ("dash", "70")),
            "next": "sendCommand",
        },
        "sendCommand": {
            "command": lambda mgr, state: state["command"],
        },
    }


def _root_exec(mgr, state):
    if not state["sequence"]:
        state["action"] = {"act": FL, "fl": "fc"}
        state["command"] = None
        return
    if state["next"] >= len(state["sequence"]):
        state["next"] = 0
    state["action"] = state["sequence"][state["next"]]
    state["command"] = None


def _advance_target(state):
    state["next"] += 1
    if state["next"] >= len(state["sequence"]):
        state["next"] = 0
    state["action"] = state["sequence"][state["next"]]


def _compute_follower_vars(mgr, state):
    closest = mgr.getClosestTeammate()
    if closest:
        _, obj = closest
        state["teammate_dist"] = obj.get("dist", 9999)
        state["teammate_angle"] = obj.get("dir", 0)
    else:
        state["teammate_dist"] = 9999
        state["teammate_angle"] = 0
    state["command"] = None
