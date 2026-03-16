from decision_tree import DecisionTree
from dt_manager import DTManager
from goalie_dt import create_goalie_tree
from player_dt import create_player_tree


class Controller:
    def __init__(self, actions=None, is_goalie=False):
        self.is_goalie = is_goalie
        self.manager = DTManager()
        if is_goalie:
            tree_dict = create_goalie_tree()
        else:
            tree_dict = create_player_tree(actions or [])
        self.dt = DecisionTree(tree_dict)

    def reset(self):
        state = self.dt.state
        if "next" in state:
            state["next"] = 0
            if state.get("sequence"):
                state["action"] = state["sequence"][0]
        state["command"] = None

    def on_goal(self):
        self.reset()

    def decide(self, visible_objects, game_on, team="", side="", player_number=0, x=None, y=None):
        if not game_on:
            return None
        self.manager.update(
            visible_objects=visible_objects,
            team=team,
            side=side,
            player_number=player_number,
            x=x,
            y=y,
        )
        result = self.dt.execute(self.manager)
        if result and isinstance(result, tuple) and len(result) == 2:
            return result
        return None
