# player_size + ball_size + catchable_area ≈ 0.3 + 0.085 + 1.2 = 1.585
CATCHABLE_DIST = 1.585
KICKABLE_DIST = 0.5


def _kick_to_away_goal(mgr, state):
    flag = mgr.getAwayGoalFlag()
    state["command"] = ("kick", f"100 {int(mgr.getAngle(flag))}")


def _kick_to_flag(mgr, state, flag, power):
    state["command"] = ("kick", f"{power} {int(mgr.getAngle(flag))}")


def _kick_weak_forward(mgr, state):
    """Слабый удар вперёд (от своих ворот): вправо (0°) если side l, влево (180°) если side r."""
    angle = 0 if mgr.side == "l" else 180
    state["command"] = ("kick", f"30 {angle}")


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
            "condition": lambda mgr, state: state["ball_dist"] <= KICKABLE_DIST,
            "trueCond": "kickBall",
            "falseCond": "checkCatchable",
        },
        "checkCatchable": {
            "condition": lambda mgr, state: state["ball_dist"] <= CATCHABLE_DIST,
            "trueCond": "tryCatch",
            "falseCond": "approachBall",
        },
        "tryCatch": {
            "exec": lambda mgr, state: state.__setitem__(
                "command", ("catch", str(int(state["ball_angle"])))
            ),
            "next": "sendCommand",
        },
        "kickBall": {
            "condition": lambda mgr, state: mgr.getVisible(mgr.getAwayGoalFlag()),
            "trueCond": "kickToAwayGoal",
            "falseCond": "kickToAwayCornerOrWeak",
        },
        "kickToAwayGoal": {
            "exec": lambda mgr, state: _kick_to_away_goal(mgr, state),
            "next": "sendCommand",
        },
        "kickToAwayCornerOrWeak": {
            "condition": lambda mgr, state: mgr.getVisible(mgr.getAwayCornerTop()),
            "trueCond": "kickToAwayCornerTop",
            "falseCond": "kickToAwayCornerBottomOrWeak",
        },
        "kickToAwayCornerTop": {
            "exec": lambda mgr, state: _kick_to_flag(mgr, state, mgr.getAwayCornerTop(), 80),
            "next": "sendCommand",
        },
        "kickToAwayCornerBottomOrWeak": {
            "condition": lambda mgr, state: mgr.getVisible(mgr.getAwayCornerBottom()),
            "trueCond": "kickToAwayCornerBottom",
            "falseCond": "kickWeak",
        },
        "kickToAwayCornerBottom": {
            "exec": lambda mgr, state: _kick_to_flag(mgr, state, mgr.getAwayCornerBottom(), 80),
            "next": "sendCommand",
        },
        "kickWeak": {
            "exec": lambda mgr, state: _kick_weak_forward(mgr, state),
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
            "condition": lambda mgr, state: mgr.getVisible(mgr.getOurGoalFlag()),
            "trueCond": "checkGoalDist",
            "falseCond": "searchGoal",
        },
        "searchGoal": {
            "exec": lambda mgr, state: state.__setitem__("command", ("turn", "60")),
            "next": "sendCommand",
        },
        "checkGoalDist": {
            "condition": lambda mgr, state: mgr.getDistance(mgr.getOurGoalFlag()) > 5,
            "trueCond": "moveToGoal",
            "falseCond": "positionInGoal",
        },
        "moveToGoal": {
            "condition": lambda mgr, state: abs(mgr.getAngle(mgr.getOurGoalFlag())) > 5,
            "trueCond": "turnToGoal",
            "falseCond": "dashToGoal",
        },
        "turnToGoal": {
            "exec": lambda mgr, state: state.__setitem__(
                "command", ("turn", str(int(mgr.getAngle(mgr.getOurGoalFlag()))))
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
    flag = mgr.getPenaltyCenterFlag()
    if mgr.getVisible(flag):
        dist = mgr.getDistance(flag)
        if dist < 10 or dist > 18:
            return True
        if abs(mgr.getAngle(flag)) > 30:
            return True
    return False


def _adjust_position(mgr, state):
    flag = mgr.getPenaltyCenterFlag()
    our_goal = mgr.getOurGoalFlag()
    if mgr.getVisible(flag):
        dist = mgr.getDistance(flag)
        angle = mgr.getAngle(flag)
        if dist > 18:
            if mgr.getVisible(our_goal) and abs(mgr.getAngle(our_goal)) > 5:
                state["command"] = ("turn", str(int(mgr.getAngle(our_goal))))
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
