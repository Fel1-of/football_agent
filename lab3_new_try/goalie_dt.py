def create_goalie_tree():
    return {
        "state": {
            "command": None,
            "ball_dist": 9999,
            "ball_angle": 0,
            "ball_dist_change": 0,
        },
        "root": {
            "exec": lambda mgr, state: state.__setitem__("command", None),
            "next": "checkBallVisible",
        },
        "checkBallVisible": {
            "condition": lambda mgr, state: mgr.getVisible("b"),
            "trueCond": "updateBallInfo",
            "falseCond": "goToGoal",
        },
        "updateBallInfo": {
            "exec": lambda mgr, state: _update_ball_info(mgr, state),
            "next": "checkBallClose",
        },
        "checkBallClose": {
            "condition": lambda mgr, state: state["ball_dist"] < 20,
            "trueCond": "ballCloseLogic",
            "falseCond": "goToGoal",
        },
        "ballCloseLogic": {
            "condition": lambda mgr, state: state["ball_dist"] < 1.5,
            "trueCond": "checkDistChange",
            "falseCond": "checkBallKickable",
        },
        "checkDistChange": {
            "condition": lambda mgr, state: state["ball_dist_change"] < 2,
            "trueCond": "checkBallKickable",
            "falseCond": "tryCatch",
        },
        "tryCatch": {
            "exec": lambda mgr, state: state.__setitem__(
                "command", ("catch", str(int(state["ball_angle"])))
            ),
            "next": "sendCommand",
        },
        "checkBallKickable": {
            "condition": lambda mgr, state: state["ball_dist"] < 0.7,
            "trueCond": "kickBall",
            "falseCond": "approachBall",
        },
        "kickBall": {
            "condition": lambda mgr, state: mgr.getVisible("gl"),
            "trueCond": "kickToGl",
            "falseCond": "kickToFltOrFlb",
        },
        "kickToGl": {
            "exec": lambda mgr, state: state.__setitem__(
                "command", ("kick", f"100 {int(mgr.getAngle('gl'))}")
            ),
            "next": "sendCommand",
        },
        "kickToFltOrFlb": {
            "condition": lambda mgr, state: mgr.getVisible("flt"),
            "trueCond": "kickToFlt",
            "falseCond": "kickToFlbOrWeak",
        },
        "kickToFlt": {
            "exec": lambda mgr, state: state.__setitem__(
                "command", ("kick", f"80 {int(mgr.getAngle('flt'))}")
            ),
            "next": "sendCommand",
        },
        "kickToFlbOrWeak": {
            "condition": lambda mgr, state: mgr.getVisible("flb"),
            "trueCond": "kickToFlb",
            "falseCond": "kickWeak",
        },
        "kickToFlb": {
            "exec": lambda mgr, state: state.__setitem__(
                "command", ("kick", f"80 {int(mgr.getAngle('flb'))}")
            ),
            "next": "sendCommand",
        },
        "kickWeak": {
            "exec": lambda mgr, state: state.__setitem__("command", ("kick", "30 90")),
            "next": "sendCommand",
        },
        "approachBall": {
            "condition": lambda mgr, state: abs(state["ball_angle"]) > 5,
            "trueCond": "turnToBall",
            "falseCond": "dashToBall",
        },
        "turnToBall": {
            "exec": lambda mgr, state: state.__setitem__(
                "command", ("turn", str(int(state["ball_angle"])))
            ),
            "next": "sendCommand",
        },
        "dashToBall": {
            "exec": lambda mgr, state: state.__setitem__("command", ("dash", "100")),
            "next": "sendCommand",
        },
        "goToGoal": {
            "condition": lambda mgr, state: mgr.getVisible("gr"),
            "trueCond": "checkGoalDist",
            "falseCond": "searchGoal",
        },
        "searchGoal": {
            "exec": lambda mgr, state: state.__setitem__("command", ("turn", "60")),
            "next": "sendCommand",
        },
        "checkGoalDist": {
            "condition": lambda mgr, state: mgr.getDistance("gr") > 5,
            "trueCond": "moveToGoal",
            "falseCond": "positionInGoal",
        },
        "moveToGoal": {
            "condition": lambda mgr, state: abs(mgr.getAngle("gr")) > 5,
            "trueCond": "turnToGoal",
            "falseCond": "dashToGoal",
        },
        "turnToGoal": {
            "exec": lambda mgr, state: state.__setitem__(
                "command", ("turn", str(int(mgr.getAngle("gr"))))
            ),
            "next": "sendCommand",
        },
        "dashToGoal": {
            "exec": lambda mgr, state: state.__setitem__("command", ("dash", "80")),
            "next": "sendCommand",
        },
        "positionInGoal": {
            "condition": lambda mgr, state: _need_adjustment(mgr),
            "trueCond": "adjustPosition",
            "falseCond": "faceBall",
        },
        "adjustPosition": {
            "exec": lambda mgr, state: _adjust_position(mgr, state),
            "next": "sendCommand",
        },
        "faceBall": {
            "condition": lambda mgr, state: mgr.getVisible("b"),
            "trueCond": "faceBallCheck",
            "falseCond": "faceBallSearch",
        },
        "faceBallCheck": {
            "condition": lambda mgr, state: abs(mgr.getAngle("b")) > 5,
            "trueCond": "turnFaceBall",
            "falseCond": "standStill",
        },
        "turnFaceBall": {
            "exec": lambda mgr, state: state.__setitem__(
                "command", ("turn", str(int(mgr.getAngle("b"))))
            ),
            "next": "sendCommand",
        },
        "faceBallSearch": {
            "exec": lambda mgr, state: state.__setitem__("command", ("turn", "30")),
            "next": "sendCommand",
        },
        "standStill": {
            "exec": lambda mgr, state: state.__setitem__("command", ("turn", "1")),
            "next": "sendCommand",
        },
        "sendCommand": {
            "command": lambda mgr, state: state["command"],
        },
    }


def _update_ball_info(mgr, state):
    state["ball_dist"] = mgr.getDistance("b")
    state["ball_dist_change"] = mgr.getDistChange("b")
    state["ball_angle"] = mgr.getAngle("b")


def _need_adjustment(mgr):
    if mgr.getVisible("fprc"):
        dist = mgr.getDistance("fprc")
        if dist < 10 or dist > 18:
            return True
        if abs(mgr.getAngle("fprc")) > 30:
            return True
    return False


def _adjust_position(mgr, state):
    if mgr.getVisible("fprc"):
        dist = mgr.getDistance("fprc")
        angle = mgr.getAngle("fprc")
        if dist > 18:
            if mgr.getVisible("gr") and abs(mgr.getAngle("gr")) > 5:
                state["command"] = ("turn", str(int(mgr.getAngle("gr"))))
            else:
                state["command"] = ("dash", "50")
        elif dist < 10:
            state["command"] = ("dash", "-30")
        elif abs(angle) > 30:
            state["command"] = ("turn", str(int(angle / 2)))
        else:
            state["command"] = ("turn", "1")
    else:
        state["command"] = ("turn", "30")
