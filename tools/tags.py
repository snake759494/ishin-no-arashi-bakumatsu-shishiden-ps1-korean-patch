# WINFRAME.I2 성향 태그(佐幕 尊王 攘夷 開国 主戦 穏健) 한글화: 레코드 8바이트+24x14 4bpp
import os, numpy as np
from PIL import Image, ImageDraw, ImageFont
from winframe import get, put
W=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')
F=ImageFont.truetype(os.path.join(W,'fonts/Galmuri9.ttf'),10)
TAGS=['좌막','존왕','양이','개국','주전','온건']
def glyph(t):
    im=Image.new('L',(40,16),0); ImageDraw.Draw(im).text((0,0),t,font=F,fill=255)
    a=np.array(im)>127; ys,xs=np.where(a); return a[ys.min():ys.max()+1, xs.min():xs.max()+1]
def apply(D, preview=None):
    D=bytearray(D); out=[]
    for i,t in enumerate(TAGS):
        S=63519+i*176; a=get(D,S,12,14)
        reg=a[1:12,4:23]; reg[reg>=6]=2   # 기존 밝은 글자 지우기
        g=glyph(t); h,w=g.shape
        y0=1+(11-h)//2; x0=4+(19-w)//2
        sub=a[y0:y0+h,x0:x0+w]
        sh=np.zeros_like(g); sh[1:,1:]=g[:-1,:-1]
        sub[sh&~g]=1; sub[g]=15
        put(D,S,a); out.append(a)
    if preview:
        p=np.concatenate([np.pad(x,((0,0),(0,2))) for x in out],1)
        Image.fromarray(p*17).resize((p.shape[1]*6,p.shape[0]*6),0).save(preview)
    return bytes(D)
if __name__=='__main__':
    apply(open(os.path.join(W,'orig/CG/WINFRAME.I2'),'rb').read(), os.path.join(W,'scratch/w.png'))

def kaisen(D, preview=None):
    """回戦 → 회전 (행 21~30, 12바이트 폭)"""
    D=bytearray(D); base=26667-12*21
    a=get(D,base+12*21,12,10)
    a[(a>0)]=1
    g=glyph('회전'); h,w=g.shape
    y0=(10-h)//2; x0=1+(22-w)//2
    sub=a[y0:y0+h,x0:x0+w]; sh=np.zeros_like(g); sh[1:,1:]=g[:-1,:-1]
    sub[sh&~g]=2; sub[g]=15
    put(D,base+12*21,a)
    if preview: Image.fromarray(a*17).resize((144,60),0).save(preview)
    return bytes(D)
