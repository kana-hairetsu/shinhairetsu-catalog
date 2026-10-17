# -*- coding: utf-8 -*-
"""かむ配列の配列定義（map）を、行×段の組み合わせから組み立てる。

    python tools/build_kamu.py

tools/layouts/kamu.seed.json の _gyou / _dan / _sub を読み、
すべてのかなへの割り当てを展開して tools/layouts/kamu.json に書き出す。
作者ご本人に確認していただくときは、このファイルをお渡しするとよい。
"""
import json, os

SEED = "tools/layouts/kamu.seed.json"
OUT = "tools/layouts/kamu.json"

# 行×段の表。空白は割り当て無し
TABLE = {
    "あ": "あいうえお", "か": "かきくけこ", "さ": "さしすせそ", "た": "たちつてと",
    "な": "なにぬねの", "は": "はひふへほ", "ま": "まみむめも",
    "や": "や、ゆんよ",     # や行い段＝「、」／や行え段＝「ん」
    "ら": "らりるれろ",
    "わ": "わ 。 を",       # わ行う段＝「。」。い段・え段は割り当て無し
    "が": "がぎぐげご", "ざ": "ざじずぜぞ", "だ": "だぢづでど",
    "ば": "ばびぶべぼ", "ぱ": "ぱぴぷぺぽ", "ぁ": "ぁぃぅぇぉ",
}
DAN_ORDER = ["あ", "い", "う", "え", "お"]
# 拗音を作れる行（い段の文字＋ゃゅょ）
YOUON = {"か": "き", "さ": "し", "た": "ち", "な": "に", "は": "ひ", "ま": "み",
         "ら": "り", "が": "ぎ", "ざ": "じ", "だ": "ぢ", "ば": "び", "ぱ": "ぴ"}


def chord(*parts):
    keys = [k for p in parts if p for k in p.split("+")]
    return "+".join(sorted(keys, key=lambda k: (k[0], int(k[1]))))


def main():
    seed = json.load(open(SEED, encoding="utf-8"))
    gyou, dan, sub = seed["_gyou"], seed["_dan"], seed["_sub"]
    m = {}

    for g, chars in TABLE.items():
        for i, ch in enumerate(chars):
            if ch != " ":
                m[ch] = chord(gyou[g], dan[DAN_ORDER[i]])

    for g, head in YOUON.items():
        for small in ("ゃ", "ゅ", "ょ"):
            m[head + small] = chord(gyou[g], sub[small])

    for ch, spec in sub.items():
        m[ch] = chord(spec)
    m["ゎ"] = chord(sub["ゃ"])

    out = dict(seed)
    out["map"] = dict(sorted(m.items(), key=lambda x: (len(x[0]), x[0])))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    from collections import Counter
    c = Counter(len(v.split("+")) for v in m.values())
    print(f"{len(m)}文字を割り当てました → {OUT}")
    print("  " + " / ".join(f"{k}キー同時 {n}文字" for k, n in sorted(c.items())))


if __name__ == "__main__":
    main()
