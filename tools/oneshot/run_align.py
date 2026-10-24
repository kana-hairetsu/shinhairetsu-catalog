import sys, json
import os
HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, 'work')
os.makedirs(WORK, exist_ok=True)
sys.path.insert(0, HERE)
import align
R=open(os.path.join(HERE, 'texts', 'wagahai_kanji_ruby.txt'),encoding='utf-8').read().splitlines()
H=open(os.path.join(HERE, 'texts', 'wagahai_hira.txt'),encoding='utf-8').read().splitlines()
RFIX={'善いいか':'善いか','善いい泥棒':'善い泥棒','波斯産ペルシャさん':'ペルシャ','催うし':'催し',
 '以太利イタリー':'イタリー',
 '見始みはじめ':'見始|','第一毛を':'第一毛|を','その後いろいろ':'その後|いろいろ','一間ひとまへ':'一間|へ',
 '入いれない':'入|れない','自みずから':'自|ら','笑わらいが':'笑|が','後うしろで':'後|で','覚さめて':'覚|めて',
 '一分いちぶばかり':'一分|ばかり','色彩いろどっ':'色彩|っ','第一色が':'第一色|が','斑入ふいりの':'斑入|の',
 '左さの':'左|の','一と月':'一|と月','定さだめた':'定|めた','考かんげえると':'考|えると','体ていの':'体|の',
 '這入はいったら':'這入|ったら','今日こんにち':'今日|','這入はいってしまった':'這入|ってしまった','淡黄色たんこうしょく':'淡黄色|'}
HFIX={'ぶうぶう':'ぶーぶー'}
for k,v in RFIX.items():
    n=sum(x.count(k) for x in R)
    if n==0: print('NOT FOUND',k)
    R=[x.replace(k,v) for x in R]
for k,v in HFIX.items(): H=[x.replace(k,v) for x in H]
res=[align.align_line(r,h) for r,h in zip(R,H)]
json.dump({'raw':R,'hira':H,'aligned':res},open(os.path.join(WORK, 'aligned.json'),'w',encoding='utf-8'),ensure_ascii=False)
ks=[x for line in res for x in line if x[0]=='K']
print('kanji runs',len(ks))
print('  '.join(f'{x[1]}={x[2]}' + (f'[{x[3]}]' if x[3] else '') for x in ks))
