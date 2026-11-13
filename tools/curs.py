# 0x800a3ef0(x,y) 호출 목록: python curs.py FILE BASE HOFF [lo hi]
import sys,capstone
f,B,h=sys.argv[1],int(sys.argv[2],16),int(sys.argv[3],16)
lo=int(sys.argv[4],16) if len(sys.argv)>4 else 0; hi=int(sys.argv[5],16) if len(sys.argv)>5 else 1<<32
d=open(f,'rb').read()
md=capstone.Cs(capstone.CS_ARCH_MIPS,capstone.CS_MODE_MIPS32+capstone.CS_MODE_LITTLE_ENDIAN)
def ins(a):
    o=a-B+h; r=list(md.disasm(d[o:o+4],a)); return r[0] if r else None
for o in range(h,len(d)-4,4):
    a=B+o-h
    if not lo<=a<hi: continue
    if d[o:o+4]==bytes.fromhex('bc8f020c'):  # jal 0x800a3ef0
        regs={}
        for k in range(-6,2):
            x=ins(a+4*k)
            if x and x.mnemonic=='addiu' and x.op_str.split(', ')[1]=='$zero':
                r=x.op_str.split(', ')[0]; regs[r]=(int(x.op_str.split(', ')[2],16),hex(a+4*k))
        print(hex(a),'x=',regs.get('$a0'),'y=',regs.get('$a1'))
