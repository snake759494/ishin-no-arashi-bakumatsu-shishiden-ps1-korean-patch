# 상태저장(슬롯1)에서 VRAM(1024x512 u16) 추출
import zstandard,numpy as np,os,re
W=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')
def load(slot=1):
    d=open(os.path.join(W,f'duck/savestates/SLPM-86144_{slot}.sav'),'rb').read()
    dc=zstandard.ZstdDecompressor(); out=b''; k=d.find(b'\x28\xb5\x2f\xfd')
    while k>=0:
        try: out+=dc.decompressobj().decompress(d[k:])
        except Exception: pass
        k=d.find(b'\x28\xb5\x2f\xfd',k+4)
    for m in re.finditer(re.escape(b'\x00\x00\x10\x00'),out):
        b=m.start()+4
        if b+0x100000<=len(out) and 2000000<b<3000000: break
    return np.frombuffer(out[b:b+0x100000],'<u2').reshape(512,1024).copy()
def rgb(v):
    return np.dstack([(v&31)<<3,((v>>5)&31)<<3,((v>>10)&31)<<3]).astype('uint8')
if __name__=='__main__':
    from PIL import Image
    v=load(); Image.fromarray(rgb(v)).save(os.path.join(W,'scratch/vram.png'))
