# WINFRAME.I2 상태창 글자(연호·행동력·소지금·년월일) 한글화
import os, numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
W=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')
FONT=os.path.join(W,'..','SeoulHangangEB.ttf')
def get(d,S,wb,h):
    a=np.frombuffer(bytes(d[S:S+wb*h]),'uint8').reshape(h,wb)
    n=np.zeros((h,wb*2),'uint8'); n[:,0::2]=a&15; n[:,1::2]=a>>4; return n
def put(d,S,n):
    h,w=n.shape; b=(n[:,0::2]|(n[:,1::2]<<4)).astype('uint8'); d[S:S+h*w//2]=b.tobytes()
def glyphs(text, cell=12, h=13, size=12):
    # 4배 확대해 그린 뒤 축소 → 회색조(0~1)
    S=4; im=Image.new('L',(cell*len(text)*S,h*S),0); dr=ImageDraw.Draw(im)
    f=ImageFont.truetype(FONT,size*S)
    for i,ch in enumerate(text):
        bb=f.getbbox(ch); w=bb[2]-bb[0]; hh=bb[3]-bb[1]
        dr.text((i*cell*S+(cell*S-w)//2-bb[0], (h*S-hh)//2-bb[1]), ch, font=f, fill=255)
    a=np.array(im.resize((cell*len(text),h),Image.LANCZOS)).astype(float)/255
    return np.clip(a,0,1)
def render(text, h=13):
    a=glyphs(text,h=h)
    sh=np.zeros_like(a); sh[1:,1:]=a[:-1,:-1]
    edge=ndimage.grey_dilation(a,size=(3,3))
    out=np.zeros(a.shape,'uint8')
    out[edge>0.25]=2
    out[sh>0.3]=np.maximum(out[sh>0.3],3)
    m=a>0.15
    out[m]=np.clip(np.round(4+a[m]*11),4,15).astype('uint8')
    return out
def apply(D, preview=None, parts='ABY'):
    D=bytearray(D)
    if 'B' in parts:
      B=get(D,4008,120,14)
      B[1:13,:]=render('가영안정만연문구원치경응명치행동력소지금',h=12)  # 0행 끝에 CLUT가 있으므로 보존
      put(D,4008,B)
    if 'A' in parts:
      A=get(D,32,78,14)
      A[:13,120:156]=render('년월일')
      put(D,32,A)
    # 예/아니 버튼 (56x32, 194541)
    Y=get(D,194541,28,36)
    if 'Y' not in parts: return bytes(D)
    for half,bg,txt in ((0,7,'예'),(1,8,'아니')):
        x0,x1=(0,28) if half==0 else (28,56)
        sub=Y[:,x0:x1]
        inner=(sub==bg)
        rows=np.where(inner.sum(1)>8)[0]; cols=np.where(inner.sum(0)>8)[0]
        ys,ye,xs,xe=rows[0],rows[-1]+1,cols[0],cols[-1]+1
        sub[ys:ye,xs:xe][np.isin(sub[ys:ye,xs:xe],[9,10,11])]=bg
        hh,ww=ye-ys,xe-xs
        S4=4; im=Image.new('L',(ww*S4,hh*S4),0); dr=ImageDraw.Draw(im)
        if len(txt)==1:
            f=ImageFont.truetype(FONT,16*S4); bb=f.getbbox(txt)
            dr.text(((ww*S4-(bb[2]-bb[0]))//2-bb[0],(hh*S4-(bb[3]-bb[1]))//2-bb[1]),txt,font=f,fill=255)
        else:
            f=ImageFont.truetype(FONT,10*S4); bb=dr.textbbox((0,0),txt,font=f)
            dr.text(((ww*S4-(bb[2]-bb[0]))//2-bb[0],(hh*S4-(bb[3]-bb[1]))//2-bb[1]),txt,font=f,fill=255)
        a=np.array(im.resize((ww,hh),Image.LANCZOS)).astype(float)/255
        reg=sub[ys:ye,xs:xe]
        edge=ndimage.grey_dilation(a,size=(3,3))
        reg[(edge>0.3)&(a<=0.35)]=9
        reg[a>0.35]=11
        Y[:,x0:x1]=sub
    put(D,194541,Y)
    if preview:
        Image.fromarray(Y*17).resize((224,144),0).save(preview.replace('.png','_yn.png'))
        P=np.concatenate([get(D,4008,120,14),np.pad(get(D,32,78,14),((0,0),(0,84)))])
        Image.fromarray(P*17).resize((960,112),0).save(preview)
    return bytes(D)
if __name__=='__main__':
    apply(open(os.path.join(W,'orig/CG/WINFRAME.I2'),'rb').read(), os.path.join(W,'scratch/wf_ko.png'))
