# KANJI.FNT/KANA.FNT: 블록(1440B)=240x12 4bpp, 칸 12px x20, 니블 비트 p = 글자 4*칸+p ... (순서는 검증)
import numpy as np
def decode(d):
    nb=len(d)//1440; out=[]
    for b in range(nb):
        blk=np.frombuffer(d[b*1440:(b+1)*1440],'uint8').reshape(12,120)
        px=np.zeros((12,240),'uint8'); px[:,0::2]=blk&15; px[:,1::2]=blk>>4
        for t in range(20):
            for p in range(4):
                out.append(((px[:,t*12:t*12+12]>>p)&1).astype('uint8'))
    return out
def encode(glyphs):
    n=(len(glyphs)+79)//80; res=bytearray()
    for b in range(n):
        px=np.zeros((12,240),'uint8')
        for t in range(20):
            for p in range(4):
                i=b*80+t*4+p
                if i<len(glyphs): px[:,t*12:t*12+12]|=(glyphs[i].astype('uint8')&1)<<p
        res+=(px[:,0::2]|(px[:,1::2]<<4)).astype('uint8').tobytes()
    return bytes(res)
