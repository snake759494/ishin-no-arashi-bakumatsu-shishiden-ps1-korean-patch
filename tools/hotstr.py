# 상태저장으로 띄운 게임 RAM에 새 실행파일의 문자열 영역만 덮어쓰기
import sys,os,json,glob,socket
sys.path.insert(0,os.path.dirname(__file__))
from iso import Disc
W=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
w=Disc(os.path.join(W,'..','Ishin no Arashi - Bakumatsu Shishiden (Japan) [KR] (Track 1).bin'))
w.files={x[0]:x for x in w.walk()}
_,lba,size,_,_=w.files['/SLPM_861.44']; d=w.read(lba,size); w.f.close()
R=[]
for f in [os.path.join(W,'text/ja/bin_SLPM_861.json'),os.path.join(W,'text/ja/missed.json'),os.path.join(W,'text/ja/extra.json')]:
    for k,v in json.load(open(f,encoding='utf-8')).items():
        if k.startswith('SLPM_861.44.'):
            o=int(k.rsplit('.',1)[1],16); R.append([o,o+v['max']+1])
R.sort(); M=[]
for a,b in R:
    if M and a<=M[-1][1]: M[-1][1]=max(M[-1][1],b)
    else: M.append([a,b])
cmds=[]
for a,b in M:
    for x in range(a,b,512):
        y=min(b,x+512); cmds.append('wr %x %s'%(0x80010000+x-0x800,d[x:y].hex()))
def send(c):
    s=socket.create_connection(('127.0.0.1',2399)); s.sendall(c.encode()); r=b''
    while True:
        q=s.recv(65536)
        if not q: break
        r+=q
    return r
for i in range(0,len(cmds),40): send(';'.join(cmds[i:i+40]))
print(len(M),'구간',len(cmds),'쓰기')
