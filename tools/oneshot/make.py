# -*- coding: utf-8 -*-
"""薙刀式＋ワンショット漢直（一打漢直）の動画・ヒートマップのデータを作る。

    python tools/oneshot/make.py

typing-distance のエンジンには漢直の仕組みが無いため、この配列だけは
ここで打鍵列を組み立てる。手順は次のとおり。

  1. ルビ入りの漢字まじり原文と、ひらがな化済み本文を突き合わせ、漢字ごとの読みを取る
     （run_align.py → work/aligned.json）
  2. 一打漢直の表にある漢字は漢字のまま、無い漢字はひらがなに置き換える
  3. かなは薙刀式 v18、漢字は一打漢直の5レイヤーで打鍵列にする（build.py）
  4. public/anim/naginata-oneshot.json と src/data/heat.json の該当エントリを書き出す

かなだけで打った場合の集計は、エンジンで計算した薙刀式の値と一致することを確認済み。
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
WORK = os.path.join(HERE, 'work')
sys.path.insert(0, HERE)

ID = 'naginata-oneshot'
NAME = '薙刀式＋ワンショット漢直'
GENRE_ID = 'kanchoku'
SKIP = set('　\n')


def run(script):
    subprocess.run([sys.executable, os.path.join(HERE, script)], check=True,
                   stdout=subprocess.DEVNULL)


def main():
    run('run_align.py')
    run('build.py')
    from kanji_table import TABLE
    from build import UN, SH

    genres = json.load(open(os.path.join(ROOT, 'src/data/genres.json'), encoding='utf-8'))
    g = next(x for x in genres if x['id'] == GENRE_ID)
    built = json.load(open(os.path.join(WORK, 'built.json'), encoding='utf-8'))

    # ---- 漢字面（盤面の刻印を差し替えるための表） ----
    LAYER = {'tan': 'tan', 'pre_v': 'V', 'pre_m': 'M', 'mid_r': 'mid', 'mid_l': 'mid',
             'bot_r': 'bot', 'bot_l': 'bot'}
    layers = {k: {} for k in ('tan', 'V', 'M', 'mid', 'bot')}
    for ch, (kind, key, _) in TABLE.items():
        layers[LAYER[kind]][key] = ch
    layers['tan']['v'] = layers['tan']['m'] = '前置'
    layers['V']['v'] = layers['M']['m'] = '×'
    names = {'tan': '主漢字面・単打（変換＋キー）',
             'V': '主漢字面・変換＋V のあと（左：同手／右：逆手）',
             'M': '主漢字面・変換＋M のあと（左：逆手／右：同手）',
             'mid': '機能漢字面・同時1（中段3キー＋逆手）',
             'bot': '機能漢字面・同時2（下段3キー＋逆手）'}

    def actions(part):
        units = part['units']
        pos, text = {}, []
        for i, u in enumerate(units):
            if u['t'] in SKIP:
                continue
            pos[i] = len(text)
            text.append(u['t'])
        out = []
        for a in part['acts']:
            if a.get('skip'):
                continue
            o = {'c': pos[max(a['u'])], 'k': a['keys']}
            if 'mode' in a:
                if a.get('pre'):
                    o['L'] = 'V' if 'v' in a['keys'] else 'M'
                else:
                    o['L'] = LAYER[TABLE[a['out']][0]]
            out.append(o)
        return ''.join(text), out

    def summarize(acts):
        return {'actions': len(acts), 'keys': sum(len(a['k']) for a in acts),
                'chords': sum(1 for a in acts if len(a['k']) > 1)}

    clip_text, clip_acts = actions(built['clip'])
    _, full_acts = actions(built['full'])
    # 既存の配列と同じ区間（ひらがなで553字／10,872字）を打っている
    data = {'text': clip_text, 'clip_chars': 553, 'full_chars': 10872,
            'layout': {'id': ID, 'name': NAME, 'genre': g['name'], 'color': g['color'],
                       'actions': clip_acts, 'full': summarize(full_acts),
                       'clip': summarize(clip_acts),
                       'layers': layers, 'layer_names': names}}
    out = os.path.join(ROOT, 'public/anim', ID + '.json')
    json.dump(data, open(out, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))

    # ---- ヒートマップ ----
    from collections import Counter
    count = Counter(k for a in full_acts for k in a['k'])
    left = set('qwertasdfgzxcvb')
    hands = {'L': 0, 'R': 0, 'thumb': 0}
    for k, n in count.items():
        hands['thumb' if k in ('space', 'henkan') else ('L' if k in left else 'R')] += n
    labels = {v: k for k, v in UN.items()}
    labels.update({'q': '小', 't': '←', 'y': '→', 'u': '', 'space': 'スペース（シフト）', 'henkan': '変換'})
    subs = {v: k for k, v in SH.items()}
    heat_path = os.path.join(ROOT, 'src/data/heat.json')
    heat = json.load(open(heat_path, encoding='utf-8'))
    heat[ID] = {'id': ID, 'name': NAME, 'genre': g['name'], 'color': g['color'],
                'labels': labels, 'subs': subs, 'heat': dict(count), 'hands': hands,
                'total': sum(count.values()), 'chars': 10872}
    json.dump(heat, open(heat_path, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))

    s, k = data['layout']['clip'], data['layout']['full']
    kana = built['full']['kana_stats']
    print(f'動画 {len(clip_text)}字  アクション {s["actions"]} / 打鍵 {s["keys"]} / 同時押し {s["chords"]}')
    print(f'全文          アクション {k["actions"]:,} / 打鍵 {k["keys"]:,} / 同時押し {k["chords"]:,}')
    print(f'（かなのみ    アクション {kana["actions"]:,} / 打鍵 {kana["keys"]:,} / 同時押し {kana["chords"]:,}）')
    print(f'{out} と {heat_path} を書き出しました')


if __name__ == '__main__':
    main()
