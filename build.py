# 유신의 폭풍 막말지사전 (SLPM-86144) 한글패치 빌드

import os, sys, json, glob, struct, shutil, collections

import numpy as np

from PIL import Image, ImageDraw, ImageFont

W = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, os.path.join(W, 'tools'))

import ls12

from fnt import decode, encode

from ko import tokens, ONE

from disc import Writer



GAME = 'Ishin no Arashi - Bakumatsu Shishiden (Japan)'

SRC = os.path.join(W, '..', GAME + ' (Track 1).bin')

OUT = os.path.join(W, '..', GAME + ' [KR] (Track 1).bin')

log = open(os.path.join(W, 'build.log'), 'w', encoding='utf-8')

def warn(*a): print(*a, file=log)



# ---------- 번역 모으기 ----------

idx = json.load(open(os.path.join(W, 'text/ja_index.json'), encoding='utf-8'))

KO = {}; FULL = {}

for f in sorted(glob.glob(os.path.join(W, 'text/work/*.json'))):

    if os.path.basename(f) == 'full_req.json': continue

    for k, v in json.load(open(f, encoding='utf-8')).items():

        if v.get('ko') not in (None, '='):

            KO[v['ja']] = v['ko']

fr = os.path.join(W, 'text/work/full_req.json')

if os.path.exists(fr):

    for k, v in json.load(open(fr, encoding='utf-8')).items():

        if v.get('full'): FULL[v['ja']] = v['full']

# 수동 덮어쓰기

ov = os.path.join(W, 'text/override.json')

if os.path.exists(ov):

    KO.update(json.load(open(ov, encoding='utf-8')))

EXJ = json.load(open(os.path.join(W, 'text/ja/extra.json'), encoding='utf-8'))

EXK = json.load(open(os.path.join(W, 'text/extra_ko.json'), encoding='utf-8'))

for k, v in EXJ.items(): KO[v['ja']] = EXK[k]

# 코드에서 lui/addiu 로 직접 참조하는 문자열: 키 -> [(lui 주소, addiu 주소)]

CODEREF = {

 'COM.BIN.1010': [(0x80162d28, 0x80162d30)],   # 인물 목록 헤더

 'COM.BIN.2e30': [(0x8016efd0, 0x8016efd4)],   # 霧島

 'COM.BIN.2e38': [(0x8016efdc, 0x8016efe0)],   # 指宿

}

MISSED = json.load(open(os.path.join(W, 'text/ja/missed.json'), encoding='utf-8'))

print('번역', len(KO), '/', len(idx), file=log)



# ---------- 한글 → 코드 배정 (한자 영역 0x889F~) ----------

cnt = collections.Counter()

for s in KO.values():

    for k, t in tokens(s):

        if k == 'ch' and '가' <= t <= '힣': cnt[t] += 1

# 이름 입력용 KS X 1001 완성형 2350자 + 번역에 쓰인 글자, 가나다순 배치

KS = [chr(c) for c in range(0xac00, 0xd7a4) if (lambda b: len(b) == 2)(chr(c).encode('euc-kr', 'ignore'))]

HAN = sorted(set(cnt) | set(KS))

assert len(HAN) <= 2965, len(HAN)

def sjis(i):

    p = i + 158; h = (p - 64) // 188; a = p - h * 188

    return bytes([0x88 + h, a if a < 0x7f else a + 1])

CODE = {c: sjis(i) for i, c in enumerate(HAN)}

print('한글 글자 수', len(HAN), file=log)



WIDE = {',': '，', '.': '．', '!': '！', '?': '？'}

WIDE.update({str(i): chr(0xff10 + i) for i in range(10)})

def enc(s, wide=False):

    out = bytearray()

    for k, t in tokens(s):

        if k == 'tok': out += t.encode('ascii')

        elif t in CODE: out += CODE[t]

        elif wide and t in WIDE: out += WIDE[t].encode('cp932')

        elif t in ONE: out += t.encode('ascii')

        else: out += NORM.get(t, t).encode('cp932')

    return bytes(out)

NORM = {'·': '・', '~': '～', '—': '―', '-': '－', '"': '”', "'": '’', '(': '（', ')': '）', ':': '：', ';': '；', '/': '／', '%': '％', '…': '…'}

WRAP120 = {'INIT.BIN.0', 'INIT.BIN.110', 'INIT.BIN.248'}

def WRAPW(k):

    # 게임이 글자 단위로 자동 줄바꿈하는 상자: 빌드 때 단어 단위로 미리 줄바꿈

    if k in WRAP120: return 114

    if k.startswith('INIT.BIN.'):

        o = int(k.rsplit('.', 1)[1], 16)

        if 0xd48 <= o < 0x1604: return 144 if max(len(re.sub(r'..', '', l)) for l in JA[k].split(chr(10))) <= 12 else 288

    return 248   # 일반 메시지 창 폭

JA = {}

for _f in glob.glob(os.path.join(W, 'text/ja/bin_INIT.json')):

    JA.update({k: v['ja'] for k, v in json.load(open(_f, encoding='utf-8')).items()})

class Skip(Exception): pass

def enc_safe(s, k, wide=False):

    try: return enc(s, wide)

    except UnicodeEncodeError as e:

        warn(f'{k}: 인코딩 불가 문자', repr(s)); return None

import re

TOKRE = re.compile(r'(%[-\d.]*[sdgxc]|[A-Z]\d|\x1b[CMc]\d|\x1b.)+')

def fix_prefix(ja, ko):

    m = re.match(r'^[\x20-\x7e]+', ja)

    if not m or '%' in m.group() or len(m.group()) > 4 or TOKRE.fullmatch(m.group()) or ko.startswith(m.group()): return ko

    pre = m.group()

    return pre + ko if not ko.startswith(pre.strip()) else pre + ko[len(pre.strip()):]

def enc_pre(ja, cand, k, wide=False):

    # 원문 앞의 쓰레기 ASCII 접두(포인터가 그 뒤를 가리킴)는 원래 바이트 그대로

    m = re.match(r'^[ -~]+', ja)

    if m and '%' not in m.group() and len(m.group()) <= 4 and not TOKRE.fullmatch(m.group()) and cand.startswith(m.group()):

        r = enc_safe(cand[len(m.group()):], k, wide)

        return None if r is None else m.group().encode('ascii') + r

    return enc_safe(cand, k, wide)

def wrap(s, limit=288):

    out = []

    for line in s.split('\n'):

        words = line.split(' '); cur = ''

        for wd in words:

            cand = wd if cur == '' else cur + ' ' + wd

            if cur and wbox(cand) > limit: out.append(cur); cur = wd

            else: cur = cand

        out.append(cur)

    return '\n'.join(out)

def wbox(s):

    n = 0

    for k, t in tokens(s):

        if k == 'tok':

            if t[0] in 'SM' and len(t) == 2: n += 48 if t[0] == 'S' else 36

            elif t[0] in 'AKP' and len(t) == 2: n += 48

            elif t[0] == '%': n += 48 if t[-1] == 's' else 24

        elif t == ' ': n += 8   # 게임 줄바꿈 판정은 공백 8px

        else: n += 12

    return n

def pad(b, n):

    # ESC+공백(2바이트 무동작)으로 채우고, 홀수면 반각 공백 하나

    k = n - len(b); assert k >= 0

    return b + b'\x1b ' * (k // 2) + b' ' * (k % 2)



# ---------- 글꼴 ----------

gal = ImageFont.truetype(os.path.join(W, 'fonts/Galmuri11.ttf'), 12)

kanji = decode(open(os.path.join(W, 'orig/CG/KANJI.FNT'), 'rb').read())

for i, c in enumerate(HAN):

    im = Image.new('L', (12, 12), 0)

    ImageDraw.Draw(im).text((0, 0), c, font=gal, fill=255)

    kanji[i] = (np.array(im) >= 128).astype('uint8')

FNT = encode(kanji)



# ---------- 실행파일·오버레이 ----------

exe = bytearray(open(os.path.join(W, 'orig/SLPM_861.44'), 'rb').read())

struct.pack_into('<H', exe, 0xfe01c, 0x020a)   # ASCII 공백 → 8px 빈칸

bins = {'SLPM_861': exe}

for f in glob.glob(os.path.join(W, 'orig/CODE/*.BIN')):

    bins[os.path.basename(f)[:-4]] = bytearray(open(f, 'rb').read())

BASE = {'SLPM_861': (0x80010000, 0x800)}

miss = 0

for nm, d in bins.items():

    p = os.path.join(W, f'text/ja/bin_{nm}.json')

    if not os.path.exists(p): continue

    S = json.load(open(p, encoding='utf-8'))

    pre = 'SLPM_861.44.' if nm == 'SLPM_861' else nm + '.BIN.'

    S.update({k: v for k, v in EXJ.items() if k.startswith(pre)})

    S.update({k: v for k, v in MISSED.items() if k.startswith(pre)})

    base, hoff = BASE.get(nm, (0x8015b858, 0))

    free = []; reloc = []

    for k, v in S.items():

        off = int(k.rsplit('.', 1)[1], 16)

        ko = KO.get(v['ja'])

        if ko is None:

            miss += 1; continue

        cands = [fix_prefix(v['ja'], wrap(c, WRAPW(k))) for c in ([FULL[v['ja']]] if v['ja'] in FULL else []) + [ko]]

        b = None

        for cand in cands:

            for wide in (True, False):

                bb = enc_pre(v['ja'], cand, k, wide)

                if bb is not None and len(bb) <= v['max']: b = bb; break

            if b is not None: break

        if b is not None:

            d[off:off + v['max'] + 1] = b + bytes(v['max'] + 1 - len(b))

            if v['max'] - len(b) >= 2: free.append([off + len(b) + 1, off + v['max'] + 1])

        elif v['ptr'] or k in CODEREF:

            alts = [x for x in (enc_pre(v['ja'], c, k) for c in cands) if x is not None]

            if alts: reloc.append((off, v, alts))

        else:

            warn(f'{k}: 길이 초과(포인터 없음)', cands[-1])

    for off, v, alts in reloc:   # 원래 자리도 빈 공간으로

        d[off:off + v['max'] + 1] = bytes(v['max'] + 1)

        free.append([off, off + v['max'] + 1])

    free.sort(); merged = []

    for f in free:

        if merged and f[0] <= merged[-1][1]: merged[-1][1] = max(merged[-1][1], f[1])

        else: merged.append(list(f))

    free = merged

    orig_len = len(d)

    if nm not in ('SLPM_861', 'PERS2'):

        # 오버레이 끝 확장: 섹터 여유 안에서, 최대 오버레이 크기(111944) 이하

        ext = min(((orig_len + 2047) // 2048) * 2048, 111944)

        if ext > orig_len:

            d.extend(bytes(ext - orig_len)); free.append([orig_len, ext])

    if nm == 'SLPM_861':

        f = next(f for f in free if f[1] - ((f[0] + 3) & ~3) >= 40)

        cave = (f[0] + 3) & ~3; f[0] = cave + 40

    short = []

    for off, v, alts in sorted(reloc, key=lambda x: -len(x[2][0])):

        done = False

        for b in alts:

            need = len(b) + 1

            cand = [f for f in free if f[1] - f[0] >= need]

            if cand:

                f = min(cand, key=lambda f: f[1] - f[0])

                a = f[0]; d[a:a + need] = b + bytes(1); f[0] += need

                for q in v['ptr']:

                    struct.pack_into('<I', d, q, base + a - hoff)

                kk = pre + '%x' % off

                for lui, lo in CODEREF.get(kk, []):

                    na = base + a - hoff; h_ = (na + 0x8000) >> 16

                    lo_o = lo - base + hoff; lu_o = lui - base + hoff

                    struct.pack_into('<H', d, lu_o, h_ & 0xffff)

                    struct.pack_into('<H', d, lo_o, (na - (h_ << 16)) & 0xffff)

                done = True; break

        if not done: warn(f'{nm}.{off:x}: 재배치 공간 없음 {len(alts[-1]) + 1}')

    if len(d) > orig_len:

        e = len(d)

        while e > orig_len and d[e - 1] == 0: e -= 1

        e = (e + 3) & ~3

        del d[max(e, orig_len):]

    print(nm, '재배치', len(reloc), file=log)

    if nm == 'SLPM_861':

        # 공백(0x20A) 6px 전진 코드 동굴

        import keystone

        ks = keystone.Ks(keystone.KS_ARCH_MIPS, keystone.KS_MODE_MIPS32 + keystone.KS_MODE_LITTLE_ENDIAN)

        a = cave; C = base + a - hoff

        code = '''.set noreorder

 lhu $v0,-0x28d0($s2)

 xori $v1,$s1,0xa

 bnez $v1,L

 addiu $v0,$v0,8

 addiu $v0,$v0,-2

L: j 0x800a3944

 sh $v0,-0x28d0($s2)

'''

        enc_, _ = ks.asm(code, C); assert len(enc_) <= 40; d[a:a + len(enc_)] = bytes(enc_)

        j, _ = ks.asm('.set noreorder; j %#x; nop' % C, 0x800a3370)

        o = 0x800a3370 - base + hoff; d[o:o + 8] = bytes(j)

        print('공백 코드', hex(C), file=log)

import btn

# ---------- 이름 입력 화면: 가나 표 → 한글 (초성×모음 2묶음) ----------

def name_entry(d):

    B = 0x8015b858; VP = 0xafc0; ST = 0xb088; EN = 0xb120

    sp = bytes([0x81, 0x40])

    groups = []

    for i in range(19):

        for v0, v1 in ((0, 7), (8, 20)):

            mem = [c for c in HAN if (ord(c) - 0xac00) // 588 == i and v0 <= (ord(c) - 0xac00) % 588 // 28 <= v1]

            groups.append((CODE[chr(0xac00 + (i * 21 + v0) * 28)], CODE[mem[0]], CODE[mem[-1]]))

    sym = '！？＋＊－／（）『』＝％＆”＜＞：’'.encode('cp932')

    groups.append(('０'.encode('cp932'), bytes([0x82, 0x4f]), bytes([0x82, 0x9a]), sym))

    # 행 우선(왼→오) 배치: 칸 번호 idx = col*5 + row

    cell = {}

    for n, g in enumerate(groups):

        row, col = divmod(n, 10); cell[col * 5 + row] = g

    # 변형 문자열 영역 재작성 (원래 0xa68~0xc8c)

    lo = min(struct.unpack_from('<I', d, VP + 4 * i)[0] for i in range(50)) - B

    hi = 0xc8c

    pos = lo; empty = None

    for idx in range(50):

        g = cell.get(idx)

        if g is None:

            if empty is None:

                empty = pos; d[pos] = 0; pos += 1

            ptr = empty; d[ST + 3 * idx:ST + 3 * idx + 2] = sp; d[EN + 3 * idx:EN + 3 * idx + 2] = sp

        else:

            v = g[3] if len(g) > 3 else g[0]

            ptr = pos; d[pos:pos + len(v) + 1] = v + bytes(1); pos += len(v) + 1

            d[ST + 3 * idx:ST + 3 * idx + 2] = g[1]; d[EN + 3 * idx:EN + 3 * idx + 2] = g[2]

        struct.pack_into('<I', d, VP + 4 * idx, B + ptr)

    assert pos <= hi, (hex(lo), hex(pos))

    for row in range(5):

        p = struct.unpack_from('<I', d, 0xaf98 + 4 * row)[0] - B

        out = sp.join(cell[c * 5 + row][0] if c * 5 + row in cell else sp for c in range(10))

        assert len(out) == 38 and d[p + 38] == 0

        d[p:p + 38] = out

name_entry(bins['INIT'])



# 코드 속(스택에 바이트로 조립되는) 문자열

import stk

STK = {

 '残資金': '잔여금',

 '三番勝負': '삼판승부', '六番勝負': '육판승부', '九番勝負': '구판승부', '十二番勝負': '십이판승부', '一発勝負': '단판승부',

 '花札を始める': '화투 시작', '札の説明': '패 설명', '役の説明': '족보 설명', '勝つための心得': '이기는 요령',

 '設定を変える': '설정 변경', '花札を終了する': '화투 종료',

 ' する': ' 한다', ' しない': ' 안 한다', ' 札の確認': ' 패 확인',

 '勝負数 ': '판 수 ', '相手の強さ': '상대 실력', '相手の性格': '상대 성격', '開始時の親': '첫 선',

 '手札・山札': '손패・더미', 'あなたの姿': '당신 모습', '設定の終了': '설정 종료',

 '弱い ': '약함 ', '普通 ': '보통 ', '強い ': '강함 ', '臆病 ': '소심 ', '大胆 ': '대담 ',

 'あなた': '당신', '相手 ': '상대 ', '札めくりで決定': '패 뒤집어 결정', '通常 ': '보통 ', '全てオープン': '모두 공개',

 '坂本竜馬': '사카모토 료마', '土方歳三': '히지카타 도시조', 'フリーキャラ': '자유 캐릭터',

 '一人用': '1인용', '二人用': '2인용', '打込み練習': '타격 연습', '剣術を終了する': '검술 종료',

}

for nm in ('SLPM_861', 'HANA', 'SCOM'):

    for x in stk.patch(bins[nm], STK, enc): print('코드문자열', nm, *x, file=log)



# 화투 점수: 한자 숫자표(〇一二…九 / 十百千万)를 코드에서 바이트로 만드는 부분을 한글 숫자로 교체

def hana_num(d):

    o = 0xe904 + 0x34

    assert d[o:o+4] == bytes.fromhex('8100 0224'.replace(' ', '')), d[o:o+4].hex()

    tb = bytearray(0x24)

    for i, ch in enumerate('영일이삼사오육칠팔구'): tb[0x10 + i*2:0x12 + i*2] = CODE[ch]

    tb += bytes(4) + b'  ' + CODE['십'] + CODE['백'] + CODE['천'] + CODE['만'] + bytes(2)

    ins = [0xafbf0054, 0xafb1003c, 0xafa00024]  # sw ra / sw s1 / sw zero,0x24

    for off in (0x10, 0x14, 0x18, 0x1c, 0x20, 0x28, 0x2c, 0x30):

        w = int.from_bytes(tb[off:off+4], 'little')

        ins += [0x3c020000 | (w >> 16), 0x34420000 | (w & 0xffff), 0xafa20000 | off]

    n = (0xe904 + 0x128 - o) // 4  # 0x8016a190..0x8016a283

    assert len(ins) <= n

    ins += [0] * (n - len(ins))

    d[o:o+4*n] = b''.join(x.to_bytes(4, 'little') for x in ins)

hana_num(bins['HANA'])

# ---------- 표 칸 맞춤 (원본과 같은 길이로 서식 문자열 교체) ----------

def raw(nm, off, old, new):

    d = bins[nm]; assert len(old) == len(new) and d[off:off + len(old)] == old, (nm, hex(off), d[off:off + len(old)])

    d[off:off + len(new)] = new

def imm(nm, addr, old, new):

    # addiu rX,zero,imm 의 즉치값 교체

    d = bins[nm]; base, hoff = BASE.get(nm, (0x8015b858, 0)); o = addr - base + hoff

    w = struct.unpack_from('<I', d, o)[0]

    assert w >> 26 == 9 and w & 0xffff == old, (nm, hex(addr), hex(w))

    struct.pack_into('<H', d, o, new)

# 지역 목록: 이름 7자 / 지방 4자 / 조직 5자 / 상태 5자

for a, o_, n_ in [(0x80171ca0, 0x3a, 0x60), (0x80171d88, 0x82, 0x98), (0x80171e20, 0x82, 0x98), (0x80171ecc, 0xb2, 0xd2),
                  (0x80172058, 0x18, 0x0c), (0x80172074, 0x4c, 0x6a), (0x80172090, 0x84, 0x98), (0x801720ac, 0xd8, 0xdc)]:

    imm('COM', a, o_, n_)

raw('COM', 0x34ac, '－' .encode('cp932') * 7, '－'.encode('cp932') * 5 + bytes(4))

# 관광 탭: 온천 4+3 두 줄(48px 간격), 명물특산 3열 격자(72px). 좌표표를 만들던 죽은 코드 자리를 동굴로 사용

def asm(nm, addr, code):

    import keystone

    ks = keystone.Ks(keystone.KS_ARCH_MIPS, keystone.KS_MODE_MIPS32 + keystone.KS_MODE_LITTLE_ENDIAN)

    b, _ = ks.asm('.set noreorder; ' + code.replace(chr(10), '; '), addr); b = bytes(b)

    base, hoff = BASE.get(nm, (0x8015b858, 0)); o = addr - base + hoff

    bins[nm][o:o + len(b)] = b; return addr + len(b)

asm('COM', 0x8016f524, 'j 0x8016f62c; nop')

CAVE = 0x8016f52c

CO = CAVE

CM = asm('COM', CO, '''slti $v0,$s2,4

 move $a0,$s0

 bnez $v0,LO1

 addiu $a1,$zero,0x8a

 addiu $a0,$s0,-0xe0

 addiu $a1,$zero,0x9c

LO1: jal 0x800a3ef0

 nop

 j 0x8016eff4

 nop''')

end = asm('COM', CM, '''addiu $v0,$zero,3

 div $s2,$v0

 mflo $a1

 mfhi $a0

 sll $v0,$a0,6

 sll $a0,$a0,3

 addu $a0,$a0,$v0

 addiu $a0,$a0,0x42

 sll $a1,$a1,4

 jal 0x800a3ef0

 addiu $a1,$a1,0x66

 j 0x8016f63c

 nop''')

assert end <= 0x8016f62c, hex(end)

asm('COM', 0x8016efe8, 'j %#x; nop; nop' % CO)

asm('COM', 0x8016f62c, 'j %#x; nop; nop; nop' % CM)

imm('COM', 0x8016f044, 0x20, 0x38)

raw('COM', 0x8, b'%-7s %-7s %2s%2s %s', b'%-8s %-7s  %2s%2s%s')   # 인물 목록: 이름 8자, 신뢰 앞 공백 제거
bins['INIT'] = bytearray(btn.apply(bins['INIT']))

print('바이너리 미번역', miss, file=log)



# ---------- 이벤트 ----------

evout = {}

for f in ['FEVRE', 'HEVIJ', 'HEVIS', 'MEVAP', 'SEVAK', 'WEVAR']:

    raw = open(os.path.join(W, f'orig/EVENT/{f}.I2'), 'rb').read()

    S = json.load(open(os.path.join(W, f'text/ja/ev_{f}.json'), encoding='utf-8'))

    blobs = [bytearray(b) for b in ls12.unpack(raw)]

    n = 0

    for k, v in S.items():

        _, e, o = k.split('.'); e = int(e); o = int(o, 16)

        ko = KO.get(v['ja'])

        if ko is None: miss += 1; continue

        ko = wrap(ko)

        b = enc_safe(ko, k)

        if b is None: continue

        if len(b) > v['max']:

            warn(f'{k}: 길이 초과 {len(b)}>{v["max"]}', ko); continue

        blobs[e][o:o + v['max']] = pad(b, v['max']); n += 1

    evout[f] = ls12.pack([bytes(b) for b in blobs])

    print(f, '적용', n, len(raw), '->', len(evout[f]), file=log)



# ---------- 디스크 ----------

shutil.copyfile(SRC, OUT)

w = Writer(OUT)

def put(path, new):

    _, lba, size, _, _ = w.files[path]

    if len(new) == size:

        old = w.read(lba, size)

        for k in range(0, size, 2048):

            if old[k:k + 2048] != new[k:k + 2048]:

                w.wsec(lba + k // 2048, new[k:k + 2048], keep_sub=True)

    else:

        cap = w.capacity(path)

        assert len(new) <= cap, (path, len(new), cap)

        w.replace(path, new, allow_move=False)

put('/CG/KANJI.FNT', FNT)

import card, winframe, kendo

put('/CG/SCOMBAT.I2', kendo.apply(open(os.path.join(W, 'orig/CG/SCOMBAT.I2'), 'rb').read()))

import tags

import labels
put('/CG/WINFRAME.I2', labels.apply(tags.kaisen(tags.apply(winframe.apply(open(os.path.join(W, 'orig/CG/WINFRAME.I2'), 'rb').read(), parts=os.environ.get('WFP', 'ABY'))))))

import title, graph, selector
put('/CG/SELECTOR.I2', selector.apply(open(os.path.join(W, 'orig/CG/SELECTOR.I2'), 'rb').read(), open(os.path.join(W, 'orig/CODE/COM.BIN'), 'rb').read()))
import chotin
put('/INFOCOM/CHOTIN.I2', chotin.apply(open(os.path.join(W, 'orig/INFOCOM/CHOTIN.I2'), 'rb').read()))
import renda, settoku
put('/CG/RENDA.I2', renda.apply(open(os.path.join(W, 'orig/CG/RENDA.I2'), 'rb').read()))
put('/CG/SETTOKU.I2', settoku.apply(open(os.path.join(W, 'orig/CG/SETTOKU.I2'), 'rb').read()))
put('/INFOCOM/GRAPH.I2', graph.apply(open(os.path.join(W, 'orig/INFOCOM/GRAPH.I2'), 'rb').read()))

put('/CG/INIT.I2', card.apply(title.apply(open(os.path.join(W, 'orig/CG/INIT.I2'), 'rb').read())))

put('/SLPM_861.44', bytes(exe))

for nm, d in bins.items():

    if nm != 'SLPM_861': put(f'/CODE/{nm}.BIN', bytes(d))

for f, d in evout.items(): put(f'/EVENT/{f}.I2', d)

w.f.close()

print('완료', OUT)

log.close()

