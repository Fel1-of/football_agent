import math

from control_hierarchy import ControllerLayer
from flags import FLAGS


def _angle_gap_deg(a1, a2):
    diff = abs(a1 - a2)
    return min(diff, 360 - diff)


def _estimate_distance_between_rays(d1, a1, d2, a2):
    angle = math.radians(_angle_gap_deg(a1, a2))
    sq = d1 * d1 + d2 * d2 - 2 * d1 * d2 * math.cos(angle)
    return math.sqrt(max(0.0, sq))


class PerceptionLayer(ControllerLayer):
    def __init__(self, team, side, role):
        super().__init__()
        self.team = team
        self.side = side
        self.role = role
        self.player_number = 0
        self.role_key = ""

    def process(self, input_data):
        visible = input_data.get("visible", {})
        ball = visible.get("b")
        referee_msg = str(input_data.get("referee_msg") or "")
        ball_dist = ball.get("dist", 9999) if ball else 9999
        can_kick = bool(ball and ball_dist < 0.85)
        if ball and self.role == "goalie" and ball_dist < 1.25:
            can_kick = True
        if ball and self._is_my_restart(referee_msg) and ball_dist < 1.2:
            can_kick = True

        own_goal_key = "gl" if self.side == "l" else "gr"
        opp_goal_key = "gr" if self.side == "l" else "gl"

        packet = {
            "visible": visible,
            "play_on": input_data.get("play_on", False),
            "last_heard": input_data.get("last_heard_msg"),
            "referee_msg": input_data.get("referee_msg"),
            "team": self.team,
            "side": self.side,
            "role": self.role,
            "role_key": self.role_key,
            "player_number": self.player_number,
            "ball": ball,
            "my_ball_dist": ball_dist,
            "can_kick": can_kick,
            "goal_own": visible.get(own_goal_key),
            "goal_opp": visible.get(opp_goal_key),
            "flags": {},
            "teammates": [],
            "opponents": [],
            "teammate_near_ball": False,
            "i_am_closest_to_ball": True,
            "teammates_closer_to_ball": 0,
            "pass_to_me": False,
            "best_pass_target": None,
            "memory": self.memory,
        }

        for key, obj in visible.items():
            if key in FLAGS:
                packet["flags"][key] = obj

            name = obj.get("name", [])
            if not isinstance(name, list) or not name:
                continue
            if name[0] != "p" or len(name) < 2:
                continue

            team_name = str(name[1]).strip('"')
            if team_name == self.team:
                packet["teammates"].append(obj)
            else:
                packet["opponents"].append(obj)

        self._analyse_ball_competition(packet)
        self._choose_pass_target(packet)
        self._process_audio(packet, input_data.get("last_heard_msg"))

        return packet

    def _is_my_restart(self, referee_msg):
        if not referee_msg or not self.side:
            return False
        restart_prefixes = (
            "kick_off_",
            "kick_in_",
            "corner_kick_",
            "free_kick_",
            "goal_kick_",
            "indirect_free_kick_",
            "back_pass_",
            "catch_fault_",
            "foul_",
        )
        return referee_msg.startswith(restart_prefixes) and referee_msg.endswith(f"_{self.side}")

    def _analyse_ball_competition(self, packet):
        ball = packet["ball"]
        if not ball:
            return

        my_ball_dist = ball.get("dist", 9999)
        ball_dir = ball.get("dir", 0)
        teammates_closer = 0

        for mate in packet["teammates"]:
            mate_dist = mate.get("dist", 9999)
            mate_dir = mate.get("dir", 0)
            mate_to_ball = _estimate_distance_between_rays(
                my_ball_dist,
                ball_dir,
                mate_dist,
                mate_dir,
            )
            mate["ball_distance_est"] = mate_to_ball

            if mate_to_ball < 1.5:
                packet["teammate_near_ball"] = True
                if mate_to_ball + 0.5 < my_ball_dist:
                    packet["i_am_closest_to_ball"] = False
                teammates_closer += 1
                continue

            if mate_to_ball + 1.2 < my_ball_dist:
                packet["i_am_closest_to_ball"] = False
                teammates_closer += 1

        packet["teammates_closer_to_ball"] = teammates_closer

    def _choose_pass_target(self, packet):
        candidates = packet["teammates"]
        if not candidates:
            return

        goal_opp = packet["goal_opp"]
        goal_own = packet["goal_own"]
        opponents = packet["opponents"]

        best = None
        best_score = -10_000

        for mate in candidates:
            dist = mate.get("dist", 9999)
            direction = mate.get("dir", 0)
            if dist < 4 or dist > 35:
                continue

            score = 0
            score += 25 - abs(dist - 14)

            if goal_opp:
                goal_dir = goal_opp.get("dir", 0)
                gap = _angle_gap_deg(direction, goal_dir)
                if gap < 35:
                    score += 25
                elif gap < 60:
                    score += 10

            if goal_own:
                own_gap = _angle_gap_deg(direction, goal_own.get("dir", 0))
                if own_gap < 55:
                    score -= 60

            for opp in opponents:
                opp_dist = opp.get("dist", 9999)
                opp_dir = opp.get("dir", 0)
                if opp_dist < dist and _angle_gap_deg(opp_dir, direction) < 15:
                    score -= 35

            if score > best_score:
                best_score = score
                best = mate

        if best and best_score > 0:
            packet["best_pass_target"] = best

    def _process_audio(self, packet, heard):
        if not heard:
            return
        msg = str(heard).strip().lower()

        if msg == "pass":
            packet["pass_to_me"] = True
            return

        if msg.startswith("pass:"):
            target = msg.split(":", 1)[1].strip()
            if target.isdigit() and int(target) == int(packet.get("player_number", -1)):
                packet["pass_to_me"] = True

    def merge(self, current_result, upper_result):
        if upper_result is None:
            return None
        if isinstance(upper_result, (tuple, dict)):
            return upper_result
        return None
