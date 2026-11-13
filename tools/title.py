# 타이틀 화면(INIT.I2 304x224 8bpp) 로고 한글화: 幕末志士伝 → 막말지사전, 維新の嵐 → 유신의 폭풍
import os, numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
W=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')
F_LOGO=os.path.join(W,'..','SeoulHangangEB.ttf')
F_PLATE=os.path.join(W,'..','NanumSquareNeo-eHv.ttf')
TW,TH=304,224
def pal(D):
    v=np.frombuffer(bytes(D[:512]),'<u2');return np.stack([(v&31)<<3,((v>>5)&31)<<3,((v>>10)&31)<<3],1).astype(int)
def quant(P,cols):
    # 색 배열 → 가장 가까운 팔레트 인덱스 (0번=투명 제외)
    c=cols.reshape(-1,3)[:,None,:]; dd=((P[None,1:,:]-c)**2).sum(2)
    return (dd.argmin(1)+1).reshape(cols.shape[:-1]).astype('uint8')
def apply(D, preview=None):
    D=bytearray(D); P=pal(D)
    a=np.frombuffer(bytes(D[512:512+TW*TH]),'uint8').reshape(TH,TW).copy(); C=P[a]
    r,g,b=C[...,0],C[...,1],C[...,2]
    logo=((r-g)>22)&(r>85); logo[0:30,78:231]=False
    logo=ndimage.binary_opening(logo,iterations=1)
    lab,n=ndimage.label(logo); sz=ndimage.sum(logo,lab,range(1,n+1))
    logo=np.isin(lab,[i+1 for i,s_ in enumerate(sz) if s_>=40])
    lum=(r+g+b)/3
    shadow=ndimage.binary_dilation(logo,iterations=12)&(lum<72)&~((b>r)&(b>40))
    m=ndimage.binary_dilation(logo|shadow,iterations=2); m[0:30,78:231]=False
    src_bad=m.copy(); src_bad[0:40,70:240]=True
    tex_src=C.copy(); tex_mask=logo.copy()
    # 배경 복원: 위쪽 질감 띠는 왼쪽 위 깨끗한 조각으로 통째로 채우고, 물결(아래)은 55px 주기 복사
    out=a.copy()
    tile=a[0:28,0:76]
    YW=108
    for y in range(30,YW):
        for x in range(TW):
            if 0<=y<40 and 78<=x<231: continue
            out[y,x]=tile[(y-30)%28,x%76]
    m2=m.copy(); m2[:YW]=False
    src_bad=m2.copy(); src_bad[:YW]=True
    for y,x in zip(*np.where(m2)):
        for dx in (55,-55,110,-110,165,-165,220,-220,275,-275):
            xx=x+dx
            if 0<=xx<TW and not src_bad[y,xx]: out[y,x]=a[y,xx]; break
        else:
            for dy in (55,110,-55):
                yy=y+dy
                if YW<=yy<TH and not src_bad[yy,x]: out[y,x]=a[yy,x]; break
    # 명판 아래 테두리에 걸친 획 잔여: 같은 행 왼쪽 값으로
    for y in range(30,40):
        for x in range(78,231):
            if m[y,x]: out[y,x]=out[y,77]
    # 명판 글자 지우기
    py0,py1,px0,px1=8,33,96,201
    plate=out[py0:py1,px0:px1]; bgc=np.bincount(plate.flatten()).argmax(); plate[:]=bgc
    out[py0:py1,px0:px1]=plate
    # 새 로고 글자
    S=3; im=Image.new('L',(TW*S,TH*S),0); dr=ImageDraw.Draw(im)
    f=ImageFont.truetype(F_LOGO,60*S); txt='막말지사전'
    bb=dr.textbbox((0,0),txt,font=f); tw=bb[2]-bb[0]; th=bb[3]-bb[1]
    cx,cy=TW*S//2,(100)*S
    dr.text((cx-tw//2-bb[0],cy-th//2-bb[1]),txt,font=f,fill=255)
    im=im.transform(im.size,Image.AFFINE,(1,0.12,-0.12*cy,0,1,0),Image.BICUBIC)   # 붓글씨 느낌으로 기울임
    g=np.array(im.resize((TW,TH),Image.LANCZOS)).astype(float)/255
    gm=ndimage.binary_dilation(g>0.45,iterations=1)
    # 그림자
    sh=np.zeros_like(gm); sh[3:,3:]=gm[:-3,:-3]
    dark=quant(P,np.array([[[40,20,10]]]))[0,0]
    out[sh&~gm]=dark
    # 금빛 결: 원래 로고 픽셀 색을 가장 가까운 위치에서 가져옴
    _,(iy,ix)=ndimage.distance_transform_edt(~tex_mask,return_indices=True)
    cols=tex_src[iy,ix]
    # 위→아래 밝기 변화 보정
    out[gm]=quant(P,cols[gm][None,:,:])[0]
    edge=gm&~ndimage.binary_erosion(gm)
    out[edge]=quant(P,np.array([[[96,40,8]]]))[0,0]
    # 명판 글자
    im2=Image.new('L',((px1-px0)*S,(py1-py0)*S),0); d2=ImageDraw.Draw(im2)
    f2=ImageFont.truetype(F_PLATE,19*S); t2='유신의 폭풍'
    bb=d2.textbbox((0,0),t2,font=f2)
    d2.text((((px1-px0)*S-(bb[2]-bb[0]))//2-bb[0],((py1-py0)*S-(bb[3]-bb[1]))//2-bb[1]),t2,font=f2,fill=255)
    g2=np.array(im2.resize((px1-px0,py1-py0),Image.LANCZOS)).astype(float)/255
    base=P[out[py0:py1,px0:px1]].astype(float)
    mix=base*(1-g2[...,None])+np.array([240,240,240])*g2[...,None]
    sel=g2>0.12
    sub=out[py0:py1,px0:px1]; sub[sel]=quant(P,mix[sel][None,:,:])[0]
    D[512:512+TW*TH]=out.tobytes()
    if preview: Image.fromarray(P[out].astype('uint8')).resize((608,448),0).save(preview)
    return bytes(D)
if __name__=='__main__':
    apply(open(os.path.join(W,'orig/CG/INIT.I2'),'rb').read(),os.path.join(W,'scratch/title_ko.png'))
