# 빌드 방법

번역 대본(`text/`)과 글꼴 파일은 저장소에 없으므로, 아래는 같은 자료를 갖춘 경우의 절차입니다.

## 준비
- Python 3.11 이상, `pip install pillow numpy scipy keystone-engine capstone zstandard`
- 원본 `Ishin no Arashi - Bakumatsu Shishiden (Japan) (Track 1).bin` (README의 해시와 일치)을 저장소 상위 폴더에 둡니다.
- 디스크의 `SLPM_861.44`, `CODE/*.BIN`, `CG/*`, `EVENT/*.I2`, `INFOCOM/*.I2` 를 같은 경로로 `orig/` 에 꺼냅니다(`tools/iso.py`).
- 글꼴: `fonts/Galmuri11.ttf`, `fonts/Galmuri9.ttf`, 상위 폴더에 `SeoulHangangEB.ttf`, `NanumSquareNeo-eHv.ttf`

## 순서
1. 원문 추출: `python tools/extract_all.py` → `text/ja/*.json` (실행 파일·오버레이는 `bin_*.json`, 이벤트는 `ev_*.json`). 추출기가 놓치는 문자열은 `python tools/missed.py` → `text/ja/missed.json`
2. 번역 묶음: `python tools/mkchunks.py` → `text/work/*.json` 의 `ko` 를 채웁니다. 길이 검사는 `python tools/check.py text/work/파일.json`
3. 수동 덮어쓰기: `text/override.json` (원문 → 한국어, 칸 맞춤용 축약 등)
4. 빌드: `python build.py` → 상위 폴더에 `Ishin no Arashi - Bakumatsu Shishiden (Japan) [KR] (Track 1).bin` (로그는 `build.log`, 남은 일본어 검사는 `python tools/scanout.py`)
5. 차분 파일: `xdelta3 -f -e -0 -S none -s "Ishin no Arashi - Bakumatsu Shishiden (Japan) (Track 1).bin" "Ishin no Arashi - Bakumatsu Shishiden (Japan) [KR] (Track 1).bin" Ishin_no_Arashi_Bakumatsu_Shishiden_KO_v1.0.xdelta`
