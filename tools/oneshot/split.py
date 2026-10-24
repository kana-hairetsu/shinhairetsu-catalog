import json, sys
import os
HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, 'work')
os.makedirs(WORK, exist_ok=True)
from collections import defaultdict
sys.path.insert(0, HERE)
import pykakasi, fugashi
from kanji_table import TABLE
kks = pykakasi.kakasi(); tg = fugashi.Tagger()
def k2h(s): return ''.join(chr(ord(c)-0x60) if 0x30A1<=ord(c)<=0x30F6 else c for c in s)
d = json.load(open(os.path.join(WORK, 'aligned.json'), encoding='utf-8'))
cand = defaultdict(set)
for line in d['aligned']:
    for x in line:
        if x[0]=='K' and len(x[1])==1:
            cand[x[1]].add(x[2])
def cands(c):
    s = set(cand[c])
    s.add(''.join(x['hira'] for x in kks.convert(c)))
    for w in tg(c):
        if w.feature.kana: s.add(k2h(w.feature.kana))
    out=set()
    for r in s:
        if not r: continue
        out.add(r)
        if len(r)>=2: out.add(r[:-1]+'っ')          # 促音化
        out.add(r[0].translate(str.maketrans('かきくけこさしすせそたちつてとはひふへほ','がぎぐげござじずぜぞだぢづでどばびぶべぼ'))+r[1:])  # 連濁
        out.add(r[0].translate(str.maketrans('はひふへほ','ぱぴぷぺぽ'))+r[1:])
    return out
def split(run, rd):
    n=len(run); m=len(rd)
    INF=1e9
    best=[[INF]*(m+1) for _ in range(n+1)]; bp=[[None]*(m+1) for _ in range(n+1)]
    best[0][0]=0
    for i in range(n):
        cs=cands(run[i])
        for j in range(m+1):
            if best[i][j]>=INF: continue
            for l in range(1, min(6, m-j)+1) if i<n-1 else [m-j]:
                if l<=0: continue
                seg=rd[j:j+l]
                c = 0 if seg in cs else 3 + min((abs(len(seg)-len(x)) for x in cs), default=2)
                if run[i] in '々' : c = 0 if seg==rd[j-l:j] else c
                if best[i][j]+c < best[i+1][j+l]:
                    best[i+1][j+l]=best[i][j]+c; bp[i+1][j+l]=(j,seg)
    out=[]; j=m
    for i in range(n,0,-1):
        pj,seg=bp[i][j]; out.append(seg); j=pj
    return list(reversed(out)), best[n][m]
if __name__=='__main__':
    res={}
    for line in d['aligned']:
        for x in line:
            if x[0]=='K' and len(x[1])>1:
                sup=[c in TABLE for c in x[1]]
                if any(sup) and not all(sup):
                    segs,cost=split(x[1],x[2])
                    res[x[1]+'='+x[2]]=(segs,cost)
    json.dump(res,open(os.path.join(WORK, 'splits.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=0)
    for k,(s,c) in res.items():
        print(('!!' if c>0 else '  ')+k+' → '+'/'.join(s))
