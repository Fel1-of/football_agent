def create_scorer_tree():
    """Как у друга: без ведения — подбежал к мячу и сразу бьёт по воротам."""
    tree = {
        "state": {"status": "init", "command": None},
        "root": {"exec": lambda mgr, state: _root_exec(mgr, state), "next": "checkHeardGo"},
        "checkHeardGo": {"condition": lambda mgr, state: mgr.last_heard_msg == "go", "trueCond": "startScoring", "falseCond": "checkStatus"},
        "checkStatus": {"condition": lambda mgr, state: state["status"] == "init", "trueCond": "startMoving", "falseCond": "checkMoveToFplb"},
        "startMoving": {"exec": lambda mgr, state: state.__setitem__("status", "move_to_fplb"), "next": "checkMoveToFplb"},
        "checkMoveToFplb": {"condition": lambda mgr, state: state["status"] == "move_to_fplb", "trueCond": "atFplb", "falseCond": "checkMoveToFgrb"},
        "atFplb": {"condition": lambda mgr, state: mgr.getDistance(mgr.getScorerWingFlag()) < 3, "trueCond": "startMoveToFgrb", "falseCond": "goToFplb"},
        "goToFplb": {"condition": lambda mgr, state: mgr.getVisible(mgr.getScorerWingFlag()), "trueCond": "approachFplb", "falseCond": "searchFplb"},
        "searchFplb": {"exec": lambda mgr, state: state.__setitem__("command", ("turn", "60")), "next": "sendCommand"},
        "approachFplb": {"condition": lambda mgr, state: abs(mgr.getAngle(mgr.getScorerWingFlag())) > 5, "trueCond": "turnToFplb", "falseCond": "dashToFplb"},
        "turnToFplb": {"exec": lambda mgr, state: state.__setitem__("command", ("turn", str(int(mgr.getAngle(mgr.getScorerWingFlag()))))), "next": "sendCommand"},
        "dashToFplb": {"exec": lambda mgr, state: state.__setitem__("command", ("dash", "80")), "next": "sendCommand"},
        "startMoveToFgrb": {"exec": lambda mgr, state: state.__setitem__("status", "move_to_fgrb"), "next": "checkMoveToFgrb"},
        "checkMoveToFgrb": {"condition": lambda mgr, state: state["status"] == "move_to_fgrb", "trueCond": "atFgrb", "falseCond": "checkWaitPass"},
        "atFgrb": {"condition": lambda mgr, state: mgr.getDistance(mgr.getGoalCornerFlag()) < 3, "trueCond": "startWaitPass", "falseCond": "goToFgrb"},
        "goToFgrb": {"condition": lambda mgr, state: mgr.getVisible(mgr.getGoalCornerFlag()), "trueCond": "approachFgrb", "falseCond": "searchFgrb"},
        "searchFgrb": {"exec": lambda mgr, state: state.__setitem__("command", ("turn", "60")), "next": "sendCommand"},
        "approachFgrb": {"condition": lambda mgr, state: abs(mgr.getAngle(mgr.getGoalCornerFlag())) > 5, "trueCond": "turnToFgrb", "falseCond": "dashToFgrb"},
        "turnToFgrb": {"exec": lambda mgr, state: state.__setitem__("command", ("turn", str(int(mgr.getAngle(mgr.getGoalCornerFlag()))))), "next": "sendCommand"},
        "dashToFgrb": {"exec": lambda mgr, state: state.__setitem__("command", ("dash", "80")), "next": "sendCommand"},
        "startWaitPass": {"exec": lambda mgr, state: state.__setitem__("status", "wait_pass"), "next": "checkWaitPass"},
        "checkWaitPass": {"condition": lambda mgr, state: state["status"] == "wait_pass", "trueCond": "waitForGo", "falseCond": "checkScore"},
        "waitForGo": {"exec": lambda mgr, state: state.__setitem__("command", ("turn", "10")), "next": "sendCommand"},
        "startScoring": {"exec": lambda mgr, state: state.__setitem__("status", "score"), "next": "checkScore"},
        "checkScore": {"condition": lambda mgr, state: state["status"] == "score", "trueCond": "atBallScore", "falseCond": "waitGoalScorer"},
        "atBallScore": {"condition": lambda mgr, state: mgr.getDistance("b") < 0.8, "trueCond": "kickToGoal", "falseCond": "goToBallScore"},
        "goToBallScore": {"condition": lambda mgr, state: mgr.getVisible("b"), "trueCond": "approachBallScore", "falseCond": "searchBallScore"},
        "searchBallScore": {"exec": lambda mgr, state: state.__setitem__("command", ("turn", "45")), "next": "sendCommand"},
        "approachBallScore": {"condition": lambda mgr, state: abs(mgr.getAngle("b")) > 5, "trueCond": "turnToBallScore", "falseCond": "dashToBallScore"},
        "turnToBallScore": {"exec": lambda mgr, state: state.__setitem__("command", ("turn", str(int(mgr.getAngle("b"))))), "next": "sendCommand"},
        "dashToBallScore": {"exec": lambda mgr, state: state.__setitem__("command", ("dash", "100")), "next": "sendCommand"},
        "kickToGoal": {"condition": lambda mgr, state: mgr.getVisible(mgr.getGoalFlag()), "trueCond": "goalVisibleScore", "falseCond": "goalInvisibleScore"},
        "goalVisibleScore": {"exec": lambda mgr, state: state.__setitem__("command", ("kick", f"100 {int(mgr.getAngle(mgr.getGoalFlag()))}")), "next": "sendCommand"},
        "goalInvisibleScore": {"exec": lambda mgr, state: state.__setitem__("command", ("kick", "10 45")), "next": "sendCommand"},
        "waitGoalScorer": {"exec": lambda mgr, state: state.__setitem__("command", ("turn", "10")), "next": "sendCommand"},
        "sendCommand": {"command": lambda mgr, state: state["command"]},
    }
    return tree


def _root_exec(mgr, state):
    state["command"] = None
