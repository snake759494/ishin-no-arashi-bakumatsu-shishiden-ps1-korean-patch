# WINFRAME.I2 명령 라벨(96x24 4bpp, 1152바이트 레코드 59개) 한글화
# 원본: 외곽선 9, 글자색은 행마다 다른 인덱스(위 1 → 아래 8 그라데이션)
import os, numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
W=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')
BASE=123117; N=59
KO=['정보 보기','주변인과 대화','선물 건네기','참배하기','게임 목적','선물 사기','밥 먹기','이동하기','한숨 돌리기',
'화투 치기','가이엔타이 정보','학문소 그만두기','샤추 정보','휴양하기','연습하기','건물에서 나가기','이야기 나누기',
'시합 신청','사진 찍기','주인공 정보','술 마시기','주변 지역 정보','출동하기','장사 지시','정보 보기','정보 모으기',
'정보 듣기','식사하기','신센구미 정보','진찰 받기','사람 찾기','세력 정보','설득하기','마을에서 나가기','다른 인물 정보',
'대원에게 지시','지구에서 나가기','거리에서 나가기','온천 요양','일하기','동행자 변경','도구 사기','도구 팔기',
'도장 그만두기','특산품 사기','특산품 팔기','날짜 넘기기','입문하기','목욕하기','관람하기','숙박하기','무구 사기',
'무구 팔기','공부하기','본거지로 지정','면회하기','신센구미 간부','가이엔타이 간부','샤추 간부']
assert len(KO)==N
def get(D,o):
    a=np.frombuffer(bytes(D[o:o+1152]),'uint8').reshape(24,48)
    n=np.zeros((24,96),'uint8'); n[:,0::2]=a&15; n[:,1::2]=a>>4; return n
def put(D,o,n): D[o:o+1152]=(n[:,0::2]|(n[:,1::2]<<4)).astype('uint8').tobytes()
def mask(t):
    for fn,sz,bold in (('Galmuri11.ttf',12,1),('Galmuri11.ttf',12,0),('Galmuri9.ttf',10,0)):
        f=ImageFont.truetype(os.path.join(W,'fonts',fn),sz)
        im=Image.new('L',(160,16),0); ImageDraw.Draw(im).text((0,1),t,font=f,fill=255)
        m=np.array(im)>=128
        if bold: m[:,1:]|=m[:,:-1].copy()
        xs=np.where(m.any(0))[0]
        if xs.max()+1<=87: return m[:,:xs.max()+1]
    raise ValueError(t)
def apply(D, preview=None):
    D=bytearray(D); outs=[]
    for i,t in enumerate(KO):
        o=BASE+i*1152; n=get(D,o)
        # 행별 글자색
        rowc={}
        for y in range(24):
            v=n[y][(n[y]!=0)&(n[y]!=9)]
            if len(v): rowc[y]=np.bincount(v).argmax()
        m=mask(t); h,w=m.shape
        new=np.zeros_like(n)
        g=np.zeros((24,96),bool); g[0:h,6:6+w]=m
        ys=np.where(g.any(1))[0]; top,bot=ys.min(),ys.max()
        # 원본 글자 행 범위(1~12)에 맞춰 세로 위치 조정
        g=np.roll(g,1-top+ (12-(bot-top+1))//2,axis=0)
        edge=ndimage.binary_dilation(g,np.ones((3,3),bool))&~g
        new[edge]=9
        ry=[y for y in sorted(rowc)]
        for y in range(24):
            c=rowc.get(y, rowc[min(ry,key=lambda k:abs(k-y))])
            new[y][g[y]]=c
        put(D,o,new); outs.append(new)
    if preview:
        im=np.concatenate(outs,0); Image.fromarray(((im>0)*(255-(im==9)*120)).astype('uint8')).resize((96*3,im.shape[0]*3),0).save(preview)
    return bytes(D)
if __name__=='__main__':
    apply(open(os.path.join(W,'orig/CG/WINFRAME.I2'),'rb').read(), os.path.join(W,'scratch/labko.png'))
