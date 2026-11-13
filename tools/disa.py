# python dis.py FILE BASE HOFF ADDR LEN
import sys,capstone
f,B,h,a,n=sys.argv[1],int(sys.argv[2],16),int(sys.argv[3],16),int(sys.argv[4],16),int(sys.argv[5],16)
d=open(f,'rb').read()
md=capstone.Cs(capstone.CS_ARCH_MIPS,capstone.CS_MODE_MIPS32+capstone.CS_MODE_LITTLE_ENDIAN)
for o in range(a-B+h,a-B+h+n,4):
  r=list(md.disasm(d[o:o+4],B+o-h))
  print('%x: %s'%(B+o-h,(r[0].mnemonic+' '+r[0].op_str) if r else '?'))
