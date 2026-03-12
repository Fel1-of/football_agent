#!/bin/bash
# Запуск двух агентов (teamA и teamB). Сначала запустите rcssserver и rcssmonitor.

python3 app.py --team teamA --x -15 --y 0 --rotation 20 &
PID1=$!
sleep 1
python3 app.py --team teamB --x 15 --y 0 --rotation 0 &
PID2=$!

echo "Агенты запущены (PIDs: $PID1, $PID2). Нажмите Enter для остановки."
read
kill $PID1 $PID2 2>/dev/null
