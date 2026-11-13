# 한국어 문자열 → 게임 바이트 길이/너비 계산 (실제 인코딩은 build.py)
import re
ONE=set(' ,.!?0123456789')
TOKEN=re.compile(r'\x1b[CMc]\d|\x1bn.|\x1b.|%[-\d.]*[sdgxc]|[A-Z]\d|\n')
def tokens(s):
    i=0
    while i<len(s):
        m=TOKEN.match(s,i)
        if m: yield ('tok',m.group()); i=m.end()
        else: yield ('ch',s[i]); i+=1
def blen(s):
    n=0
    for k,t in tokens(s):
        if k=='tok': n+=len(t)
        elif t in ONE: n+=1
        else: n+=2
    return n
def bad_chars(s):
    out=[]
    for k,t in tokens(s):
        if k=='ch' and t not in ONE:
            if '\uac00'<=t<='\ud7a3': continue
            try:
                b=t.encode('cp932')
                if len(b)!=2 or b[0]>=0x88: out.append(t)   # 한자 영역 금지(한글이 차지)
            except UnicodeEncodeError: out.append(t)
    return out
def width(s):
    w=0;mx=0
    for k,t in tokens(s):
        if t=='\n': mx=max(mx,w); w=0
        elif k=='tok': continue
        elif t==' ': w+=8
        else: w+=12
    return max(mx,w)
