"""
Запуск: python3 app.py [--team NAME] [--x X] [--y Y] [--role attacker|goalie]
"""
import argparse
import sys

from controller import Controller
from agent import Agent, InitError


def main():
    parser = argparse.ArgumentParser(description="Лаб. 5: временные автоматы (атакующий против вратаря)")
    parser.add_argument("--team", default="teamA", help="Имя команды")
    parser.add_argument("--x", type=float, default=-20, help="Начальная координата x")
    parser.add_argument("--y", type=float, default=0, help="Начальная координата y")
    parser.add_argument("--role", choices=["attacker", "goalie"], default="attacker", help="Роль агента")
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
