# 빌드 결과에서 남은 일본어(가나, 한글 영역 밖 한자) 문자열 찾기
import sys,os,re,glob
sys.path.insert(0,os.path.dirname(__file__))
from disc import Writer
from binstr import find_strings
W=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(W,'..','Ishin no Arashi - Bakumatsu Shishiden (Japan) [KR] (Track 1).bin')
w=Writer(OUT)
LAST=0x9500
def jp(b):
    i=0; n=0
    while i<len(b):
        c=b[i]
        if 0x81<=c<=0x9f or 0xe0<=c<=0xef:
            code=c<<8|b[i+1]
            if (0x829f<=code<=0x8396) or code>=0x9600: n+=1
            i+=2
        else: i+=1
    return n
for p in sorted(w.files):
    if not (p.startswith('/CODE/') or p=='/SLPM_861.44'): continue
    _,lba,size,_,_=w.files[p]; d=w.read(lba,size)
    for off,ln,s in find_strings(d):
        if jp(d[off:off+ln])>=2: print(p,hex(off),repr(s))
w.f.close()
