//! お題文を、メジロ式の打鍵列（ストローク列）に直す。
//! 変換規則はすべて本家エンジン（mejiro-engine）に任せ、ここでは
//! 「どのストロークを押せばお題文の続きが出るか」を探すだけ。
//!
//!   cargo run --release -- <お題文.txt> > 出力.json
//!
//! 探し方：先頭から順に、その位置で押せるストロークのうち「次のストロークまで含めて
//! 最も先へ進めるもの」を選ぶ（同じなら押すキーの少ないもの）。
//! エンジンの状態（直前の母音・助詞の判定に使う文脈）も1打ずつ引き継ぐ。
//! 最後に、選んだ列を最初から打ち直してお題文と一致することを確かめる。
//!
//! 標準出力に JSON：{"strokes":[{"c":文字位置,"s":"TAk-SAn","o":"たくさん"},…],"skipped":[…]}
use mejiro_engine::{Context, Request, State, translate};
use std::collections::HashMap;

const HAND: [char; 11] = ['S', 'T', 'K', 'N', 'Y', 'I', 'A', 'U', 'n', 't', 'k'];

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
/// カタカナはひらがなに寄せて比べる（IMEに渡す前の読みとして同じ）
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

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let text: Vec<char> = std::fs::read_to_string(&args[1]).unwrap()
        .chars().filter(|c| !matches!(c, '\n' | '\r' | '\u{3000}' | '\u{FEFF}')).collect();

    // 1. 全ストローク（左11キー×右11キー×*）を既定の状態で引いて、出力→ストロークの索引を作る
    let mut index: HashMap<String, Vec<(String, u32)>> = HashMap::new();
    let mut add = |o: String, r: String, keys: u32| {
        let v = index.entry(norm(&o)).or_default();
        if !v.iter().any(|(x, _)| *x == r) { v.push((r, keys)); }
    };
    let ctxs = ["unknown","nominalizable","incomplete","attributive_na","question_predicate",
                "noun","place","indefinite_noun","question_particle"];
    for l in 0u32..2048 {
        for r in 0u32..2048 {
            for star in [false, true] {
                let rw = raw(l, r, star);
                let keys = l.count_ones() + r.count_ones() + star as u32;
                if let Some((o, _)) = out_of(&rw, State::default()) {
                    if o.chars().count() <= 24 { add(o, rw.clone(), keys); }
                }
                // 親指だけの助詞は、直前の語で出方が変わるので全文脈で引く
                if l & 0xFF == 0 && r & 0xFF == 0 {
                    for c in ctxs {
                        let mut st = State::default();
                        st.context = Context::from_name(c).unwrap();
                        if let Some((o, _)) = out_of(&rw, st) { add(o, rw.clone(), keys); }
                    }
                }
            }
        }
    }
    let maxlen = index.keys().map(|k| k.chars().count()).max().unwrap();
    eprintln!("索引: {} 通りの出力", index.len());

    // 2. 先頭から、2ストローク先まで見て最も長く進めるものを選ぶ
    let cands = |p: usize, st: State| -> Vec<(String, usize, u32, String, State)> {
        let mut v = Vec::new();
        for len in 1..=maxlen.min(text.len() - p) {
            let want: String = text[p..p + len].iter().collect();
            if let Some(list) = index.get(&want) {
                for (rw, keys) in list {
                    if let Some((o, next)) = out_of(rw, st) {
                        if norm(&o) == want { v.push((rw.clone(), len, *keys, o, next)); }
                    }
                }
            }
        }
        v
    };
    let mut st = State::default();
    let mut p = 0;
    let mut strokes = Vec::new();
    let mut skipped = Vec::new();
    while p < text.len() {
        let c1 = cands(p, st);
        if c1.is_empty() { skipped.push((p, text[p])); p += 1; continue; }
        let mut best: Option<(usize, i64, String, usize, String, State)> = None;
        for (rw, len, keys, o, next) in c1 {
            let ahead = if p + len < text.len() {
                cands(p + len, next).iter().map(|x| x.1).max().unwrap_or(0) } else { 0 };
            let score = (len + ahead, -(keys as i64));
            let better = match &best { None => true,
                Some(b) => (score.0, score.1, len) > (b.0, b.1, b.3) };
            if better { best = Some((score.0, score.1, rw, len, o, next)); }
        }
        let (_, _, rw, len, o, next) = best.unwrap();
        strokes.push((p, rw, o));
        st = next;
        p += len;
    }

    // 3. 検算：選んだ列を先頭から打ち直して、お題文（読み飛ばした文字を除く）と一致するか
    let mut st = State::default();
    let mut got = String::new();
    for (_, rw, _) in &strokes {
        let (o, next) = out_of(rw, st).expect("検算で出力なし");
        got.push_str(&norm(&o)); st = next;
    }
    let want: String = text.iter().enumerate()
        .filter(|(i, _)| !skipped.iter().any(|(j, _)| j == i)).map(|(_, c)| *c).collect();
    assert_eq!(got, want, "検算が一致しません");

    let esc = |s: &str| s.replace('\\', "\\\\").replace('"', "\\\"");
    let body: Vec<String> = strokes.iter().map(|(c, s, o)|
        format!("{{\"c\":{},\"s\":\"{}\",\"o\":\"{}\"}}", c, esc(s), esc(o))).collect();
    let sk: Vec<String> = skipped.iter().map(|(i, c)| format!("[{},\"{}\"]", i, c)).collect();
    println!("{{\"chars\":{},\"strokes\":[{}],\"skipped\":[{}]}}", text.len(), body.join(","), sk.join(","));
    eprintln!("{}字 → {}ストローク（読み飛ばし {}字）", text.len(), strokes.len(), skipped.len());
}
