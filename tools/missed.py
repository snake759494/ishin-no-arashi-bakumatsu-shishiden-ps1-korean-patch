# 추출 누락 문자열: 4바이트 정렬 시작, 앞 바이트 != 0, 포인터로 참조됨
import sys,os,glob,struct,json,re
sys.path.insert(0,os.path.dirname(__file__))
from binstr import is_lead,OKCH,capacity
def scan(d,base,hoff,known=()):
    n=len(d)//4; W=struct.unpack('<%dI'%n,d[:n*4]); ref={}
    for i,w in enumerate(W): ref.setdefault(w,[]).append(i*4)
    out=[]
    for a in range(4,len(d)-2,4):
        if d[a-1]==0: continue
        ps=ref.get(base+a-hoff) or []
        j=a; dbl=0; ok=True
        while j<len(d) and d[j]!=0:
            b=d[j]
            if is_lead(b):
                if j+1>=len(d) or not 0x40<=d[j+1]<=0xfc: ok=False;break
                j+=2; dbl+=1
            elif b in (10,27) or 0x20<=b<0x7f: j+=1
            else: ok=False;break
        if not ok or dbl<1: continue
        try: s=d[a:j].decode('cp932')
        except: continue
        if not OKCH.match(s) or not re.search('[぀-ヿ一-鿿]',s): continue
        if ps or (d[a-1]==0x80 and not is_lead(d[a-2]) and (s in known or re.fullmatch(r'[぀-ヿ一-鿿]{2,}',s))): out.append((a,j-a,s,ps))
    return out
if __name__=='__main__':
    W=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    fs={'SLPM_861':(os.path.join(W,'orig/SLPM_861.44'),0x80010000,0x800)}
    for f in glob.glob(os.path.join(W,'orig/CODE/*.BIN')): fs[os.path.basename(f)[:-4]]=(f,0x8015b858,0)
    import glob as g
    known=set()
    for f in g.glob(os.path.join(W,'text/ja/bin_*.json')):
        known|={v['ja'] for v in json.load(open(f,encoding='utf-8')).values()}
    res={}
    for nm,(f,b,h) in fs.items():
        d=open(f,'rb').read()
        pre='SLPM_861.44.' if nm=='SLPM_861' else nm+'.BIN.'
        for a,ln,s,ps in scan(d,b,h,known):
            res[pre+'%x'%a]={'ja':s,'max':capacity(d,a,ln),'len':ln,'ptr':ps}
    json.dump(res,open(sys.argv[1],'w',encoding='utf-8'),ensure_ascii=False,indent=1)
    for k,v in res.items(): print(k,v['max'],repr(v['ja']))
