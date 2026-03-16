#!/bin/bash
# Сценарий для lab3:
# - два полевых игрока teamA формируют звено
# - вратарь teamB защищает правые ворота
# Перед запуском поднимите rcssserver и rcssmonitor.

PLAYER_ACTIONS='[{"act":"flag","fl":"frb"},{"act":"kick","fl":"b","goal":"gr"}]'

python3 app.py --team teamA --x -20 --y 0 --rotation 0 --actions "$PLAYER_ACTIONS" &
PID1=$!

sleep 1
python3 app.py --team teamA --x -23 --y -3 --rotation 0 --actions "$PLAYER_ACTIONS" &
PID2=$!

sleep 1
python3 app.py --team teamB --x 45 --y 0 --rotation 0 --goalie &
PID3=$!

echo "Запущены агенты lab3 (PIDs: $PID1, $PID2, $PID3)."
echo "В rcssmonitor переведите матч в Kick off, затем в Play on."
echo "Нажмите Enter для остановки."
read

kill $PID1 $PID2 $PID3 2>/dev/null
