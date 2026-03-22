from ta import TA
from attacker_ta import create_attacker_ta
from goalie_ta import create_goalie_ta
from ta_manager import TAManager


class Controller:
    def __init__(self, role: str = "attacker"):
        self.role = role
        self.manager = TAManager()

        if role == "goalie":
            ta = create_goalie_ta()
        else:
            ta = create_attacker_ta()

        self.ta = TA(ta)

    def reset(self):
        self.ta.reset()

    def decide(
        self,
        visible_objects,
        game_on,
        team="",
        side="",
        player_number=0,
        time_cycle=0,
        x=None,
        y=None,
        last_heard_msg=None,
    ):
        if not game_on:
            return None

        self.manager.update(
            visible_objects=visible_objects,
            team=team,
            side=side,
            player_number=player_number,
            time_cycle=time_cycle,
        )

        return self.ta.step(self.manager)

