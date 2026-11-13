# SCOMBAT.I2 검술 시합 글자(8bpp, 폭 240, 0~15 회색조) 한글화
import os, numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
W=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')
FONT=os.path.join(W,'..','SeoulHangangEB.ttf')
BASE=370593; IW=240; IH=230
ITEMS=[((26,67,0,158),'단판승부'),((67,108,0,158),'삼판승부'),((108,147,0,158),'승부났다'),((108,147,158,240),'주의'),
       ((147,186,0,120),'시작'),((147,186,120,240),'첫째판'),((186,226,0,120),'둘째판'),((186,226,120,240),'셋째판')]
def draw(w,h,text,size=34):
    S=4; im=Image.new('L',(w*S,h*S),0); dr=ImageDraw.Draw(im)
    f=ImageFont.truetype(FONT,size*S); bb=dr.textbbox((0,0),text,font=f)
    tw=bb[2]-bb[0]
    if tw>(w-4)*S:
        f=ImageFont.truetype(FONT,int(size*S*(w-4)*S/tw)); bb=dr.textbbox((0,0),text,font=f)
    dr.text(((w*S-(bb[2]-bb[0]))//2-bb[0],(h*S-(bb[3]-bb[1]))//2-bb[1]),text,font=f,fill=255)
    return np.array(im.resize((w,h),Image.LANCZOS)).astype(float)/255
def apply(D, preview=None):
    D=bytearray(D)
    a=np.frombuffer(bytes(D[BASE:BASE+IW*IH]),'uint8').reshape(IH,IW).copy()
    for (y0,y1,x0,x1),t in ITEMS:
        g=draw(x1-x0,y1-y0,t)
        out=np.zeros(g.shape,'uint8')
        edge=ndimage.grey_dilation(g,size=(5,5))
        out[edge>0.3]=1
        m=g>0.2; out[m]=np.clip(np.round(3+g[m]*12),3,15).astype('uint8')
        a[y0:y1,x0:x1]=out
    D[BASE:BASE+IW*IH]=a.tobytes()
    if preview: Image.fromarray((a*17).astype('uint8')).resize((480,460),0).save(preview)
    return bytes(D)
if __name__=='__main__':
    apply(open(os.path.join(W,'orig/CG/SCOMBAT.I2'),'rb').read(),os.path.join(W,'scratch/kendo_ko.png'))
