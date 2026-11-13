# CG/SELECTOR.I2 지구 선택 스프라이트 51개(2048 정렬, 크기표 COM.BIN 0x1adc0) 왼쪽 위 지명 라벨 한글화
import os, struct, numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
W=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')
NAMES=('구루와우치 소토사쿠라다 반초이다 니혼바시 핫초보리 쓰키지 아카사카 아오야마메구로 우시고메 고이시카와 아사쿠사 '
 '혼조후카가와 시바미타 고쇼 가미교 나카교 시모교 가와라마치 니시진 니조성 미부 시마바라 사쿄 기온 기요미즈 후시미 '
 '구루와우치 나카노시마 도사보리 기타신치 도톤보리 구루와우치 기타마치 미나미마치 히가시하마 구루와우치 가미마치 시모마치 '
 '산보쿠 데지마 우치마치 소토마치 마루야마 오우라 가메야마 시로야마 혼마치 가지야마치 상하이현성 강해관 번드').split()
def rend(t,fn,sz):
    f=ImageFont.truetype(os.path.join(W,'fonts',fn),sz)
    im=Image.new('L',(200,16),0); ImageDraw.Draw(im).text((0,1),t,font=f,fill=255)
    a=np.array(im)>=128; ys,xs=np.where(a); return a[ys.min():ys.max()+1,:xs.max()+1]
def layout(t,maxw,maxh):
    for nl in (1,2,3):
        k=-(-len(t)//nl); parts=[t[j:j+k] for j in range(0,len(t),k)]
        for fn,sz in (('Galmuri11.ttf',12),('Galmuri9.ttf',10)):
            gs=[rend(x,fn,sz) for x in parts]
            if max(g.shape[1] for g in gs)<=maxw and sum(g.shape[0]+3 for g in gs)<=maxh: return gs
    raise ValueError(t)
def apply(D, com, preview=None):
    D=bytearray(D); E=[struct.unpack_from('<4H',com,0x1adc0+i*8) for i in range(51)]
    o=0; outs=[]
    for i,(x,y,w,h) in enumerate(E):
        a=np.frombuffer(bytes(D[o:o+w*h//2]),'uint8').reshape(h,w//2)
        n=np.zeros((h,w),'uint8'); n[:,0::2]=a&15; n[:,1::2]=a>>4
        # 기존 라벨 지우기: 윗부분 14행 안에서 테두리(0,1) 아닌 것 → f
        top=n[1:15]; cols=np.where((top!=15)&(top!=0)&(top!=1))
        if len(cols[1]):
            x1=cols[1].max()+1; blk=n[1:15,1:x1]; blk[(blk!=0)&(blk!=1)]=15
        gs=layout(NAMES[i],w-6,h-4)
        G=np.zeros((h,w),bool); yy=2
        for g in gs:
            gh,gw=g.shape; G[yy:yy+gh,3:3+gw]=g; yy+=gh+3
        Ed=ndimage.binary_dilation(G,np.ones((3,3),bool))&~G&(n==15)
        n[Ed]=3; n[G]=14
        D[o:o+w*h//2]=(n[:,0::2]|(n[:,1::2]<<4)).astype('uint8').tobytes(); outs.append(n)
        o=(o+w*h//2+2047)//2048*2048
    if preview:
        Wd=1200; c=np.zeros((1000,Wd),'uint8'); cx=cy=rh=0
        for n in outs:
            hh,ww=n.shape
            if cx+ww>Wd: cx=0; cy+=rh+4; rh=0
            c[cy:cy+hh,cx:cx+ww]=n*17; cx+=ww+4; rh=max(rh,hh)
        Image.fromarray(c[:cy+rh]).save(preview)
    return bytes(D)
if __name__=='__main__':
    apply(open(os.path.join(W,'orig/CG/SELECTOR.I2'),'rb').read(),open(os.path.join(W,'orig/CODE/COM.BIN'),'rb').read(),os.path.join(W,'scratch/selko.png'))
