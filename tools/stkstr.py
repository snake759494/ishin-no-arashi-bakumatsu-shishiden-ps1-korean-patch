# 코드가 sb 명령으로 스택에 한 바이트씩 써서 만드는 문자열 찾기
import struct,sys,glob
def scan(d):
    regs={}; buf={}; site={}; out=[]
    def flush():
        if not buf: return
        offs=sorted(buf); run=[]; 
        for o in offs+[None]:
            if run and (o is None or o!=run[-1]+1):
                b=bytes(buf[x] for x in run)
                for part in b.split(b'\0'):
                    try:
                        t=part.decode('cp932')
                        if len(part)>=4 and any(ord(c)>0x3000 for c in t): out.append((site[run[0]],run[0],t))
                    except: pass
                run=[]
            if o is not None: run.append(o)
        buf.clear(); site.clear()
    last=0
    for a in range(0,len(d)-3,4):
        w=struct.unpack_from('<I',d,a)[0]; op=w>>26; rs=(w>>21)&31; rt=(w>>16)&31; imm=w&0xffff
        if op==9 and rs==0: regs[rt]=imm&0xff; continue
        if op==0x28 and rs==29 and rt in regs|{0:0}.keys() if False else op==0x28 and rs==29:
            v=0 if rt==0 else regs.get(rt)
            if v is None: continue
            buf[imm]=v; site.setdefault(imm,a); last=a; continue
        if w==0x03e00008 or (a-last>0x200 and buf): flush(); regs.clear()
    flush(); return out
if __name__=='__main__':
    for f in sys.argv[1:]:
        for a,o,t in scan(open(f,'rb').read()): print(f,hex(a),hex(o),t)
