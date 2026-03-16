"""
Запуск: python3 app.py [--team NAME] [--x X] [--y Y]
"""
import argparse
import json
import sys
from agent import Agent, InitError

DEFAULT_ACTIONS = [
    {"act": "flag", "fl": "frb"},
    {"act": "flag", "fl": "gl"},
    {"act": "flag", "fl": "fc"},
    {"act": "kick", "fl": "b", "goal": "gr"},
]


def main():
    parser = argparse.ArgumentParser(description="Лаб. 3: деревья решений для игрока и вратаря")
    parser.add_argument("--team", default="teamA", help="Имя команды")
    parser.add_argument("--x", type=float, default=-15, help="Начальная координата x")
    parser.add_argument("--y", type=float, default=0, help="Начальная координата y")
    parser.add_argument("--rotation", type=float, default=20, help="Скорость вращения за такт")
    parser.add_argument("--goalie", action="store_true", help="Зарегистрироваться как вратарь")
    parser.add_argument("--actions", help="JSON-массив действий для дерева игрока")
    args = parser.parse_args()

    actions = DEFAULT_ACTIONS
    if args.actions:
        actions = json.loads(args.actions)

    agent = Agent(team_name=args.team, is_goalie=args.goalie, actions=actions)
    try:
        agent.run(start_pos=(args.x, args.y), rotation_speed=args.rotation)
    except KeyboardInterrupt:
        agent.stop()
    except InitError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(e, file=sys.stderr)
        agent.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()
