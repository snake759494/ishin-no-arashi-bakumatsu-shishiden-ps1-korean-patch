# 사용법: python tools/check.py text/work/파일.json  → 길이 초과/금지문자/토큰 불일치 보고
import sys,json,os,re
sys.path.insert(0,os.path.dirname(__file__))
from ko import blen,bad_chars,TOKEN
def toks(s): return sorted(t for t in TOKEN.findall(s) if t!='\n')
p=sys.argv[1]; D=json.load(open(p,encoding='utf-8')); bad=0; done=0
for k,v in D.items():
    ko=v.get('ko')
    if ko is None: continue
    done+=1
    if ko=='=': continue
    errs=[]
    if blen(ko)>v['max']: errs.append(f'길이 {blen(ko)}>{v["max"]}')
    b=bad_chars(ko)
    if b: errs.append('금지문자 '+''.join(b))
    if toks(ko)!=toks(v['ja']): errs.append(f'토큰 불일치 {toks(v["ja"])} vs {toks(ko)}')
    if errs: bad+=1; print(k,'|',' / '.join(errs),'|',repr(ko))
print(f'번역 {done}/{len(D)}, 오류 {bad}')
