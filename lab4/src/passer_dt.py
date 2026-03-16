def create_passer_tree():
    tree = {
        "state": {"status": "init", "command": None},
        "root": {"exec": lambda mgr, state: _root_exec(mgr, state), "next": "checkStatus"},
        "checkStatus": {"condition": lambda mgr, state: state["status"] == "init", "trueCond": "startMoving", "falseCond": "checkMoveToFplc"},
        "startMoving": {"exec": lambda mgr, state: state.__setitem__("status", "move_to_fplc"), "next": "checkMoveToFplc"},
        "checkMoveToFplc": {"condition": lambda mgr, state: state["status"] == "move_to_fplc", "trueCond": "atFplc", "falseCond": "checkMoveToBall"},
        "atFplc": {"condition": lambda mgr, state: mgr.getDistance(mgr.getCenterFlag()) < 3, "trueCond": "startMoveToBall", "falseCond": "goToFplc"},
        "goToFplc": {"condition": lambda mgr, state: mgr.getVisible(mgr.getCenterFlag()), "trueCond": "approachFplc", "falseCond": "searchFplc"},
        "searchFplc": {"exec": lambda mgr, state: state.__setitem__("command", ("turn", "60")), "next": "sendCommand"},
        "approachFplc": {"condition": lambda mgr, state: abs(mgr.getAngle(mgr.getCenterFlag())) > 5, "trueCond": "turnToFplc", "falseCond": "dashToFplc"},
        "turnToFplc": {"exec": lambda mgr, state: state.__setitem__("command", ("turn", str(int(mgr.getAngle(mgr.getCenterFlag()))))), "next": "sendCommand"},
        "dashToFplc": {"exec": lambda mgr, state: state.__setitem__("command", ("dash", "80")), "next": "sendCommand"},
        "startMoveToBall": {"exec": lambda mgr, state: state.__setitem__("status", "move_to_ball"), "next": "checkMoveToBall"},
        "checkMoveToBall": {"condition": lambda mgr, state: state["status"] == "move_to_ball", "trueCond": "atBall", "falseCond": "checkPassing"},
        "atBall": {"condition": lambda mgr, state: mgr.getDistance("b") < 0.85, "trueCond": "startPassing", "falseCond": "goToBall"},
        "goToBall": {"condition": lambda mgr, state: mgr.getVisible("b"), "trueCond": "approachBall", "falseCond": "searchBall"},
        "searchBall": {"exec": lambda mgr, state: state.__setitem__("command", ("turn", "60")), "next": "sendCommand"},
        "approachBall": {"condition": lambda mgr, state: abs(mgr.getAngle("b")) > 4, "trueCond": "turnToBall", "falseCond": "dashToBall"},
        "turnToBall": {"exec": lambda mgr, state: state.__setitem__("command", ("turn", str(int(mgr.getAngle("b"))))), "next": "sendCommand"},
        "dashToBall": {"exec": lambda mgr, state: _dash_to_ball(mgr, state), "next": "sendCommand"},
        "startPassing": {"exec": lambda mgr, state: state.__setitem__("status", "passing"), "next": "checkPassing"},
        "checkPassing": {"condition": lambda mgr, state: state["status"] == "passing", "trueCond": "findScorer", "falseCond": "waitGoal"},
        "findScorer": {"condition": lambda mgr, state: mgr.getTeammateCount() > 0, "trueCond": "aimAtScorer", "falseCond": "rotateWithBall"},
        "aimAtScorer": {"condition": lambda mgr, state: _aimed_at_teammate(mgr), "trueCond": "passToScorer", "falseCond": "turnToScorer"},
        "turnToScorer": {"exec": lambda mgr, state: _turn_to_teammate(mgr, state), "next": "sendCommand"},
        "rotateWithBall": {"exec": lambda mgr, state: state.__setitem__("command", ("turn", "60")), "next": "sendCommand"},
        "passToScorer": {"exec": lambda mgr, state: _pass_exec(mgr, state), "next": "sendCommand"},
        "waitGoal": {"exec": lambda mgr, state: state.__setitem__("command", ("turn", "10")), "next": "sendCommand"},
        "sendCommand": {"command": lambda mgr, state: state["command"]},
    }
    return tree


def _root_exec(mgr, state):
    state["command"] = None


def _dash_to_ball(mgr, state):
    """К мячу без отброса: близко — тихий dash, иначе средний (не врезаться в мяч)."""
    d = mgr.getDistance("b")
    if d < 1.2:
        power = 50
    elif d < 2.5:
        power = 65
    else:
        power = 78
    state["command"] = ("dash", str(power))


def _aimed_at_teammate(mgr):
    """Проверка: смотрим на напарника (угол < 4°), можно бить прямо."""
    t = mgr.getClosestTeammate()
    if not t:
        return False
    _, obj = t
    return abs(obj.get("dir", 999)) < 4


def _turn_to_teammate(mgr, state):
    """Поворот в сторону напарника перед пасом."""
    t = mgr.getClosestTeammate()
    if t:
        _, obj = t
        state["command"] = ("turn", str(int(obj.get("dir", 0))))
    else:
        state["command"] = ("turn", "30")


def _pass_exec(mgr, state):
    """Пас: после поворота бьём прямо (0°), сила по дистанции."""
    teammate = mgr.getClosestTeammate()
    if teammate:
        key, obj = teammate
        dist = obj.get("dist", 0)
        power = min(78, max(32, int(dist * 3 + 30)))
        state["command"] = ("kick", f"{power} 0")
        state["status"] = "wait_goal"
        state["say"] = "go"
    else:
        state["command"] = ("kick", "10 45")
