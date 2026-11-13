# INFOCOM/GRAPH.I2 사상 도표 29장(144x142 4bpp, 2048 + k*10240) 라벨 한글화
import os, numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
W=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')
F=ImageFont.truetype(os.path.join(W,'fonts/Galmuri11.ttf'),12)
# (x0,x1,y0,y1, 글자, 상자형)
LB=[(59,85,2,15,'개국',1),(3,29,50,63,'좌막',0),(115,141,50,63,'존왕',0),(59,85,98,111,'양이',0),(3,29,112,125,'주전',0),(115,141,112,125,'온건',0)]
def glyph(t):
    im=Image.new('L',(30,14),0); ImageDraw.Draw(im).text((0,0),t,font=F,fill=255)
    a=np.array(im)>=128; ys,xs=np.where(a); return a[ys.min():ys.max()+1,xs.min():xs.max()+1]
def apply(D, preview=None):
    D=bytearray(D); outs=[]
    for k in range(29):
        o=2048+k*10240
        a=np.frombuffer(bytes(D[o:o+72*142]),'uint8').reshape(142,72)
        n=np.zeros((142,144),'uint8'); n[:,0::2]=a&15; n[:,1::2]=a>>4
        for x0,x1,y0,y1,t,box in LB:
            r=n[y0:y1,x0:x1]
            g=glyph(t); h,w=g.shape
            if box:
                r[1:-1,1:-1]=13
                gy=(y1-y0-h)//2; gx=(x1-x0-w)//2
                r[gy:gy+h,gx:gx+w][g]=1
            else:
                lm=(r==1)|(r==13)
                for yy in range(r.shape[0]):
                    row=n[y0+yy]; ok=[v for v in np.r_[row[max(0,x0-6):x0],row[x1:x1+6]] if v not in (1,13)]
                    bg=np.bincount(ok).argmax() if ok else 6
                    r[yy][lm[yy]]=bg
                G=np.zeros(r.shape,bool); gy=(y1-y0-h)//2; gx=(x1-x0-w)//2; G[gy:gy+h,gx:gx+w]=g
                E=ndimage.binary_dilation(G,np.ones((3,3),bool))&~G
                r[E]=1; r[G]=13
        D[o:o+72*142]=(n[:,0::2]|(n[:,1::2]<<4)).astype('uint8').tobytes(); outs.append(n)
    if preview:
        Image.fromarray(np.concatenate(outs[:3],1)*17).resize((144*3*3,142*3),0).save(preview)
    return bytes(D)
if __name__=='__main__':
    apply(open(os.path.join(W,'orig/INFOCOM/GRAPH.I2'),'rb').read(),os.path.join(W,'scratch/gr.png'))
