# 타이틀 버튼(INIT.BIN 0x80AD, 120x96 8bpp, 팔레트 0x7E88) 한글화
import numpy as np, os
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFont
W=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')
OFF, PAL, BW, BH = 0x80ad, 0x7e88, 120, 96
LABELS=[['새로','재개','계속'],['연습','열람','음악']]
def rgbs(D):
    p=np.frombuffer(D[PAL:PAL+512],'<u2').astype(int)
    return np.stack([(p&31)<<3,((p>>5)&31)<<3,((p>>10)&31)<<3],1)
def nearest(P,c,exclude0=True):
    dd=((P-np.array(c))**2).sum(1)
    if exclude0: dd[0]=1<<30
    return int(dd.argmin())
def apply(D, preview=None):
    D=bytearray(D); P=rgbs(D)
    img=np.frombuffer(bytes(D[OFF:OFF+BW*BH]),'uint8').reshape(BH,BW).copy()
    col=P[img]; r,g,b=col[...,0],col[...,1],col[...,2]
    lum=(r*3+g*6+b)/10
    text=((r>g*1.6)&(r>60))|(lum<75)
    font=ImageFont.truetype(os.path.join(W,'..','SeoulHangangEB.ttf'),17)
    RED=nearest(P,(176,40,16)); SH=nearest(P,(48,24,16))
    for ry in range(2):
        for cx in range(3):
            ix0,ix1=[(1,29),(41,69),(81,109)][cx]; iy0,iy1=[(9,47),(57,95)][ry]
            sub=img[iy0:iy1,ix0:ix1]; m=text[iy0:iy1,ix0:ix1].copy()
            m=ndimage.binary_dilation(m,iterations=1)
            _,(iy,ix)=ndimage.distance_transform_edt(m,return_indices=True)
            sub[:]=sub[iy,ix]
            # 글자 그리기 (세로 2자)
            lay=Image.new('L',(ix1-ix0,iy1-iy0),0); dr=ImageDraw.Draw(lay)
            for k,ch in enumerate(LABELS[ry][cx]):
                bb=font.getbbox(ch); w=bb[2]-bb[0]; h=bb[3]-bb[1]
                cy=(iy1-iy0)//4*(1+2*k)
                dr.text(((ix1-ix0-w)//2-bb[0], cy-h//2-bb[1]), ch, font=font, fill=255)
            a=np.array(lay)>=110
            sh=np.zeros_like(a); sh[1:,1:]=a[:-1,:-1]
            sub[sh&~a]=SH; sub[a]=RED
            img[iy0:iy1,ix0:ix1]=sub
    D[OFF:OFF+BW*BH]=img.tobytes()
    if preview:
        Image.fromarray(P[img].astype('uint8')).resize((BW*3,BH*3),0).save(preview)
    return bytes(D)
if __name__=='__main__':
    apply(open(os.path.join(W,'orig/CODE/INIT.BIN'),'rb').read(), os.path.join(W,'scratch/btn_ko.png'))
