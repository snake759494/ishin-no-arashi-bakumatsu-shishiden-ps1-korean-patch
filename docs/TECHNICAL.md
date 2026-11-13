# 기술 문서

## 디스크 구조
- 트랙 4개(데이터 MODE2/2352 + 오디오 3). 패치는 트랙 1만 바꿉니다.
- 실행 파일 `SLPM_861.44`(RAM 0x80010000, 헤더 0x800), 오버레이 `CODE/*.BIN` 14개(기준 주소 0x8015B858), 이벤트 대사 `EVENT/*.I2` 6개, 그림 `CG/*.I2`·`INFOCOM/*.I2`.
- 빌드는 바뀐 파일의 섹터만 다시 쓰고 EDC/ECC를 다시 계산합니다(`tools/disc.py`, `tools/cdsec.py`). 파일이 커지면 디스크 뒤쪽 빈 공간으로 옮기고 디렉터리 항목을 고칩니다.

## 문자열
- 실행 파일·오버레이: 널 종료 Shift-JIS 문자열과 그 포인터를 찾아(`tools/binstr.py`) 번역문이 원래 자리에 맞으면 제자리에, 길면 여유 공간으로 옮기고 포인터를 고칩니다. lui/addiu 쌍으로 직접 참조하는 문자열은 명령어 즉시값을 고칩니다(`CODEREF`, `tools/xref.py`).
- 코드가 스택에 한 바이트씩 조립하는 문자열(화투 메뉴 등)은 명령어의 즉시값을 바꿉니다(`tools/stk.py`, `tools/stkstr.py`).
- 이벤트 대사는 코에이 LS11/Ls12 압축 묶음입니다(`tools/ls12.py`). 풀어서 바꾸고 다시 압축합니다.
- 메시지 출력은 공백을 6px로 그리지만 줄바꿈 판정은 8px로 셉니다. 줄바꿈 계산을 이 판정에 맞춰 한 줄이 넘치지 않게 합니다.
- printf의 `%-Ns` 폭 지정은 글자 수 기준이라, 표 서식 문자열과 열 좌표(addiu 즉시값)를 한글 폭에 맞게 고쳤습니다.

## 글꼴
- `CG/KANJI.FNT` 는 12×12 4bpp 글꼴입니다(`tools/fnt.py`). 한자 영역 0x889F부터 한글 2,352자(완성형 2,350자 + 번역에 쓰인 글자)를 갈무리11 원래 크기로 그려 넣습니다.
- 이름 입력 화면의 가나 표를 초성·모음 두 묶음의 한글 표로 바꿨습니다.

## 그림 글자
- `tools/title.py`·`tools/btn.py`·`tools/card.py`: 타이틀 로고·버튼·시나리오 카드(INIT.I2/INIT.BIN, 8bpp)
- `tools/winframe.py`·`tools/tags.py`·`tools/labels.py`: WINFRAME.I2 상태창, 성향 태그, 명령 버튼 59종(96×24 4bpp)
- `tools/graph.py`: 사상 도표 29장(144×142 4bpp)
- `tools/selector.py`: 지역 지도 이름표 51종(크기표는 COM.BIN 0x1ADC0)
- `tools/chotin.py`: 축제 등롱 14종(24×32 8bpp, 점등/소등 두 벌). 원래 글자를 지우고 등롱 바탕을 행별로 다시 칠한 뒤 갈무리9로 씁니다.
- `tools/kendo.py`: 검술 시합 글자(SCOMBAT.I2)
- `tools/renda.py`·`tools/settoku.py`: 연타 미니게임 현판, 설득 화면 사상 도표

## 검증 도구
- `tools/emu.py`, `tools/srv.py`, `tools/c.py`: DuckStation을 백그라운드로 띄워 GDB 원격 접속으로 메모리를 읽고 쓰고, 키 입력을 자동화합니다(`tools/reload.sh` 는 상태저장 1에서 다시 시작).
- `tools/fb.py`, `tools/vram.py`: 상태저장에서 VRAM을 꺼내 저장합니다.
- `tools/disa.py`, `tools/curs.py`, `tools/xref.py`: 역어셈블, 글자 커서 호출 위치, 주소 참조 찾기.
- `tools/scanout.py`, `tools/missed.py`: 남은 일본어와 추출 누락 문자열 찾기.
