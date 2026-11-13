# 시험용: 패치 디스크의 WINFRAME.I2만 교체
import sys,os
sys.path.insert(0,os.path.dirname(__file__))
from disc import Writer
import winframe
W=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')
w=Writer(os.path.join(W,'..','Ishin no Arashi - Bakumatsu Shishiden (Japan) [KR] (Track 1).bin'))
new=winframe.apply(open(os.path.join(W,'orig/CG/WINFRAME.I2'),'rb').read(),parts=sys.argv[1])
_,lba,size,_,_=w.files['/CG/WINFRAME.I2']; old=w.read(lba,size)
for k in range(0,size,2048):
    if old[k:k+2048]!=new[k:k+2048]: w.wsec(lba+k//2048,new[k:k+2048],keep_sub=True)
w.f.close()
