# 고유 원문을 번역 작업 묶음(text/work/*.json)으로 분할
import json,glob,os,re
W=os.path.join(os.path.dirname(__file__),'..')
ja={}; order=[]
def add(k,v,maxb,kind):
    s=v['ja']
    if s not in ja: ja[s]={'ids':[],'max':maxb,'kind':kind}; order.append(s)
    e=ja[s]; e['ids'].append(k); e['max']=min(e['max'],maxb)
for f in sorted(glob.glob(f'{W}/text/ja/bin_*.json')):
    for k,v in json.load(open(f,encoding='utf-8')).items():
        m=v['max']
        if v['ptr']: m=max(m,int(v['len']*1.5)+4)
        add(k,v,m,'bin')
for f in ['FEVRE','HEVIJ','HEVIS','MEVAP','SEVAK','WEVAR']:
    for k,v in json.load(open(f'{W}/text/ja/ev_{f}.json',encoding='utf-8')).items(): add(k,v,v['max'],'ev')
os.makedirs(f'{W}/text/work',exist_ok=True)
json.dump(ja,open(f'{W}/text/ja_index.json','w',encoding='utf-8'),ensure_ascii=False)
G=[s for s in order if ja[s]['kind']=='bin' and len(s)<=7 and '\x1b' not in s and '%' not in s]
gs=set(G)
B=[s for s in order if ja[s]['kind']=='bin' and s not in gs]
E=[s for s in order if ja[s]['kind']=='ev']
def dump(name,lst):
    D={ja[s]['ids'][0]:{'ja':s,'max':ja[s]['max']} for s in lst}
    json.dump(D,open(f'{W}/text/work/{name}.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
    print(name,len(lst),sum(len(s) for s in lst))
def split(prefix,lst,size):
    cur=[];n=0;k=0
    for s in lst:
        cur.append(s); n+=len(s)
        if n>=size: dump(f'{prefix}{k:02d}',cur); cur=[];n=0;k+=1
    if cur: dump(f'{prefix}{k:02d}',cur)
dump('g00',G); split('b',B,25000); split('e',E,25000)
