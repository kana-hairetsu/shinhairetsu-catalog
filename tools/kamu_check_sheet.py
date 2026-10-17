# -*- coding: utf-8 -*-
"""かむ配列の確認シートを作る。作者ご本人に内容を見ていただくための1枚。

    python tools/kamu_check_sheet.py
"""
import json, os

LAY = json.load(open("tools/layouts/kamu.json", encoding="utf-8"))
GYOU, DAN, SUB = LAY["_gyou"], LAY["_dan"], LAY["_sub"]
FING = LAY["_fingers"]
MAP = LAY["map"]

# 画面上の並び（左は外側から、右は内側から）
ORDER = ["l1", "l2", "l3", "l4", "l5", "r1", "r2", "r3", "r4", "r5"]
X = {"l1": 0, "l2": 1, "l3": 2, "l4": 3, "l5": 4,
     "r1": 5.4, "r2": 6.4, "r3": 7.4, "r4": 8.4, "r5": 9.4}
Y = {"l5": 1, "r1": 1}

TABLE = {
    "あ": "あいうえお", "か": "かきくけこ", "さ": "さしすせそ", "た": "たちつてと",
    "な": "なにぬねの", "は": "はひふへほ", "ま": "まみむめも",
    "や": "や、ゆんよ", "ら": "らりるれろ", "わ": "わ 。 を",
    "が": "がぎぐげご", "ざ": "ざじずぜぞ", "だ": "だぢづでど",
    "ば": "ばびぶべぼ", "ぱ": "ぱぴぷぺぽ", "ぁ": "ぁぃぅぇぉ",
}
DAN_ORDER = ["あ", "い", "う", "え", "お"]
U, K = 56, 50

single = {}
for name, spec in {**GYOU, **DAN}.items():
    if spec and "+" not in spec:
        single[spec] = name


def board(highlight=()):
    w = max(X.values()) * U + K + 2
    h = 2 * U + 24
    s = [f'<svg viewBox="0 0 {w:.0f} {h:.0f}" xmlns="http://www.w3.org/2000/svg">']
    for kid in ORDER:
        x, y = 1 + X[kid] * U, 1 + Y.get(kid, 0) * U
        on = kid in highlight
        s.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{K}" height="{K}" rx="6" '
                 f'fill="{"#4A6E8A" if on else "#fff"}" stroke="{"#4A6E8A" if on else "#B4B3AB"}"/>')
        s.append(f'<text x="{x+K/2:.1f}" y="{y+K/2+9:.1f}" font-size="24" text-anchor="middle" '
                 f'font-family="serif" fill="{"#fff" if on else "#23262A"}">{single.get(kid,"")}</text>')
        s.append(f'<text x="{x+K/2:.1f}" y="{y+K+16:.1f}" font-size="11" text-anchor="middle" '
                 f'fill="#9C9B92">{FING[kid]}</text>')
    return "".join(s) + "</svg>"


def mini(spec):
    """押すキーを小さな丸10個で示す"""
    keys = set(spec.split("+")) if spec else set()
    out = []
    for kid in ORDER:
        on = kid in keys
        gap = ' style="margin-left:7px"' if kid == "r1" else ""
        out.append(f'<i class="{"on" if on else ""}"{gap}></i>')
    return "".join(out)


rows = []
for g, chars in TABLE.items():
    cells = "".join(f'<td class="{"x" if c==" " else ""}">{"" if c==" " else c}</td>'
                    for c in chars)
    rows.append(f'<tr><th><b>{g}行</b><span class="m">{mini(GYOU[g])}</span></th>{cells}</tr>')
head = "".join(f'<th><b>{d}段</b><span class="m">{mini(DAN[d])}</span></th>' for d in DAN_ORDER)
subs = "".join(f'<tr><th><b>{k}</b></th><td><span class="m">{mini(v)}</span></td></tr>'
               for k, v in SUB.items())

from collections import Counter
cnt = Counter(len(v.split("+")) for v in MAP.values())
breakdown = "／".join(f"{k}キー同時 {n}文字" for k, n in sorted(cnt.items()))

html = f"""<!DOCTYPE html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>かむ配列｜掲載内容の確認シート</title>
<link href="https://fonts.googleapis.com/css2?family=BIZ+UDPGothic:wght@400;700&family=Shippori+Mincho+B1:wght@500;700&display=swap" rel="stylesheet">
<style>
:root{{--paper:#FBFAF7;--paper-2:#F1F0EA;--rule:#CFCEC6;--rule-strong:#9C9B92;
--ink:#23262A;--ink-soft:#5E6167;--gc:#4A6E8A}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--paper);color:var(--ink);font-family:"BIZ UDPGothic","Hiragino Sans",sans-serif;
font-size:15px;line-height:1.85}}
.wrap{{max-width:900px;margin:0 auto;padding:0 24px 72px}}
header{{border-top:4px solid var(--gc);padding-top:20px;margin:28px 0 24px}}
header .k{{font-size:12.5px;color:var(--gc);font-weight:700;letter-spacing:.08em}}
header h1{{font-family:"Shippori Mincho B1",serif;font-size:32px;font-weight:700;margin-top:4px}}
header p{{font-size:13.5px;color:var(--ink-soft);margin-top:10px;max-width:62ch}}
h2{{font-family:"Shippori Mincho B1",serif;font-size:19px;font-weight:700;
border-bottom:2px solid var(--ink);padding-bottom:7px;margin:38px 0 6px}}
.src{{font-size:11.5px;color:var(--ink-soft);margin-bottom:16px;max-width:66ch}}
.fig{{background:#fff;border:1px solid var(--rule);padding:22px}}
.fig svg{{width:100%;height:auto;display:block}}
table{{border-collapse:collapse;background:#fff;width:100%;font-size:18px;border:1px solid var(--rule)}}
th,td{{border:1px solid var(--rule);text-align:center;padding:6px 4px}}
thead th{{background:var(--paper-2);font-weight:400;padding:8px 4px}}
tbody th{{background:var(--paper-2);font-weight:400;white-space:nowrap}}
th b{{font-size:14px;font-family:"Shippori Mincho B1",serif;display:block}}
td{{font-family:"Shippori Mincho B1",serif}}
td.x{{background:var(--paper-2)}}
.m{{display:block;margin-top:3px;white-space:nowrap}}
.m i{{display:inline-block;width:7px;height:7px;border-radius:50%;
border:1px solid var(--rule-strong);margin-right:2px}}
.m i.on{{background:var(--gc);border-color:var(--gc)}}
.ask{{background:#fff;border:1px solid var(--rule-strong);border-left:4px solid #8E3B46;
padding:16px 20px;margin-top:10px}}
.ask li{{margin-left:1.2em;font-size:14.5px}}
.sub{{max-width:300px}}
</style></head><body><div class="wrap">

<header>
  <div class="k">掲載内容の確認シート</div>
  <h1>かむ配列</h1>
  <p>新配列カタログへの掲載にあたり、公開ページ（かむ配列一覧表・かむ配列２）の記載から
  こちらで起こした内容です。<b>誤りがないか、ご確認をお願いいたします。</b></p>
</header>

<h2>キーと指の対応</h2>
<div class="src">左右とも、外側から小指・薬指・中指・人差指・親指としています。
親指は最も内側にあるため、1段下げて描いています。刻印は、そのキーを単独で押したときの行・段です。</div>
<div class="fig">{board()}</div>

<h2>行（左手）と段（右手）の組み合わせ</h2>
<div class="src">左手で行、右手で段を同時に押して1文字を入力します。
丸が押すキーで、左5個が左手、右5個が右手です（画面上の並びと同じ順）。</div>
<table>
<thead><tr><th>左手＼右手</th>{head}</tr></thead>
<tbody>
{"".join(rows)}
</tbody>
</table>

<h2>右手だけで入力するもの</h2>
<table class="sub"><tbody>{subs}</tbody></table>

<h2>打鍵の数え方</h2>
<div class="src">当サイトでは、1文字を打つための同時押しを「1アクション」として数えています。
かむ配列は全{len(MAP)}文字で、{breakdown}です。</div>

<div class="ask">
<b>特にご確認いただきたい点</b>
<ul>
<li>指の対応（外側から小指・薬指・中指・人差指・親指）で合っていますか。</li>
<li>わ行の「い段」「え段」は割り当て無しとしていますが、合っていますか。</li>
<li>や行の「い段」を「、」、「え段」を「ん」、わ行の「う段」を「。」としています。</li>
<li>拗音（きゃ・きゅ・きょ など）は、行＋右手の組み合わせで1アクションとしています。</li>
<li>掲載名は「かむ配列」としています。「かむ配列２」として掲載すべきでしょうか。</li>
<li>公開年と現行バージョンが未記入です。差し支えなければお知らせください。</li>
</ul>
</div>

</div></body></html>"""

os.makedirs("/mnt/user-data/outputs", exist_ok=True)
open("/mnt/user-data/outputs/かむ配列_確認シート.html", "w", encoding="utf-8").write(html)
print("確認シートを書き出しました")
