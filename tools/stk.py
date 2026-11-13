# 코드가 스택에 sb로 한 바이트씩 만드는 문자열(인라인 char 배열)을 찾아 교체
import struct
def ins(d,a): return struct.unpack_from('<I',d,a)[0]
def kind(w):
    op=w>>26; rs=(w>>21)&31; rt=(w>>16)&31
    if op==9 and rs==0 and rt!=0: return 'li'
    if op==0x28 and rs==29: return 'sb'
    return None
def spans(d):
    """(시작,끝) 구간: li/sb 가 몰린 구간. 다른 명령 6개 이상 연속이면 끊는다"""
    out=[]; a=0; n=len(d)//4*4
    while a<n:
        if kind(ins(d,a))=='sb':
            # 뒤로 확장
            s=a; gap=0; b=a
            while b>=4 and gap<6:
                b-=4
                if kind(ins(d,b)): s=b; gap=0
                else: gap+=1
            e=a; gap=0; b=a
            while b+4<n and gap<6:
                b+=4
                if kind(ins(d,b)): e=b; gap=0
                else: gap+=1
            out.append((s,e+4)); a=e+4
        else: a+=4
    return out
def analyze(d,s,e):
    regs={}; buf={}; other=[]
    for a in range(s,e,4):
        w=ins(d,a); k=kind(w); rt=(w>>16)&31
        if k=='li': regs[rt]=w&0xff
        elif k=='sb':
            if rt!=0 and rt not in regs: return None
            buf[w&0xffff if w&0xffff<0x8000 else None]=0 if rt==0 else regs[rt]
        else: other.append((a,w))
    return regs,buf,other
def strings(buf):
    res=[]; offs=sorted(o for o in buf if o is not None); i=0
    while i<len(offs):
        j=i
        while j+1<len(offs) and offs[j+1]==offs[j]+1: j+=1
        b=bytes(buf[o] for o in offs[i:j+1]); p=offs[i]
        for part in b.split(b'\0'):
            try: t=part.decode('cp932')
            except: t=None
            if t and len(part)>=2 and any(ord(c)>0x3000 for c in t):
                # 사용 가능 길이 = 문자열 + 뒤따르는 0들 (다음 비0 바이트 전, 버퍼 연속 구간 안)
                q=p+len(part)
                while q in buf and buf[q]==0: q+=1
                res.append((p,t,q-p))
            p+=len(part)+1
        i=j+1
    return res

def regs_of(w):
    op=w>>26; rs=(w>>21)&31; rt=(w>>16)&31; rd=(w>>11)&31
    return {rs,rt,rd}
def is_ct(w):
    op=w>>26; fn=w&63
    if op==0 and fn in (8,9): return True
    return op in (1,2,3,4,5,6,7)
def patch(d, TR, enc):
    """TR: 일본어→한국어. d: bytearray. 바뀐 문자열 목록 반환"""
    done=[]
    for s,e in spans(bytes(d)):
        r=analyze(bytes(d),s,e)
        if r is None: continue
        st=[x for x in strings(r[1]) if x[1] in TR]
        if not st: continue
        # 범위 R: 첫 분기/점프의 지연 슬롯까지
        end=e
        for a in range(s,e,4):
            if not kind(ins(d,a)) and is_ct(ins(d,a)): end=a+8; break
        others=[(a,ins(d,a)) for a in range(s,end,4) if not kind(ins(d,a))]
        used=set()
        for a,w in others: used|=regs_of(w)
        regs={}; buf={}; pinned=set(); free=[]; lastw={}
        for a in range(s,end,4):
            w=ins(d,a); k=kind(w); rt=(w>>16)&31
            if k=='li': regs[rt]=w&0xffff; lastw[rt]=('li',w)
            elif k=='sb': buf[w&0xffff]=0 if rt==0 else regs[rt]&0xff
            else:
                for x in regs_of(w):
                    pass
                op=w>>26
                # 쓰기 대상 레지스터 기록
                lastw[(w>>11)&31 if op==0 else rt]=('other',w)
        for a in range(s,end,4):
            w=ins(d,a); k=kind(w); rt=(w>>16)&31
            if k=='li' and rt in used: pinned.add(a)
            elif k in('li','sb'): free.append(a)
        sc=1
        assert sc not in used, hex(s)
        nb=dict(buf)
        for p,t,l in st:
            b=enc(TR[t])
            assert len(b)<=l and (len(b)<l or len(t.encode('cp932'))==l), (t,TR[t],len(b),l)
            for i in range(l): nb[p+i]=b[i] if i<len(b) else 0
            done.append((hex(s),t,TR[t]))
        code=[]; cur=None
        offs=sorted(nb); seen=set()
        for o in offs:
            if o in seen: continue
            base=o&~3
            if all(base+i in nb for i in range(4)) and o==base:
                v=int.from_bytes(bytes(nb[base+i] for i in range(4)),'little')
                if v==0: code.append(0xafa00000|base)
                else:
                    hi,lo=v>>16,v&0xffff
                    if hi: code.append(0x3c010000|hi); code.append(0x34210000|lo) if lo else None
                    else: code.append(0x34010000|lo)
                    code.append(0xafa10000|base)
                seen|={base,base+1,base+2,base+3}
            else:
                v=nb[o]
                if v==0: code.append(0xa3a00000|o)
                else:
                    if cur!=v: code.append(0x24010000|v); cur=v
                    code.append(0xa3a10000|o)
                seen.add(o)
                continue
            cur=None
        for rt,(k,w) in lastw.items():
            if k=='li' and rt not in used: code.append(w)
        assert len(code)<=len(free), (hex(s),len(code),len(free))
        code+= [0]*(len(free)-len(code))
        for a,w in zip(free,code): struct.pack_into('<I',d,a,w)
    return done
