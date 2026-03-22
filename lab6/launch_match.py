import argparse
import subprocess
import sys
import time


def spawn_team(team_name, side_name, delay):
    command = [
        sys.executable,
        "launch_team.py",
        "--team",
        team_name,
        "--side",
        side_name,
        "--delay",
        str(delay),
    ]
    print("Team launcher:", " ".join(command))
    return subprocess.Popen(command, cwd=".")


def main():
    parser = argparse.ArgumentParser(description="Launch full match (11 vs 11)")
    parser.add_argument("--left-team", type=str, default="teamA")
    parser.add_argument("--right-team", type=str, default="teamB")
    parser.add_argument("--left-side", type=str, default="l", choices=["l", "r"])
    parser.add_argument("--right-side", type=str, default="r", choices=["l", "r"])
    parser.add_argument("--team-delay", type=float, default=3.0,
                        help="Пауза перед запуском второй команды (секунды)")
    parser.add_argument("--spawn-delay", type=float, default=0.12,
                        help="Пауза между игроками в каждой команде (секунды)")
    args = parser.parse_args()

    left_process = spawn_team(args.left_team, args.left_side, args.spawn_delay)
    time.sleep(args.team_delay)
    right_process = spawn_team(args.right_team, args.right_side, args.spawn_delay)

    try:
        left_process.wait()
        right_process.wait()
    except KeyboardInterrupt:
        left_process.terminate()
        right_process.terminate()
        left_process.wait()
        right_process.wait()


if __name__ == "__main__":
    main()
