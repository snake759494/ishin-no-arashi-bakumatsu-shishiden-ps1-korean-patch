# 시나리오 선택 캐릭터 카드(INIT.I2) 이름판 한글화
import os, numpy as np
from PIL import Image, ImageDraw, ImageFont
W=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')
O=512+304*224-24; BW=120; BLK=18432
NAMES=['사카모토 료마','히지카타 도시조','자유캐릭터 남','자유캐릭터 여']
Y0,Y1,X0,X1=127,146,5,115
def pal(D):
    v=np.frombuffer(bytes(D[:512]),'<u2');return np.stack([(v&31)<<3,((v>>5)&31)<<3,((v>>10)&31)<<3],1).astype(int)
def near(P,c): return int(np.argmin(((P[1:]-c)**2).sum(1)))+1
def apply(D, preview=None, size=13):
    D=bytearray(D); P=pal(D)
    font=ImageFont.truetype(os.path.join(W,'..','SeoulHangangEB.ttf'),size)
    FG=near(P,(248,240,208)); SH=near(P,(56,24,8))
    outs=[]
    for k,name in enumerate(NAMES):
        s=O+k*BLK; c=np.frombuffer(bytes(D[s:s+153*BW]),'uint8').reshape(153,BW).copy()
        reg=c[Y0:Y1,X0:X1]
        for x in range(reg.shape[1]):
            col=np.r_[reg[:3,x],reg[-3:,x]]; vals,cnt=np.unique(col,return_counts=True); reg[:,x]=vals[cnt.argmax()]
        lay=Image.new('L',(X1-X0,Y1-Y0),0); dr=ImageDraw.Draw(lay)
        bb=dr.textbbox((0,0),name,font=font); w=bb[2]-bb[0]; h=bb[3]-bb[1]
        dr.text(((X1-X0-w)//2-bb[0],(Y1-Y0-h)//2-bb[1]),name,font=font,fill=255)
        a=np.array(lay)>=110
        o=np.zeros_like(a)
        for dy in (-1,0,1):
            for dx in (-1,0,1): o|=np.roll(np.roll(a,dy,0),dx,1)
        reg[o&~a]=SH; reg[a]=FG
        c[Y0:Y1,X0:X1]=reg
        D[s:s+153*BW]=c.tobytes(); outs.append(P[c])
    if preview: Image.fromarray(np.concatenate(outs,1).astype('uint8')).resize((960,306),0).save(preview)
    return bytes(D)
if __name__=='__main__':
    apply(open(os.path.join(W,'orig/CG/INIT.I2'),'rb').read(),os.path.join(W,'scratch/cards_ko.png'))
