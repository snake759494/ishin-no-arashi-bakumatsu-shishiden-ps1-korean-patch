# Koei LS11/Ls12 압축: 헤더16 + 사전256 + 항목(csize,usize,off BE)*n + 0
import struct
class Bits:
    def __init__(s,d): s.d=d; s.p=0
    def bit(s):
        b=(s.d[s.p>>3]>>(7-(s.p&7)))&1; s.p+=1; return b
    def bits(s,n):
        v=0
        for _ in range(n): v=(v<<1)|s.bit()
        return v
def code(b):
    v=0;n=0
    while True:
        x=b.bit(); v=(v<<1)|x; n+=1
        if not x: break
    return v+b.bits(n)
def dec1(dic,data,usize):
    b=Bits(data); out=bytearray()
    while len(out)<usize:
        c=code(b)
        if c<256: out.append(dic[c])
        else:
            off=c-256; ln=code(b)+3
            for _ in range(ln): out.append(out[-off])
    return bytes(out)
def entries(d):
    e=[];p=0x110
    while True:
        cs,us,of=struct.unpack_from('>3I',d,p)
        if cs==0: break
        e.append((cs,us,of)); p+=12
    return e
def unpack(d):
    dic=d[16:0x110]
    return [dec1(dic,d[of:of+cs],us) if cs!=us else d[of:of+cs] for cs,us,of in entries(d)]
# 인코더: 비트 쓰기 + 탐욕 LZ
class W:
    def __init__(s): s.o=bytearray(); s.cur=0; s.n=0
    def bit(s,x):
        s.cur=(s.cur<<1)|x; s.n+=1
        if s.n==8: s.o.append(s.cur); s.cur=0; s.n=0
    def bits(s,v,n):
        for i in range(n-1,-1,-1): s.bit((v>>i)&1)
    def done(s):
        if s.n: s.o.append(s.cur<<(8-s.n)); s.cur=0; s.n=0
        return bytes(s.o)
def gamma(w,v):
    n=1
    while v>=(1<<(n+1))-2: n+=1
    w.bits((1<<n)-2,n); w.bits(v-((1<<n)-2),n)
def glen(v):
    n=1
    while v>=(1<<(n+1))-2: n+=1
    return 2*n
def comp1(data,rank,maxoff=0x8000):
    """탐욕+1단계 지연 매칭 LZ"""
    w=W(); n=len(data); i=0; heads={}
    def best(i):
        if i+3>n: return 0,0
        key=data[i:i+3]; bl=0;bo=0
        for j in reversed(heads.get(key,[])[-64:]):
            if i-j>maxoff: break
            l=3
            while i+l<n and data[j+l]==data[i+l] and l<2000: l+=1
            gain=sum(glen(rank[data[i+k]]) for k in range(l))-glen(i-j+256)-glen(l-3)
            if gain>0 and (l>bl or (l==bl and i-j<bo)): bl=l;bo=i-j
        return bl,bo
    def ins(i):
        if i+3<=n: heads.setdefault(data[i:i+3],[]).append(i)
    while i<n:
        l,o=best(i)
        if l:
            l2,o2=best(i+1) if i+1<n else (0,0)
            if l2>l+1:
                gamma(w,rank[data[i]]); ins(i); i+=1; continue
            gamma(w,o+256); gamma(w,l-3)
            for k in range(l): ins(i+k)
            i+=l
        else:
            gamma(w,rank[data[i]]); ins(i); i+=1
    return w.done()
def pack(blobs,orig=None):
    import collections
    C=collections.Counter()
    for b in blobs: C.update(b)
    order=sorted(range(256),key=lambda x:(-C[x],x))
    dic=bytes(order); rank={b:i for i,b in enumerate(order)}
    head=b'Ls12'+b' '*12+dic
    comps=[comp1(b,rank) for b in blobs]
    tbl=len(head)+12*len(blobs)+4
    out=bytearray(head); off=tbl; ents=[]
    for b,c in zip(blobs,comps):
        out+=struct.pack('>3I',len(c),len(b),off); off+=len(c)
    out+=bytes(4)
    for c in comps: out+=c
    return bytes(out)
