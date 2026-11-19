#!/bin/sh
# 에뮬레이터·제어서버 재시작
taskkill //F //IM duckstation-qt-x64-ReleaseLTCG.exe >/dev/null 2>&1
taskkill //F //IM python.exe >/dev/null 2>&1
sleep 2
cd "$(dirname "$0")/.."
(python tools/srv.py "${CUE:-../Ishin no Arashi - Bakumatsu Shishiden (Japan) [KR].cue}" $1 > scratch/srv.log 2>&1 &)
python tools/c.py w ${2:-25}
