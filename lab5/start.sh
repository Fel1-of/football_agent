#!/bin/bash
# Lab 5: атакующий (teamA) против вратаря-защитника (teamB).
# Перед запуском должны быть подняты rcssserver и rcssmonitor.

python3 app.py --team teamA --role attacker --x -20 --y 0 &
ATTACKER_PID=$!
sleep 1
python3 app.py --team teamB --role goalie --x 50 --y 0 &
GOALIE_PID=$!

echo "Lab 5: attacker vs goalie. Нажмите Enter для остановки."
read
kill $ATTACKER_PID $GOALIE_PID 2>/dev/null
