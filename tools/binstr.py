# 실행파일/오버레이 문자열 추출: 널 종료 SJIS 문자열 + 용량 + 데이터 포인터
import struct,re
def is_lead(b): return 0x81<=b<=0x9f or 0xe0<=b<=0xef
OKCH=re.compile(r'^[\u3000-\u30ff\u4e00-\u9fff\uff01-\uff9f\u2010-\u266f\u0391-\u03c9\u0410-\u044f\x0a\x1b\x20-\x7e]+$')
def find_strings(d):
    res=[]; i=0; n=len(d)
    while i<n:
        if (i==0 or d[i-1]==0) and d[i]!=0:
            j=i; ok=True; dbl=0
            while j<n and d[j]!=0:
                b=d[j]
                if is_lead(b):
                    if j+1>=n or not (0x40<=d[j+1]<=0xfc and d[j+1]!=0x7f): ok=False;break
                    j+=2; dbl+=1
                elif b==0x0a or b==0x1b or 0x20<=b<0x7f: j+=1
                else: ok=False;break
            if ok and dbl>=1 and j<n:
                try:
                    s=d[i:j].decode('cp932',errors='strict')
                    if OKCH.match(s): res.append((i,j-i,s))
                except UnicodeDecodeError: pass
                i=j+1; continue
            i=j+1 if not ok else j+1
            continue
        i+=1
    return res
def capacity(d,off,ln):
    e=off+ln  # null at e
    k=e+1
    al=(e+1+3)&~3
    while k<min(al,len(d)) and d[k]==0: k+=1
    return k-off-1   # 사용 가능 바이트(널 제외)
def pointers(d,base,addr_of):
    n=len(d)//4; W=struct.unpack('<%dI'%n,d[:n*4]); idx={}
    for i,w in enumerate(W): idx.setdefault(w,[]).append(i*4)
    return idx
