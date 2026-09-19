# -*- coding: utf-8 -*-
"""タイピング動画のデータを public/anim/<id>.json に書き出す。

計算そのものは別リポジトリ typing-distance の typing_distance.py に任せる。
このスクリプトは、その出力を「どのキーがいつ光るか」の形に並べ替えるだけ。

    python tools/make_animation.py --engine ../typing-distance

--engine には typing-distance のフォルダを指定する。その中の
  typing_distance.py / texts/wagahai.txt / texts/wagahai_500.txt / layouts/*.json
を読む。対象の配列は tools/anim_layouts.json に書く。
"""
import argparse, json, os, sys
from collections import Counter

# キーの並び（ロウスタッガード／オーソリニア／カラムスタッガード）は
# サイト側の src/lib/keyboard.js が決める。ここでは「どのキーに何が刷られるか」だけ出す。
NUM_ROW = list("1234567890-")


def alpha_labels(td, rows, num):
    lab = {}
    for c, k in zip(list(rows[0]) + list(rows[1]) + list(rows[2]), td.ALPHA_SLOTS):
        lab[k] = c.upper()
    for c, k in zip(num, NUM_ROW):
        lab[k] = c
    return lab, {}


def kana_labels(layout):
    """単打の印字と、シフト同時押し（裏レイヤー）の印字。
    シフトキーは、1文字のかなを出す2キー同時押しで最も多く使われているキーとみなす。"""
    pairs = [s.split("+") for k, s in layout["map"].items()
             if isinstance(s, str) and len(k) == 1]
    cnt = Counter(p[0] for p in pairs if len(p) == 2)
    shift_key = cnt.most_common(1)[0][0] if cnt else None
    base, sub = {}, {}
    for kana, spec in layout["map"].items():
        if not isinstance(spec, str) or len(kana) != 1:
            continue
        parts = spec.split("+")
        if len(parts) == 1:
            base.setdefault(parts[0], kana)
        elif len(parts) == 2 and parts[0] == shift_key:
            sub.setdefault(parts[1], kana)
    if shift_key:
        base[shift_key] = "シフト"
    return base, sub


# ---- 打鍵列（どの文字を打っているかの位置つき） ----------------------------
def units_kana(text):
    """っ／ん／拗音をまとめた最小単位に切る。
    ローマ字化は次の文字に依存する（っ＝子音を重ねる、ん＝次がaiueonyなら nn）ため、
    依存先を同じ単位に入れないと全文一括の変換結果とずれる。"""
    out, i, n = [], 0, len(text)
    while i < n:
        j = i
        while text[j] in "っん" and j + 1 < n:
            j += 1
        if j + 1 < n and text[j + 1] in "ゃゅょぁぃぅぇぉ":
            j += 1
        out.append((i, text[i:j + 1]))
        i = j + 1
    return out


def actions_romaji(td, text, layout):
    acts = []
    for ci, unit in units_kana(text):
        for ch in td.kana_to_romaji(unit):
            spec = layout["map"].get(ch)
            if spec is None:
                continue
            main, mods = td.parse_stroke(spec)
            acts.append({"c": ci, "k": mods + [main]})
    return acts


def actions_kana(td, text, layout):
    """keystrokes_kana の min_actions と同じ切り分けを、文字位置つきで再現する"""
    m = {k: v for k, v in layout["map"].items() if v}
    maxlen = max(len(k) for k in m)
    n = len(text)
    INF = float("inf")
    best = [INF] * (n + 1); back = [None] * (n + 1); best[0] = 0
    for i in range(n):
        if best[i] == INF:
            continue
        for ln in range(1, min(maxlen, n - i) + 1):
            seg = text[i:i + ln]
            if seg not in m:
                continue
            st = td.parse_entry(m[seg])
            if best[i] + len(st) < best[i + ln]:
                best[i + ln] = best[i] + len(st); back[i + ln] = (i, st)
        if best[i] < best[i + 1] and back[i + 1] is None:
            best[i + 1] = best[i]; back[i + 1] = (i, None)
    seq, pos = [], n
    while pos > 0:
        prev, st = back[pos]
        if st:
            seq.insert(0, (prev, st))
        pos = prev
    return [{"c": ci, "k": mods + [main]} for ci, st in seq for main, mods in st]


def summarize(acts):
    return {"actions": len(acts),
            "keys": sum(len(a["k"]) for a in acts),
            "chords": sum(1 for a in acts if len(a["k"]) > 1)}


def summarize_strokes(strokes):
    return summarize([{"k": mods + [main]} for main, mods in strokes])


def heatmap(td, strokes):
    """お題文全体を打ったときの、キーごとの打鍵回数と左右の内訳"""
    count = Counter()
    for main, mods in strokes:
        count[main] += 1
        for m in mods:
            count[m] += 1
    hands = {"L": 0, "R": 0, "thumb": 0}
    for k, n in count.items():
        if k in getattr(td, "THUMB_KEYS", set()):
            hands["thumb"] += n
        else:
            hands[td.HAND_OF_KEY.get(k, "L")] += n
    return dict(count), hands


# ---- 本体 ------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", required=True, help="typing-distance のフォルダ")
    ap.add_argument("--config", default="tools/anim_layouts.json")
    ap.add_argument("--out", default="public/anim")
    ap.add_argument("--heat-out", default="src/data/heat.json")
    a = ap.parse_args()

    sys.path.insert(0, a.engine)
    import typing_distance as td

    def read(*parts):
        for cand in (os.path.join(a.engine, *parts),
                     os.path.join(a.engine, parts[-1])):
            if os.path.exists(cand):
                return open(cand, encoding="utf-8").read()
        raise SystemExit(f"見つかりません: {os.path.join(*parts)}")

    full = read("texts", "wagahai.txt").replace("\n", "").replace("\u3000", "")
    clip = read("texts", "wagahai_500.txt").replace("\n", "").replace("\u3000", "")
    cfg = json.load(open(a.config, encoding="utf-8"))
    os.makedirs(a.out, exist_ok=True)

    print(f"集計 {len(full)}字 ／ 動画 {len(clip)}字\n")
    print(f'{"id":<12}{"配列":<16}{"アクション":>10}{"打鍵":>9}{"同時押し":>9}{"左右":>12}')
    heat_all = {}
    for c in cfg:
        if c["mode"] == "romaji":
            lay = td.alpha_layout(c["name"], *c["rows"], extra=c.get("extra"))
            labels, subs = alpha_labels(td, c["rows"], c["num"])
            acts = actions_romaji(td, clip, lay)
            full_strokes = td.keystrokes_romaji(full, lay)
            ref = summarize_strokes(td.keystrokes_romaji(clip, lay))
        else:
            lay = json.load(open(os.path.join(a.engine, c["json"]), encoding="utf-8"))
            labels, subs = kana_labels(lay)
            acts = actions_kana(td, clip, lay)
            full_strokes = td.keystrokes_kana(full, lay)
            ref = summarize_strokes(td.keystrokes_kana(clip, lay))
        sf = summarize_strokes(full_strokes)
        sc = summarize(acts)
        assert ref == sc, f"{c['id']}: エンジンの結果と一致しません {ref} != {sc}"
        heat, hands = heatmap(td, full_strokes)
        heat_all[c["id"]] = {
            "id": c["id"], "name": c["name"], "genre": c["genre"], "color": c["color"],
            "labels": labels, "subs": subs, "heat": heat, "hands": hands,
            "total": sf["keys"], "chars": len(full),
        }

        data = {"text": clip, "full_chars": len(full), "clip_chars": len(clip),
                "layout": {"id": c["id"], "name": c["name"], "genre": c["genre"],
                           "color": c["color"],
                           "actions": acts, "full": sf, "clip": sc}}
        path = os.path.join(a.out, c["id"] + ".json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        bal = hands["L"] + hands["R"] + hands["thumb"]
        print(f'{c["id"]:<12}{c["name"]:<16}{sf["actions"]:>10,}{sf["keys"]:>9,}'
              f'{sf["chords"]:>9,}{hands["L"]*100//bal:>6}:{hands["R"]*100//bal:<5}')

    os.makedirs(os.path.dirname(a.heat_out), exist_ok=True)
    with open(a.heat_out, "w", encoding="utf-8") as f:
        json.dump(heat_all, f, ensure_ascii=False, separators=(",", ":"))
    print(f'\n{a.heat_out} にヒートマップ用のデータを書き出しました')
    print("書き出し完了")


if __name__ == "__main__":
    main()
