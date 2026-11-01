# -*- coding: utf-8 -*-
"""メジロ式の動画・ヒートマップのデータを作る。

    python tools/mejiro/make.py --engine ../typing-distance

メジロ式は速記なので、typing-distance のエンジン（1文字ずつ打つ前提）では計算できない。
代わりに、作者の公式エンジン Mejiro_Engine（Rust）でお題文を打てるストローク列を探し、
それを「どのキーを同時に押したか」の形に並べ替える。探し方は encoder/src/main.rs の冒頭を参照。

  1. tools/mejiro/encoder（Rust）がお題文をストローク列に直す
       → tools/mejiro/strokes_clip.json（動画 553字）
       → tools/mejiro/strokes_full.json（集計 10,872字）
     Rust が使えない環境では --skip-encode を付けると、保存済みの2つをそのまま使う
  2. このスクリプトが public/anim/mejiro.json と src/data/heat.json の mejiro を書く

1ストローク＝1アクション。打鍵数はそのストロークで押したキーの数。
"""
import argparse, json, os, subprocess, sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

ID, NAME, GENRE, COLOR = "mejiro", "メジロ式", "速記系", "#7A5C2E"
# 盤面の刻印。キーIDは src/lib/keyboard.js の STENO_KEYS と同じ
LEFT = "#STKNYIAUntk"
RIGHT = "STKNYIAUntk*"
THUMBS = {"Ln", "Lt", "Lk", "Rn", "Rt", "Rk"}


def keys_of(stroke):
    """ 'TAk-SAn' → ['LT','LA','Lk','RS','RA','Rn'] """
    left, _, right = stroke.partition("-")
    out = ["L" + c for c in left]
    for c in right:
        out.append("R*" if c == "*" else "R" + c)
    assert all((k[1] in (LEFT if k[0] == "L" else RIGHT)) for k in out), stroke
    return out


def actions(enc):
    acts = []
    for st in enc["strokes"]:
        acts.append({"c": st["c"], "n": len(st["o"]), "k": keys_of(st["s"]),
                     "s": st["s"], "o": st["o"]})
    return acts


def summarize(acts):
    return {"actions": len(acts),
            "keys": sum(len(a["k"]) for a in acts),
            "chords": sum(1 for a in acts if len(a["k"]) > 1)}


def heatmap(acts):
    count = Counter(k for a in acts for k in a["k"])
    hands = {"L": 0, "R": 0, "thumb": 0}
    for k, n in count.items():
        hands["thumb" if k in THUMBS else k[0]] += n
    return dict(count), hands


def encode(text_path, out_path):
    enc_dir = os.path.join(HERE, "encoder")
    with open(out_path, "w", encoding="utf-8") as f:
        subprocess.run(["cargo", "run", "--release", "--quiet", "--", text_path],
                       cwd=enc_dir, stdout=f, check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", required=True, help="typing-distance のフォルダ（お題文を読む）")
    ap.add_argument("--skip-encode", action="store_true", help="保存済みのストローク列を使う")
    a = ap.parse_args()

    texts = {k: os.path.abspath(os.path.join(a.engine, "texts", f))
             for k, f in (("clip", "wagahai_500.txt"), ("full", "wagahai.txt"))}
    enc = {}
    for k, path in texts.items():
        out = os.path.join(HERE, f"strokes_{k}.json")
        if not a.skip_encode:
            print(f"ストローク列を探しています（{k}）…", file=sys.stderr)
            encode(path, out)
        enc[k] = json.load(open(out, encoding="utf-8"))

    read = lambda p: open(p, encoding="utf-8").read().replace("\n", "").replace("　", "")
    full, clip = read(texts["full"]), read(texts["clip"])
    assert len(full) == enc["full"]["chars"] and len(clip) == enc["clip"]["chars"], "お題文が変わっています"

    # 検算：各ストロークの出力が、その位置のお題文と一致する（カタカナ・半角記号はそろえて比べる）
    def same(o, t):
        tbl = {ord("?"): "？", ord("!"): "！"}
        o = "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヴ" else c for c in o.translate(tbl))
        return o == t
    for k, t in (("clip", clip), ("full", full)):
        for st in enc[k]["strokes"]:
            assert same(st["o"], t[st["c"]:st["c"] + len(st["o"])]), (k, st)

    acts_clip, acts_full = actions(enc["clip"]), actions(enc["full"])
    sc, sf = summarize(acts_clip), summarize(acts_full)
    heat, hands = heatmap(acts_full)

    labels = {}
    for c in LEFT:
        labels["L" + c] = c
    for c in RIGHT:
        labels["R*" if c == "*" else "R" + c] = c

    data = {"text": clip, "full_chars": len(full), "clip_chars": len(clip),
            "layout": {"id": ID, "name": NAME, "genre": GENRE, "color": COLOR,
                       "actions": acts_clip, "full": sf, "clip": sc}}
    path = os.path.join(ROOT, "public", "anim", ID + ".json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

    heat_path = os.path.join(ROOT, "src", "data", "heat.json")
    heat_all = json.load(open(heat_path, encoding="utf-8"))
    heat_all[ID] = {"id": ID, "name": NAME, "genre": GENRE, "color": COLOR,
                    "labels": labels, "subs": {}, "heat": heat, "hands": hands,
                    "total": sf["keys"], "chars": len(full)}
    with open(heat_path, "w", encoding="utf-8") as f:
        json.dump(heat_all, f, ensure_ascii=False, separators=(",", ":"))

    star = sum(1 for x in acts_full if x["s"].endswith("*"))
    bal = hands["L"] + hands["R"] + hands["thumb"]
    print(f"動画 {len(clip)}字：{sc['actions']}ストローク・{sc['keys']}打鍵")
    print(f"集計 {len(full)}字：{sf['actions']:,}ストローク・{sf['keys']:,}打鍵"
          f"（1ストロークあたり {len(full) / sf['actions']:.2f}字、うち * を使う {star}回）")
    print(f"左手 {hands['L'] * 100 / bal:.1f}% ／ 親指 {hands['thumb'] * 100 / bal:.1f}%"
          f" ／ 右手 {hands['R'] * 100 / bal:.1f}%")
    skipped = "".join(c for _, c in enc["full"]["skipped"])
    if skipped:
        print(f"打たなかった文字：{skipped}（ダッシュはどの配列でも打鍵に含めない）")


if __name__ == "__main__":
    main()
