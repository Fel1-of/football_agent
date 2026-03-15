#!/bin/bash
# Пример запуска lab3: два полевых игрока в одном звене и вратарь справа.
# Перед запуском поднимите rcssserver и rcssmonitor.

python3 app.py --team teamA --x -20 --y 0 --rotation 20 --squad-size 2 &
PID1=$!
sleep 1
python3 app.py --team teamA --x -24 --y -6 --rotation 20 --squad-size 2 &
PID2=$!
sleep 1
python3 app.py --team teamA --x 48 --y 0 --rotation 20 --goalie &
PID3=$!

echo "Агенты запущены (PIDs: $PID1, $PID2, $PID3). Нажмите Enter для остановки."
read
kill $PID1 $PID2 $PID3 2>/dev/null
