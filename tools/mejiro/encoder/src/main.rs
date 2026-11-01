//! お題文を、メジロ式の打鍵列（ストローク列）に直す。
//! 変換規則はすべて作者の公式エンジン Mejiro_Engine に任せ、ここでは
//! 「どのストロークを押せばお題文の続きが出るか」を探すだけ。
//!
//!   cargo run --release -- <お題文.txt> > 出力.json
//!
//! 探し方
//!   1. 全ストローク（左11キー×右11キー×*、必要なら#）を引いて、出力→ストロークの索引を作る
//!   2. お題文の先頭から、エンジンの状態（直前の母音・助詞を決める文脈・保留中の「っ」）ごとに
//!      最少のストローク数を求める（動的計画法）。候補は必ず「その時点の状態」で変換し直して確かめる
//!   3. 同じストローク数なら、です・動詞（* や右手の子音だけで活用させる入力）を使わない方を選ぶ。
//!      文法を見ずに選ぶと、ただの名詞を動詞の活用として打つような不自然な列になるため。
//!      です・動詞はストロークが減るところでだけ使う。次に * と # の少ないもの、
//!      最後に押すキーの少ないものを選ぶ
//!   4. 選んだ列を最初から打ち直して、お題文と一致することを確かめる
//! 変換は実機と同じく、コマンド辞書（カーソル移動など）も有効にして行う。
//! 文字以外の操作（カーソル移動・BSなど）を含むストロークは使わない。
//!
//! 標準出力に JSON：{"chars":字数,"strokes":[{"c":文字位置,"s":"TAk-SAn","o":"たくさん"},…],"skipped":[…]}
use mejiro_engine::{Context, Request, State, translate};
use std::collections::HashMap;

const HAND: [char; 11] = ['S', 'T', 'K', 'N', 'Y', 'I', 'A', 'U', 'n', 't', 'k'];
/// どの配列でも打鍵に含めない文字
const SKIP: [char; 1] = ['―'];

fn hand_str(mask: u32) -> String {
    HAND.iter().enumerate().filter(|(i, _)| mask >> i & 1 == 1).map(|(_, c)| *c).collect()
}
fn raw(l: u32, r: u32, star: bool) -> String {
    let mut s = hand_str(l);
    s.push('-');
    s.push_str(&hand_str(r));
    if star { s.push('*'); }
    s
}
/// カタカナ・半角の？！は、お題文の表記にそろえて比べる（IMEに渡す前の読みとして同じ）
fn norm(s: &str) -> String {
    s.chars().map(|c| match c {
        '?' => '？', '!' => '！',
        c if ('\u{30A1}'..='\u{30F4}').contains(&c) => char::from_u32(c as u32 - 0x60).unwrap(),
        c => c }).collect()
}
fn out_of(raw: &str, st: State) -> Option<(String, State)> {
    let t = translate(raw, st, true).ok()?;
    if t.request != Request::Output || !t.output.operations().is_empty() { return None; }
    let s = t.output.text.as_str();
    if s.is_empty() { return None; }
    Some((s.to_string(), t.next))
}
fn key_of(st: State) -> (u8, &'static str, bool, u8) {
    (st.context as u8, st.last_vowel(), st.pending_sokuon(), st.mode as u8)
}
/// 同じストローク数のときの副次コスト（小さいほど良い）
fn sub_cost(rw: &str) -> (u32, u32, u32) {
    let (_, r) = rw.trim_start_matches('#').split_once('-').unwrap();
    let r = r.trim_end_matches('*');
    let star = rw.ends_with('*');
    // 右手が子音だけ（です・五段動詞の活用）
    let right_cons_only = r.chars().any(|c| "STKN".contains(c)) && !r.chars().any(|c| "YIAU".contains(c));
    let special = if star || right_cons_only { 1 } else { 0 };
    let deco = rw.chars().filter(|c| matches!(c, '*' | '#')).count() as u32;
    let keys = rw.chars().filter(|c| *c != '-').count() as u32;
    (special, deco, keys)
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let text: Vec<char> = std::fs::read_to_string(&args[1]).unwrap()
        .chars().filter(|c| !matches!(c, '\n' | '\r' | '\u{3000}' | '\u{FEFF}')).collect();
    let joined: String = norm(&text.iter().collect::<String>());

    // 1. 索引
    let mut index: HashMap<String, Vec<String>> = HashMap::new();
    let mut add = |o: &str, r: &str| {
        let v = index.entry(norm(o)).or_default();
        if !v.iter().any(|x| x == r) { v.push(r.to_string()); }
    };
    let ctxs = ["unknown","nominalizable","incomplete","attributive_na","question_predicate",
                "noun","place","indefinite_noun","question_particle"];
    for l in 0u32..2048 {
        for r in 0u32..2048 {
            for star in [false, true] {
                let rw = raw(l, r, star);
                if let Some((o, _)) = out_of(&rw, State::default()) {
                    if o.chars().count() <= 24 && joined.contains(&norm(&o)) {
                        add(&o, &rw);
                        // # はそのストロークの出力を2回くり返す。お題文に重ねた形があるときだけ候補に入れる
                        let twice = format!("{o}{o}");
                        if joined.contains(&norm(&twice)) {
                            let h = format!("#{rw}");
                            if let Some((o2, _)) = out_of(&h, State::default()) { add(&o2, &h); }
                        }
                    }
                }
                // 親指だけの助詞は、直前の語で出方が変わるので全文脈で引く
                if l & 0xFF == 0 && r & 0xFF == 0 {
                    for c in ctxs {
                        let mut st = State::default();
                        st.context = Context::from_name(c).unwrap();
                        if let Some((o, _)) = out_of(&rw, st) { add(&o, &rw); }
                    }
                }
            }
        }
    }
    let maxlen = index.keys().map(|k| k.chars().count()).max().unwrap();
    eprintln!("索引: {} 通りの出力", index.len());

    // 2. 動的計画法。best[pos] = 状態 → (コスト, ひとつ前の位置, ひとつ前の状態, ストローク, 出力)
    type Cost = (u32, u32, u32, u32);
    type K = (u8, &'static str, bool, u8);
    #[derive(Clone)]
    struct Node { cost: Cost, st: State, prev: Option<(usize, K)>, rw: String, o: String }
    let n = text.len();
    let mut best: Vec<HashMap<K, Node>> = vec![HashMap::new(); n + 1];
    best[0].insert(key_of(State::default()), Node {
        cost: (0, 0, 0, 0), st: State::default(), prev: None, rw: String::new(), o: String::new() });
    let tnorm: Vec<char> = joined.chars().collect();
    for p in 0..n {
        let here: Vec<(K, Node)> = best[p].iter().map(|(k, v)| (*k, v.clone())).collect();
        if here.is_empty() { continue; }
        let relax = |q: usize, node: Node, best: &mut Vec<HashMap<K, Node>>| {
            let k = key_of(node.st);
            match best[q].get(&k) {
                Some(old) if old.cost <= node.cost => {}
                _ => { best[q].insert(k, node); }
            }
        };
        for (k, node) in here {
            // 打たない文字（ダッシュ）は読み飛ばす
            if SKIP.contains(&text[p]) {
                relax(p + 1, Node { cost: node.cost, st: node.st, prev: Some((p, k)),
                                    rw: String::new(), o: String::new() }, &mut best);
                continue;
            }
            for len in 1..=maxlen.min(n - p) {
                let want: String = tnorm[p..p + len].iter().collect();
                let Some(list) = index.get(&want) else { continue };
                for rw in list {
                    let Some((o, next)) = out_of(rw, node.st) else { continue };
                    if norm(&o) != want { continue; }
                    let (pl, de, ke) = sub_cost(rw);
                    let c = node.cost;
                    relax(p + len, Node { cost: (c.0 + 1, c.1 + pl, c.2 + de, c.3 + ke), st: next,
                                          prev: Some((p, k)), rw: rw.clone(), o }, &mut best);
                }
            }
        }
    }
    // 打ち終わりで「っ」が保留のまま残る列は使わない
    let (_, last) = best[n].iter().filter(|(_, v)| !v.st.pending_sokuon())
        .min_by_key(|(_, v)| v.cost).expect("お題文を最後まで打てませんでした");
    let mut strokes = Vec::new();
    let mut skipped = Vec::new();
    let (mut pos, mut node) = (n, last.clone());
    while let Some((pp, pk)) = node.prev {
        if node.rw.is_empty() { skipped.push((pp, text[pp])); } else { strokes.push((pp, node.rw.clone(), node.o.clone())); }
        node = best[pp][&pk].clone();
        pos = pp;
    }
    let _ = pos;
    strokes.reverse();
    skipped.reverse();

    // 3. 検算：選んだ列を先頭から打ち直して、お題文（読み飛ばした文字を除く）と一致するか
    let mut st = State::default();
    let mut got = String::new();
    for (_, rw, _) in &strokes {
        let (o, next) = out_of(rw, st).expect("検算で出力なし");
        got.push_str(&norm(&o)); st = next;
    }
    let want: String = tnorm.iter().enumerate()
        .filter(|(i, _)| !skipped.iter().any(|(j, _)| j == i)).map(|(_, c)| *c).collect();
    assert_eq!(got, want, "検算が一致しません");
    assert!(!st.pending_sokuon());

    let esc = |s: &str| s.replace('\\', "\\\\").replace('"', "\\\"");
    let body: Vec<String> = strokes.iter().map(|(c, s, o)|
        format!("{{\"c\":{},\"s\":\"{}\",\"o\":\"{}\"}}", c, esc(s), esc(o))).collect();
    let sk: Vec<String> = skipped.iter().map(|(i, c)| format!("[{},\"{}\"]", i, c)).collect();
    println!("{{\"chars\":{},\"strokes\":[{}],\"skipped\":[{}]}}", text.len(), body.join(","), sk.join(","));
    eprintln!("{}字 → {}ストローク（読み飛ばし {}字）", text.len(), strokes.len(), skipped.len());
}
