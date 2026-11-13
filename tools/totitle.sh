#!/bin/sh
# 부팅 → 오프닝 빨리감기 → 타이틀
cd "$(dirname "$0")/.."
sh tools/restart.sh >/dev/null
python tools/c.py "p start;w 3;ff 45;w 2;p start;w 3"
