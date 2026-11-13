import sys,capstone
r=open(sys.argv[1],'rb').read(); a0=int(sys.argv[2],16); n=int(sys.argv[3],16)
md=capstone.Cs(capstone.CS_ARCH_MIPS,capstone.CS_MODE_MIPS32+capstone.CS_MODE_LITTLE_ENDIAN)
o=a0-0x80000000
for i in md.disasm(r[o:o+n],a0): print('%x: %s %s'%(i.address,i.mnemonic,i.op_str))
