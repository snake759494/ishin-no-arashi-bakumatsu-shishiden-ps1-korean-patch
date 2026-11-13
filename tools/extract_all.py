# 전체 원문 추출 → text/ja/*.json  (id -> {ja, max(바이트), kind})
import sys,os,json,re
sys.path.insert(0,os.path.dirname(__file__))
import ls12
from binstr import find_strings,capacity,pointers
W=os.path.join(os.path.dirname(__file__),'..')
OUT=os.path.join(W,'text','ja'); os.makedirs(OUT,exist_ok=True)
JUNK=re.compile(r'^(?:[^\x1b%]*[!-~][^\x1b%]*)$')
def plausible(s):
    t=re.sub(r'\x1b.\d?|%[-\d.]*[sdgx]|[MS]\d',' ',s)
    if re.search(r'[!-~]',t.replace('!','').replace('?','')):  # 남은 ASCII 영숫자
        if len(re.findall(r'[\u3040-\u30ff\u4e00-\u9fff]',t))<4: return False
    if len(s)==1 and not re.match(r'[\u4e00-\u9fff\u3040-\u30ff]',s): return False
    return True
def ev():
    for f in ['FEVRE','HEVIJ','HEVIS','MEVAP','SEVAK','WEVAR']:
        d=open(f'{W}/orig/EVENT/{f}.I2','rb').read(); res={}
        for k,o in enumerate(ls12.unpack(d)):
            # 헤더 이름(오프셋 10)
            i=0
            while True:
                i=o.find(b'7\x00',i)
                if i<0: break
                j=o.find(b'\x00',i+2); s=o[i+2:j]
                try:
                    t=s.decode('cp932')
                    if s and any(c>=0x81 for c in s):
                        res[f'{f}.{k}.{i+2:x}']={'ja':t,'max':len(s)}
                        i=j; continue
                except UnicodeDecodeError: pass
                i+=2
        json.dump(res,open(f'{OUT}/ev_{f}.json','w',encoding='utf-8'),ensure_ascii=False,indent=0)
        print(f,len(res))
def bins():
    L=[('SLPM_861.44',0x80010000,0x800)]+[(f'CODE/{x}.BIN',0x8015b858,0) for x in 'COM GATE HANA INIT KAIWA MARCH MOVIE MP MP2 PERS PERS2 SCOM STAFF WAR'.split()]
    for f,base,hoff in L:
        d=open(f'{W}/orig/{f}','rb').read(); idx=pointers(d[hoff:],0,0); res={}
        for o,l,s in find_strings(d):
            if not plausible(s): continue
            addr=base+o-hoff
            res[f'{os.path.basename(f)}.{o:x}']={'ja':s,'max':capacity(d,o,l),'len':l,'ptr':[p+hoff for p in idx.get(addr,[])]}
        nm=os.path.basename(f).split('.')[0]
        json.dump(res,open(f'{OUT}/bin_{nm}.json','w',encoding='utf-8'),ensure_ascii=False,indent=0)
        print(f,len(res),sum(len(v['ja']) for v in res.values()))
if __name__=='__main__': ev(); bins()
