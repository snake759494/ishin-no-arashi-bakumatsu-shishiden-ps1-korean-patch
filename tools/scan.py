import os,re,sys,json
def valid2(a,b): return (0x81<=a<=0x9f or 0xe0<=a<=0xef) and (0x40<=b<=0xfc and b!=0x7f)
def scan(d,minc=2):
    i=0;res=[]
    while i<len(d)-1:
        j=i;n=0
        while j<len(d)-1:
            if valid2(d[j],d[j+1]): j+=2;n+=1
            elif 0x20<=d[j]<0x7f and n>0 and False: j+=1
            else: break
        if n>=minc:
            try: s=d[i:j].decode('cp932'); res.append((i,s))
            except: pass
            i=j
        else: i+=1
    return res
if __name__=='__main__':
    tot={}
    for r,_,fs in os.walk('orig'):
        for f in fs:
            p=os.path.join(r,f); d=open(p,'rb').read(); s=scan(d)
            c=sum(len(x[1]) for x in s)
            if c>50: tot[p]=(len(s),c)
    for k,v in sorted(tot.items(),key=lambda x:-x[1][1]): print(k,v)
