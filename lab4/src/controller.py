from decision_tree import DecisionTree
from dt_manager import DTManager
from passer_dt import create_passer_tree
from scorer_dt import create_scorer_tree


class Controller:
    def __init__(self, is_goalie: bool = False, role: str = "passer"):
        self.is_goalie = is_goalie
        self.role = role
        self.manager = DTManager()
        if is_goalie:
            from goalie_dt import create_goalie_tree
            tree_dict = create_goalie_tree()
        elif role == "passer":
            tree_dict = create_passer_tree()
        else:
            tree_dict = create_scorer_tree()
        self.dt = DecisionTree(tree_dict)

    def reset(self):
        state = self.dt.state
        if "next" in state:
            state["next"] = 0
            if "sequence" in state and state["sequence"]:
                state["action"] = state["sequence"][0]
        state["command"] = None
        if "status" in state:
            state["status"] = "init"

    def decide(
        self,
        visible_objects: dict,
        game_on: bool,
        team: str = "",
        side: str = "",
        player_number: int = 0,
        x=None,
        y=None,
        last_heard_msg=None,
    ) -> tuple:
        if not game_on:
            return None
        self.manager.update(
            visible_objects, team, side, player_number, x, y, last_heard_msg
        )
        result = self.dt.execute(self.manager)
        if result and isinstance(result, tuple) and len(result) == 2:
            return result
        return None
