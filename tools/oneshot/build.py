# -*- coding: utf-8 -*-
"""薙刀式v18＋一打漢直：お題文の整形と打鍵列の生成"""
import json, sys
import os
HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, 'work')
os.makedirs(WORK, exist_ok=True)
sys.path.insert(0, HERE)
from kanji_table import TABLE, HOLD
from split import split

SPLIT_FIX = {
    ('肝心', 'かんじん'): ['かん', 'じん'],
    ('大家', 'たいか'): ['たい', 'か'],
    ('翌日吾輩', 'よくじつわがはい'): ['よく', 'じつ', 'わが', 'はい'],
    ('淡黄色', 'たんこうしょく'): ['たん', 'こう', 'しょく'],
    ('昼飯後', 'ちゅうはんご'): ['ちゅう', 'はん', 'ご'],
    ('今吾輩', 'いまわがはい'): ['いま', 'わが', 'はい'],
    ('時吾輩', 'ときわがはい'): ['とき', 'わが', 'はい'],
}

def k2h(c):
    o = ord(c)
    return chr(o - 0x60) if 0x30A1 <= o <= 0x30F6 else c

# ---- 1. お題文の整形 ----------------------------------------------------
def build_units():
    d = json.load(open(os.path.join(WORK, 'aligned.json'), encoding='utf-8'))
    lines = []
    for al in d['aligned']:
        units = []   # (表示文字, 種別, 打つかな or 漢字)
        for x in al:
            if x[0] == 'C':
                ch = x[1]
                units.append({'t': ch, 'k': 'kana', 'kana': k2h(ch)})
                continue
            run, rd = x[1], x[2]
            sup = [c in TABLE for c in run]
            if all(not s for s in sup):
                for c in rd:
                    units.append({'t': c, 'k': 'yomi', 'kana': c, 'src': run})
                continue
            segs = [rd] if len(run) == 1 else (SPLIT_FIX.get((run, rd)) or split(run, rd)[0])
            prev_kanji = False
            for c, seg in zip(run, segs):
                ok = c in TABLE and (c != '々' or prev_kanji)
                if ok:
                    units.append({'t': c, 'k': 'kanji', 'kana': None, 'yomi': seg})
                    prev_kanji = True
                else:
                    for cc in seg:
                        units.append({'t': cc, 'k': 'yomi', 'kana': cc, 'src': c})
                    prev_kanji = False
        lines.append(units)
    return lines

# ---- 2. 薙刀式 v18 -----------------------------------------------------
UN = dict(zip('きてしろけとかっほひはこそるすへくあいうーたなんられ',
              ['w','e','r','a','s','d','f','g','z','x','c','v','b','i','o','p','h','j','k','l',';','n','m',',','.','/']))
SH = dict(zip('ねりめせみにまちを、ぬさよえゆやのもつふおむわ。',
              ['w','e','r','a','s','d','f','g','c','v','b','u','i','o','p','h','j','k','l',';','n',',','.','m']))
POS = {**UN, **SH}
LEFT = set('qwertasdfgzxcvb')
DAKU = dict(zip('がぎぐげござじずぜぞだぢづでどばびぶべぼゔ', 'かきくけこさしすせそたちつてとはひふへほう'))
HAN = dict(zip('ぱぴぷぺぽ', 'はひふへほ'))
SMALL = dict(zip('ぁぃぅぇぉゃゅょゎ', 'あいうえおやゆよわ'))
YK = {'ゃ': 'h', 'ゅ': 'p', 'ょ': 'i'}

def daku_key(k): return 'j' if k in LEFT else 'f'
def han_key(k): return 'm' if k in LEFT else 'v'

def base_keys(c):
    """1文字のかなを押すキーの組（シフトは space）"""
    if c in UN: return [UN[c]]
    if c in SH: return ['space', SH[c]]
    if c in DAKU: b = POS[DAKU[c]]; return [b, daku_key(b)]
    if c in HAN: b = POS[HAN[c]]; return [b, han_key(b)]
    if c in SMALL: return ['q', POS[SMALL[c]]]
    if c == '？': return ['j', 'k', 'd']
    if c == '・': return ['j', 'k', 't']
    return None

def naginata(kana):
    """かな列 → アクション列。拗音・外来音は2〜3キー同時押し"""
    acts = []
    i = 0
    while i < len(kana):
        c = kana[i]; n = kana[i + 1] if i + 1 < len(kana) else ''
        if n in YK and c not in 'っ':
            if c in POS: keys = [POS[c], YK[n]]
            elif c in DAKU: b = POS[DAKU[c]]; keys = [b, daku_key(b), YK[n]]
            elif c in HAN: b = POS[HAN[c]]; keys = [b, han_key(b), YK[n]]
            else: raise ValueError(c + n)
            acts.append({'keys': keys, 'out': c + n}); i += 2; continue
        if c == 'ゔ' and n == 'ぁ':
            acts.append({'keys': ['l', 'f', 'j'], 'out': 'ゔぁ'}); i += 2; continue
        k = base_keys(c)
        if k is None:
            acts.append({'keys': [], 'out': c, 'skip': True})
        else:
            acts.append({'keys': k, 'out': c})
        i += 1
    return acts

def kanji_actions(c):
    kind, key, desc = TABLE[c]
    if kind == 'tan':
        return [{'keys': ['henkan', key], 'out': c, 'mode': '単打'}]
    if kind in ('pre_v', 'pre_m'):
        pk = 'v' if kind == 'pre_v' else 'm'
        return [{'keys': ['henkan', pk], 'out': '', 'mode': desc + '（前置）', 'pre': True},
                {'keys': [key], 'out': c, 'mode': desc}]
    return [{'keys': HOLD[kind] + [key], 'out': c, 'mode': '機能面・' + desc}]

SKIP_CHARS = set('　\n')

def to_actions(units, kana_only=False):
    """units → アクション列（表示用に unit 番号を付ける）"""
    acts = []
    buf = []   # 連続するかな（拗音の判定のため一括処理）
    def flush():
        if not buf: return
        s = ''.join(u['kana'] for _, u in buf)
        idx = [ui for ui, _ in buf]
        pos = 0
        for a in naginata(s):
            L = len(a['out'])
            a['u'] = idx[pos:pos + L]
            pos += L
            acts.append(a)
        buf.clear()
    for ui, u in enumerate(units):
        if u['t'] in SKIP_CHARS:
            flush(); continue
        if u['k'] == 'kanji' and not kana_only:
            flush()
            for a in kanji_actions(u['t']):
                a['u'] = [ui]; acts.append(a)
        elif u['k'] == 'kanji':
            for c in u['yomi']:
                buf.append((ui, {'kana': c}))
        else:
            buf.append((ui, u))
    flush()
    return acts

def stats(acts):
    real = [a for a in acts if not a.get('skip')]
    return {'actions': len(real),
            'keys': sum(len(a['keys']) for a in real),
            'chords': sum(1 for a in real if len(a['keys']) >= 2),
            'kanji_actions': sum(1 for a in real if 'mode' in a),
            'skipped': [a['out'] for a in acts if a.get('skip')]}

if __name__ == '__main__':
    lines = build_units()
    clip = lines[0] + [{'t': '\n', 'k': 'kana', 'kana': '\n'}] + lines[1]
    full = []
    for ln in lines:
        full += ln + [{'t': '\n', 'k': 'kana', 'kana': '\n'}]
    out = {}
    for name, us in (('clip', clip), ('full', full)):
        a1 = to_actions(us); a0 = to_actions(us, kana_only=True)
        kan = sum(1 for u in us if u['k'] == 'kanji')
        out[name] = {'units': us, 'acts': a1, 'stats': stats(a1), 'kana_stats': stats(a0),
                     'kanji_chars': kan,
                     'chars': sum(1 for u in us if u['t'] not in SKIP_CHARS)}
        print(name, 'chars', out[name]['chars'], 'kanji', kan)
        print('  漢直あり', {k: v for k, v in stats(a1).items() if k != 'skipped'}, 'skip', stats(a1)['skipped'][:10])
        print('  かなのみ', {k: v for k, v in stats(a0).items() if k != 'skipped'})
    # 表示用テキスト
    print(''.join(u['t'] for u in clip))
    json.dump(out, open(os.path.join(WORK, 'built.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    open(os.path.join(HERE, 'texts', 'wagahai_oneshot.txt'), 'w', encoding='utf-8').write(''.join(u['t'] for u in full))
