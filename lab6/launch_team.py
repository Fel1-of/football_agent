import argparse
import subprocess
import sys
import time

from squad_layout import TEAM_ROLES


def build_player_cmd(team_name, role_name, side_name):
    return [
        sys.executable,
        "app.py",
        "--team",
        team_name,
        "--role",
        role_name,
        "--side",
        side_name,
    ]


def run_team(team_name, side_name, spawn_delay=0.12):
    workers = []
    for role_name in TEAM_ROLES:
        command = build_player_cmd(team_name, role_name, side_name)
        print("Launch:", " ".join(command))
        workers.append(subprocess.Popen(command, cwd="."))
        time.sleep(spawn_delay)
    return workers


def wait_or_stop(processes):
    try:
        for process in processes:
            process.wait()
    except KeyboardInterrupt:
        print("\nInterrupt received, terminating team...")
        for process in processes:
            process.terminate()
        for process in processes:
            process.wait()


def main():
    parser = argparse.ArgumentParser(description="Launch one team (11 players)")
    parser.add_argument("--team", type=str, default="teamA")
    parser.add_argument("--side", type=str, default="l", choices=["l", "r"])
    parser.add_argument("--delay", type=float, default=0.12,
                        help="Пауза между запуском игроков (секунды)")
    args = parser.parse_args()

    squad = run_team(args.team, args.side, args.delay)
    wait_or_stop(squad)


if __name__ == "__main__":
    main()
