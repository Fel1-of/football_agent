import argparse
import sys

from controller import Controller
from agent import Agent, InitError


def main():
    parser = argparse.ArgumentParser(description="Lab 5: Timed Automata (attacker vs goalie)")
    parser.add_argument("--team", type=str, default="teamA")
    parser.add_argument("--x", type=float, default=-20)
    parser.add_argument("--y", type=float, default=0)
    parser.add_argument("--role", type=str, choices=["attacker", "goalie"], default="attacker")
    args = parser.parse_args()

    is_goalie = args.role == "goalie"
    controller = Controller(role=args.role)
    agent = Agent(team_name=args.team, is_goalie=is_goalie, controller=controller)

    try:
        agent.run(start_pos=(args.x, args.y))
    except KeyboardInterrupt:
        agent.stop()
    except InitError as exc:
        print(exc, file=sys.stderr)
        agent.stop()
        sys.exit(1)
    except Exception as exc:
        print(exc, file=sys.stderr)
        agent.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()

