#!/bin/sh
# 에뮬레이터를 상태저장 1에서 다시 시작
cd "$(dirname "$0")/.."
taskkill //F //IM duckstation-qt-x64-ReleaseLTCG.exe >/dev/null 2>&1
taskkill //F //IM python.exe >/dev/null 2>&1
sleep 2
(python tools/srv.py "../Ishin no Arashi - Bakumatsu Shishiden (Japan) [KR].cue" duck/savestates/SLPM-86144_1.sav > scratch/srv.log 2>&1 &)
python tools/c.py w 4 >/dev/null
