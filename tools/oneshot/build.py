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
# ワンショット漢直は混ぜ書き変換を使わない。語の中に表に無い漢字が1字でもあれば、
# その語はまるごとひらがなで打つ（「名前」→「なまえ」。「な前」とは打たない）。
# 語の区切りは MeCab で取り、接頭辞・接尾辞・続く数詞は前後の語にまとめる
# 数詞に続く助数詞もまとめる（「第一」「一度」「人間中」などを1語として扱う）。
import fugashi
_tagger = fugashi.Tagger()

def is_kanji(c):
    return ('\u4e00' <= c <= '\u9fff') or c in '々〆'

def word_ids(text):
    """文字位置ごとの語番号"""
    toks, pos = [], 0
    for w in _tagger(text):
        k = text.find(w.surface, pos)
        if k < 0:
            continue
        f = w.feature
        toks.append([k, k + len(w.surface), f.pos1 or '', f.pos2 or '', f.pos3 or ''])
        pos = k + len(w.surface)
    merged = []
    for t in toks:
        if merged:
            p = merged[-1]
            if (p[2] == '接頭辞' or t[2] == '接尾辞'
                    or (p[3] == '数詞' and (t[3] == '数詞' or t[4] == '助数詞可能'))) and p[1] == t[0]:
                p[1] = t[1]
                p[2], p[3], p[4] = t[2], t[3], t[4]
                continue
        merged.append(list(t))
    ids = [-1] * len(text)
    for n, (a, b, *_) in enumerate(merged):
        for i in range(a, b):
            ids[i] = n
    return ids

def build_units():
    d = json.load(open(os.path.join(WORK, 'aligned.json'), encoding='utf-8'))
    lines = []
    for al in d['aligned']:
        clean = ''.join(x[1] for x in al)
        ids = word_ids(clean)
        bad = set()
        for i, c in enumerate(clean):
            if is_kanji(c) and c not in TABLE:
                bad.add(ids[i])
        units = []   # (表示文字, 種別, 打つかな or 漢字)
        p = 0
        prev_kanji = False
        for x in al:
            if x[0] == 'C':
                ch = x[1]
                units.append({'t': ch, 'k': 'kana', 'kana': k2h(ch)})
                p += 1
                prev_kanji = False
                continue
            run, rd = x[1], x[2]
            keep = [c in TABLE and ids[p + i] not in bad for i, c in enumerate(run)]
            p += len(run)
            if not any(keep):
                for c in rd:
                    units.append({'t': c, 'k': 'yomi', 'kana': c, 'src': run})
                prev_kanji = False
                continue
            segs = [rd] if len(run) == 1 else (SPLIT_FIX.get((run, rd)) or split(run, rd)[0])
            for c, seg, ok in zip(run, segs, keep):
                ok = ok and (c != '々' or prev_kanji)
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
