# -*- coding: utf-8 -*-
"""漢字混じり原文（ルビ入り）と、ひらがな化済み本文を行ごとにアライメントし、
漢字の連なり（run）ごとの読みを取り出す。"""
import json, sys
import fugashi
_tagger = fugashi.Tagger()

def run_estimates(raw):
    """MeCabで原文を解析し、各文字位置の漢字が担う読みの長さを推定する。"""
    per = [0.0] * len(raw)
    pos = 0
    for w in _tagger(raw):
        surf = w.surface
        k = raw.find(surf, pos)
        if k < 0:
            continue
        pos = k + len(surf)
        kan = [i for i, c in enumerate(surf) if is_kanji(c)]
        if not kan:
            continue
        rd = w.feature.kana or ''
        rd = ''.join(norm(c) for c in rd)
        # 送りがな（語末・語頭のかな）を読みから除く
        a, b = 0, len(surf)
        while a < b and not is_kanji(surf[a]):
            a += 1
        while b > a and not is_kanji(surf[b - 1]):
            b -= 1
        pre = ''.join(norm(c) for c in surf[:a]); suf = ''.join(norm(c) for c in surf[b:])
        if pre and rd.startswith(pre): rd = rd[len(pre):]
        if suf and rd.endswith(suf): rd = rd[:-len(suf)]
        if not rd:
            rd = 'xx' * (b - a)
        share = len(rd) / (b - a)
        for i in range(a, b):
            per[k + i] = share
    return per

def is_kanji(c):
    return ('一' <= c <= '鿿') or c in '々〆'

def norm(c):
    o = ord(c)
    if 0x30A1 <= o <= 0x30F6:  # カタカナ→ひらがな
        return chr(o - 0x60)
    if c == 'ヴ':
        return 'ゔ'
    return c

def align_line(raw, hira):
    # raw を「かな1字」または「漢字run」の単位に分割
    units = []
    i = 0
    while i < len(raw):
        if is_kanji(raw[i]):
            j = i
            while j < len(raw) and is_kanji(raw[j]):
                j += 1
            units.append(('K', i, j))
            i = j
        elif raw[i] == '|':
            units.append(('M', i, i + 1))
            i += 1
        else:
            units.append(('C', i, i + 1))
            i += 1
    per = run_estimates(raw)
    # 前向きDP: 状態 = (rawの位置, hiraの位置)
    import heapq
    start = (0, 0)
    back = {start: None}
    dist = {start: 0}
    pos2unit = {u[1]: u for u in units}
    q = [(0, start)]
    goal = (len(raw), len(hira))
    done = set()
    while q:
        cst, st = heapq.heappop(q)
        if st in done:
            continue
        done.add(st)
        if st == goal:
            break
        i, j = st
        if i >= len(raw):
            continue
        u = pos2unit.get(i)
        nexts = []
        if u[0] == 'M':
            nexts.append(((i + 1, j), None, 0))
        elif u[0] == 'C':
            if j < len(hira) and norm(raw[i]) == hira[j]:
                nexts.append(((i + 1, j + 1), ('C', raw[i]), 0))
        else:
            _, a, b = u
            L = b - a
            E = sum(per[a:b]) or 2.0 * L
            for n in range(1, 4 * L + 2):
                if j + n > len(hira):
                    break
                rd = hira[j:j + n]
                if any(is_kanji(c) for c in rd):
                    break
                # ルビの読み飛ばし（読みの末尾と一致する直後のかな）を優先
                for m in (range(n, 0, -1) if raw[b:b + 1] != '|' else []):
                    seg = raw[b:b + m]
                    if len(seg) == m and ''.join(norm(c) for c in seg) == rd[n - m:] \
                            and not any(is_kanji(c) for c in seg):
                        nexts.append(((b + m, j + n), ('K', raw[a:b], rd, seg), abs(n - E) + 0.5))
                nexts.append(((b, j + n), ('K', raw[a:b], rd, ''), abs(n - E)))
        for ns, lab, c in nexts:
            nc = cst + c
            if nc < dist.get(ns, 1e18):
                dist[ns] = nc
                back[ns] = (st, lab)
                heapq.heappush(q, (nc, ns))
    if goal not in back:
        raise ValueError('align failed: ' + raw[:40])
    out = []
    st = goal
    while back[st] is not None:
        st, lab = back[st]
        if lab is not None:
            out.append(lab)
    out.reverse()
    return out

if __name__ == '__main__':
    raw_lines = open(sys.argv[1], encoding='utf-8').read().splitlines()
    hira_lines = open(sys.argv[2], encoding='utf-8').read().splitlines()
    assert len(raw_lines) == len(hira_lines), (len(raw_lines), len(hira_lines))
    res = []
    for r, h in zip(raw_lines, hira_lines):
        res.append(align_line(r, h))
    json.dump(res, open(sys.argv[3], 'w', encoding='utf-8'), ensure_ascii=False)
    print('lines', len(res))
