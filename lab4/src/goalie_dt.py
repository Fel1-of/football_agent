"""Минимальное дерево для вратаря: стоит на месте."""
def create_goalie_tree():
    tree = {
        "state": {"command": None},
        "root": {"exec": lambda mgr, state: state.__setitem__("command", None), "next": "sendCommand"},
        "sendCommand": {"command": lambda mgr, state: ("turn", "0")},
    }
    return tree
