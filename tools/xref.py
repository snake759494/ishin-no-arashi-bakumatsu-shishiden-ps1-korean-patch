# 오버레이/실행파일에서 주소 참조(lui+addiu/ori) 찾기: python xref.py FILE BASE HOFF ADDR...
import sys,struct,capstone
f,base,hoff=sys.argv[1],int(sys.argv[2],16),int(sys.argv[3],16)
d=open(f,'rb').read()
md=capstone.Cs(capstone.CS_ARCH_MIPS,capstone.CS_MODE_MIPS32+capstone.CS_MODE_LITTLE_ENDIAN); md.detail=False
targets=[int(x,16) for x in sys.argv[4:]]
ins=[]
for o in range(hoff,len(d)-3,4):
    r=list(md.disasm(d[o:o+4],base+o-hoff))
    ins.append(r[0] if r else type('X',(),{'mnemonic':'?','op_str':'','address':base+o-hoff})())
hi={}
for i,x in enumerate(ins):
    if x.mnemonic=='lui':
        r,v=x.op_str.split(', '); hi[r]=(int(v,16)<<16,i)
    elif x.mnemonic in('addiu','ori') :
        p=x.op_str.split(', ')
        if len(p)==3 and p[1] in hi and i-hi[p[1]][1]<12:
            v=int(p[2],16)
            if x.mnemonic=='addiu' and v>=0x8000: v-=0x10000
            a=(hi[p[1]][0]+v)&0xffffffff
            if a in targets: print(hex(a),'@',hex(x.address))
