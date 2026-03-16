#!/bin/bash
# Lab 4: Passer + Scorer (teamA), два защитника (teamB). Сначала запустите rcssserver.

# Passer и Scorer — teamA
python3 src/main.py --team teamA --role passer --x -15 --y 0 &
PASS_PID=$!
sleep 1
python3 src/main.py --team teamA --role scorer --x -15 --y 10 &
SCORE_PID=$!

# Защитники teamB у ворот
python3 src/main_defender.py --team teamB --x -48 --y -5 &
DEF1_PID=$!
sleep 0.5
python3 src/main_defender.py --team teamB --x -48 --y 5 &
DEF2_PID=$!

echo "Lab 4: Passer, Scorer (teamA), 2 defenders (teamB). Нажмите Enter для остановки."
read
kill $PASS_PID $SCORE_PID $DEF1_PID $DEF2_PID 2>/dev/null
