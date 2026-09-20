# -*- coding: utf-8 -*-
"""Googleフォームの回答CSVを、サイトの layouts.csv の形に並べ替える。

    python tools/import_responses.py 回答.csv
        → tools/out/layouts_from_responses.csv を書き出す（既存のCSVは触らない）

    python tools/import_responses.py 回答.csv --merge
        → src/data/layouts.csv に取り込む。フォームから取れない列
          （id / keymap / keymap_sub / figure / anim）は既存の値をそのまま残す。

設問の文言が多少変わっても動くよう、列は見出しの先頭一致で探している。
"""
import argparse, csv, os, re, sys, unicodedata
from datetime import datetime

# ── layouts.csv の列（順序を変えないこと） ────────────────────────────
COLS = ["id", "name", "kana", "genre", "author", "year", "version", "url",
        "resources", "proxy", "consent", "chord", "shift", "os", "software",
        "phys_keys", "thumb", "keyboard", "geometry", "keymap", "keymap_sub",
        "figure", "anim", "q11", "q12", "q13", "q21", "q21c", "q22", "q23",
        "q31", "q32", "q4", "updated"]

# フォームから取れない、手で育てる列。--merge のとき既存値を守る
KEEP = ["id", "keymap", "keymap_sub", "figure", "anim"]

# ── 見出しの探し方（先頭一致。前後の空白は無視） ──────────────────────
FIND = {
    "timestamp": "Timestamp",
    "email":     "Email",
    "agree":     "上記の内容に同意",
    "name":      "配列名",
    "kana":      "配列名の読み仮名",
    "author":    "作者名",
    "url":       "公式サイト",
    "version":   "現行バージョン",
    "year":      "公開年",
    "resources": "練習用の教材",
    "proxy":     "回答者名",
    "consent":   "作者ご本人の了承",
    "genre":     "入力方式",
    "chord":     "同時打鍵",
    "shift":     "シフト方式",
    "os":        "対応OS",
    "software":  "必要ソフト",
    "phys_keys": "必要物理キー数",
    "thumb":     "親指キー",
    "keyboard":  "想定キーボード",
    "q11":       "1-1.",
    "q12":       "1-2.",
    "q13":       "1-3.",
    "q21":       "2-1. あなたの配列は",
    "q21c":      "2-1. ひと言",
    "q22":       "2-2.",
    "q23":       "2-3.",
    "q31":       "3-1.",
    "q32":       "3-2.",
    "q4":        "Q4.",
    "howto":     "配列図の送り方",
    "note":      "その他、ご連絡",
}

GENRE = {"ローマ字系": "romaji", "行段系": "gyodan", "かな系": "kana",
         "漢字直接入力": "kanchoku", "速記系": "sokki"}
GEOMETRY = {"ロウスタッガード": "row", "オーソリニア": "ortho", "カラムスタッガード": "column"}
AIM = ["速度を意識している", "快適さとの両立を考えている", "快適さを重視している"]
LEARN = ["短め", "普通", "長め"]

# ── 読み仮名から id を作る ────────────────────────────────────────
ROMA = {
 "きゃ":"kya","きゅ":"kyu","きょ":"kyo","しゃ":"sha","しゅ":"shu","しょ":"sho",
 "ちゃ":"cha","ちゅ":"chu","ちょ":"cho","にゃ":"nya","にゅ":"nyu","にょ":"nyo",
 "ひゃ":"hya","ひゅ":"hyu","ひょ":"hyo","みゃ":"mya","みゅ":"myu","みょ":"myo",
 "りゃ":"rya","りゅ":"ryu","りょ":"ryo","ぎゃ":"gya","ぎゅ":"gyu","ぎょ":"gyo",
 "じゃ":"ja","じゅ":"ju","じょ":"jo","びゃ":"bya","びゅ":"byu","びょ":"byo",
 "ぴゃ":"pya","ぴゅ":"pyu","ぴょ":"pyo",
 "あ":"a","い":"i","う":"u","え":"e","お":"o",
 "か":"ka","き":"ki","く":"ku","け":"ke","こ":"ko",
 "さ":"sa","し":"shi","す":"su","せ":"se","そ":"so",
 "た":"ta","ち":"chi","つ":"tsu","て":"te","と":"to",
 "な":"na","に":"ni","ぬ":"nu","ね":"ne","の":"no",
 "は":"ha","ひ":"hi","ふ":"fu","へ":"he","ほ":"ho",
 "ま":"ma","み":"mi","む":"mu","め":"me","も":"mo",
 "や":"ya","ゆ":"yu","よ":"yo",
 "ら":"ra","り":"ri","る":"ru","れ":"re","ろ":"ro",
 "わ":"wa","を":"o","ん":"n",
 "が":"ga","ぎ":"gi","ぐ":"gu","げ":"ge","ご":"go",
 "ざ":"za","じ":"ji","ず":"zu","ぜ":"ze","ぞ":"zo",
 "だ":"da","ぢ":"ji","づ":"zu","で":"de","ど":"do",
 "ば":"ba","び":"bi","ぶ":"bu","べ":"be","ぼ":"bo",
 "ぱ":"pa","ぴ":"pi","ぷ":"pu","ぺ":"pe","ぽ":"po",
 "ー":"","ぁ":"a","ぃ":"i","ぅ":"u","ぇ":"e","ぉ":"o",
 "ゃ":"ya","ゅ":"yu","ょ":"yo","っ":"",
}

def to_id(kana, fallback):
    """読み仮名をローマ字にしてURL用の文字列にする。うまくいかなければ連番。"""
    s = unicodedata.normalize("NFKC", kana or "").strip()
    out, i = [], 0
    while i < len(s):
        if s[i] == "っ" and i + 1 < len(s):
            nxt = ROMA.get(s[i+1:i+3]) or ROMA.get(s[i+1], "")
            if nxt:
                out.append(nxt[0]); i += 1; continue
        two = ROMA.get(s[i:i+2])
        if two is not None:
            out.append(two); i += 2; continue
        one = ROMA.get(s[i])
        if one is not None:
            out.append(one); i += 1; continue
        if re.match(r"[0-9a-zA-Z]", s[i]):
            out.append(s[i].lower()); i += 1; continue
        i += 1
    slug = re.sub(r"[^a-z0-9]+", "-", "".join(out)).strip("-")
    return slug or fallback


# ── 値の整え方 ────────────────────────────────────────────────
def clean(v):
    return unicodedata.normalize("NFKC", (v or "")).strip()

def none_to_blank(v):
    return "" if clean(v) in ("なし", "無し", "ない", "-", "―", "none") else clean(v)

def join_multi(v, sep="・"):
    """フォームの複数選択（カンマ区切り）をつなぎ直す"""
    parts = [p.strip() for p in (v or "").split(",") if p.strip()]
    return sep.join(parts)

def keys_label(v):
    """29 → 29キー、「52 キー」→ 52キー"""
    s = clean(v)
    if not s:
        return ""
    m = re.search(r"\d+", s)
    return f"{m.group(0)}キー" if m else s

def resources(v):
    """「名称^URL」の形にする。URLが読み取れなければ空にして警告に回す"""
    s = none_to_blank(v)
    if not s or "^" in s:
        return s
    urls = re.findall(r"https?://\S+", s)
    if not urls:
        return ""
    title = re.sub(r"https?://\S+", "", s).strip(" 　:：-　()（）") or "練習用の教材"
    return f"{title}^{urls[0]}"

def index_of(v, options):
    s = clean(v)
    for i, o in enumerate(options):
        if s.startswith(o[:3]):
            return str(i)
    return ""


# ── 取り込み ──────────────────────────────────────────────────
def find_cols(header):
    idx = {}
    for key, head in FIND.items():
        for i, h in enumerate(header):
            if clean(h).startswith(clean(head)):
                idx.setdefault(key, i)
    # 配列図のアップロード列は見出しが崩れることがあるのでURLで探す
    return idx

def upload_col(header, rows):
    for i in range(len(header)):
        if any("drive.google.com" in (r[i] if i < len(r) else "") for r in rows):
            return i
    return None


def convert(path):
    text = open(path, encoding="utf-8-sig", newline="").read()
    rows = list(csv.reader(text.splitlines()))
    header, body = rows[0], [r for r in rows[1:] if any(c.strip() for c in r)]
    idx = find_cols(header)
    up = upload_col(header, body)
    missing = [k for k in ("name", "kana", "genre") if k not in idx]
    if missing:
        sys.exit(f"必要な列が見つかりません: {missing}")

    def g(r, key):
        i = idx.get(key)
        return clean(r[i]) if i is not None and i < len(r) else ""

    out, warn, files = [], [], []
    seen = {}
    for n, r in enumerate(body, 1):
        name = g(r, "name")
        if not name:
            continue
        if g(r, "agree") and "同意" not in g(r, "agree"):
            warn.append(f"{name}：同意の回答が確認できないため取り込みませんでした")
            continue

        kana = g(r, "kana")
        lid = to_id(kana, f"layout-{n}")
        if lid in seen:
            warn.append(f"{name}：id「{lid}」が{seen[lid]}と重複します。手で変えてください")
        seen[lid] = name

        genres = [GENRE[k] for k in GENRE if k in g(r, "genre")]
        if not genres:
            warn.append(f"{name}：入力方式「{g(r,'genre')}」をジャンルに変換できません")
        elif len(genres) > 1:
            warn.append(f"{name}：入力方式が複数あります（{g(r,'genre')}）。{genres[0]} を採用しました")

        kb = g(r, "keyboard")
        geo = next((v for k, v in GEOMETRY.items() if k in kb), "")
        if not geo and kb:
            warn.append(f"{name}：想定キーボード「{kb}」から並びを判定できません。geometry を手で入れてください")

        if not resources(g(r, "resources")) and none_to_blank(g(r, "resources")):
            warn.append(f"{name}：練習用の教材にURLが無いため空にしました（{g(r,'resources')}）")

        ts = g(r, "timestamp")
        try:
            d = datetime.strptime(ts.split()[0], "%m/%d/%Y")
            updated = f"{d.year}年{d.month}月{d.day}日"
        except Exception:
            updated = datetime.now().strftime("%Y年%-m月%-d日")

        consent = g(r, "consent")
        rec = {
            "id": lid, "name": name, "kana": kana,
            "genre": genres[0] if genres else "",
            "author": g(r, "author"), "year": re.sub(r"\D", "", g(r, "year")),
            "version": none_to_blank(g(r, "version")), "url": none_to_blank(g(r, "url")),
            "resources": resources(g(r, "resources")),
            "proxy": g(r, "proxy"),
            "consent": "" if "該当なし" in consent else consent,
            "chord": g(r, "chord"), "shift": join_multi(g(r, "shift")),
            "os": join_multi(g(r, "os"), " / "), "software": g(r, "software"),
            "phys_keys": keys_label(g(r, "phys_keys")), "thumb": g(r, "thumb"),
            "keyboard": join_multi(kb, " / "), "geometry": geo,
            "keymap": "", "keymap_sub": "", "figure": "", "anim": "",
            "q11": g(r, "q11"), "q12": g(r, "q12"),
            "q13": index_of(g(r, "q13"), AIM),
            "q21": index_of(g(r, "q21"), LEARN), "q21c": g(r, "q21c"),
            "q22": keys_label(g(r, "q22")), "q23": g(r, "q23"),
            "q31": g(r, "q31"), "q32": g(r, "q32"), "q4": g(r, "q4"),
            "updated": updated,
        }
        out.append(rec)

        link = clean(r[up]) if up is not None and up < len(r) else ""
        files.append((name, lid, g(r, "howto"), link))

    return out, warn, files


def merge(existing_path, records):
    """フォームから取れない列（id・配列図・動画）は既存の値を残す"""
    old = {}
    if os.path.exists(existing_path):
        with open(existing_path, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                old[row.get("id", "")] = row
    merged, added, updated = [], 0, 0
    for rec in records:
        prev = old.pop(rec["id"], None)
        if prev:
            for k in KEEP:
                if prev.get(k):
                    rec[k] = prev[k]
            updated += 1
        else:
            added += 1
        merged.append(rec)
    # フォームに現れなかった既存の行は、そのまま残す
    for row in old.values():
        merged.append({c: row.get(c, "") for c in COLS})
    return merged, added, updated


def write(path, records):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for rec in records:
            w.writerow({c: rec.get(c, "") for c in COLS})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("responses", help="Googleフォームの回答CSV")
    ap.add_argument("--merge", action="store_true",
                    help="src/data/layouts.csv に取り込む（既定は別ファイルに出力）")
    ap.add_argument("--target", default="src/data/layouts.csv")
    ap.add_argument("--out", default="tools/out/layouts_from_responses.csv")
    a = ap.parse_args()

    records, warn, files = convert(a.responses)
    print(f"{len(records)}件を読み込みました\n")
    print(f'{"id":<20}{"配列名":<18}{"ジャンル":<10}{"並び":<8}')
    for r in records:
        print(f'{r["id"]:<20}{r["name"]:<18}{r["genre"] or "?":<10}{r["geometry"] or "?":<8}')

    if warn:
        print("\n■ 確認が必要な点")
        for w in warn:
            print("  ・" + w)

    sent = [f for f in files if f[3]]
    if sent:
        print("\n■ アップロードされた配列図（ダウンロードして public/figures/ に置いてください）")
        for name, lid, how, link in sent:
            print(f"  {name}（{lid}）\n    {link}")
    other = [f for f in files if not f[3]]
    if other:
        print("\n■ ファイルが届いていない配列")
        for name, lid, how, _ in other:
            print(f"  {name}（{lid}）… 送り方の回答：{how or '未回答'}")

    if a.merge:
        records, added, updated = merge(a.target, records)
        write(a.target, records)
        print(f"\n{a.target} を更新しました（新規 {added}件 / 更新 {updated}件）")
        print("※ id・keymap・keymap_sub・figure・anim は既存の値を残しています")
    else:
        write(a.out, records)
        print(f"\n{a.out} に書き出しました")
        print("※ 中身を確認して layouts.csv に貼るか、--merge で直接取り込んでください")


if __name__ == "__main__":
    main()
