"""
Запуск: python3 app.py [--team NAME] [--x X] [--y Y] [--rotation R]
"""
import argparse
import signal
import sys
from agent import Agent, InitError

_agent = None


def _on_terminate(*_):
    """При SIGTERM (kill из start.sh) отправляем (bye) и выходим."""
    if _agent:
        _agent.stop()
    sys.exit(0)


def main():
    global _agent
    signal.signal(signal.SIGTERM, _on_terminate)

    parser = argparse.ArgumentParser(description="Лаб. 1: позиционирование игрока")
    parser.add_argument("--team", default="teamA", help="Имя команды")
    parser.add_argument("--x", type=float, default=-15, help="Начальная координата x")
    parser.add_argument("--y", type=float, default=0, help="Начальная координата y")
    parser.add_argument("--rotation", type=float, default=20, help="Скорость вращения за такт")
    parser.add_argument("--goalie", action="store_true", help="Зарегистрироваться как вратарь")
    parser.add_argument("--host", default="127.0.0.1", help="Хост rcssserver (по умолчанию 127.0.0.1)")
    parser.add_argument("--port", type=int, default=6000, help="Порт rcssserver (по умолчанию 6000)")
    args = parser.parse_args()

    _agent = Agent(team_name=args.team, is_goalie=args.goalie, host=args.host, port=args.port)
    agent = _agent
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
