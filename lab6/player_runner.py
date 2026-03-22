import argparse
import sys

from agent import Agent
from motion_layer import MotionLayer
from perception_layer import PerceptionLayer
from strategy_defense import DefenseStrategy
from strategy_goalkeeper import GoalkeeperStrategy
from strategy_offense import OffenseStrategy
from squad_layout import TEAM_ROLES, get_role_config, role_family


def build_agent(team_name, role_key, side_hint):
    role_setup = get_role_config(side_hint, role_key)
    home_flag = role_setup["home_flag"]
    start_pos = role_setup["start_pos"]
    base_role = role_family(role_key)
    is_goalie = role_key == "goalie"

    low_level = PerceptionLayer(team=team_name, side=side_hint, role=base_role)
    mid_level = MotionLayer(home_flag=home_flag, role=base_role, side=side_hint)

    if base_role == "goalie":
        high_level = GoalkeeperStrategy(side=side_hint)
    elif base_role == "defender":
        high_level = DefenseStrategy(side=side_hint, home_flag=home_flag, role_key=role_key)
    else:
        attack_flag = role_setup.get("attack_flag", "fc")
        high_level = OffenseStrategy(
            side=side_hint,
            home_flag=home_flag,
            attack_flag=attack_flag,
            role_key=role_key,
        )

    player = Agent(
        team_name=team_name,
        controllers=[low_level, mid_level, high_level],
        is_goalie=is_goalie,
        role=role_key,
        home_flag=home_flag,
    )
    return player, start_pos


def run_player_cli():
    parser = argparse.ArgumentParser(description="Lab 6: Team Play (11 players)")
    parser.add_argument("--team", type=str, default="teamA")
    parser.add_argument("--role", type=str, default="forward_center", choices=TEAM_ROLES)
    parser.add_argument("--side", type=str, default="l", choices=["l", "r"],
                        help="Ожидаемая сторона (для стартовых позиций)")
    args = parser.parse_args()

    agent, start_pos = build_agent(args.team, args.role, args.side)

    try:
        agent.run(start_pos=start_pos)
    except KeyboardInterrupt:
        agent.stop()
    except Exception as exc:
        print(exc, file=sys.stderr)
        agent.stop()
        sys.exit(1)


if __name__ == "__main__":
    run_player_cli()
