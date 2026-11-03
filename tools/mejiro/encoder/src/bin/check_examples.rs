//! 詳細ページに載せる運指例（src/data/stroke_examples.json）を、公式エンジンで打ち直して確かめる。
//!   cargo run --release --bin check_examples -- ../../../src/data/stroke_examples.json mejiro
//! ストロークの出力と、JSON に書いた "out" が食い違えば止まる。
use mejiro_engine::{Request, State, translate};

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let text = std::fs::read_to_string(&args[1]).unwrap();
    let id = format!("\"{}\"", args[2]);
    let body = &text[text.find(&id).expect("id が見つかりません")..];
    let mut bad = 0;
    // 依存を増やさないよう、"stroke" と "out" の組だけを素朴に拾う
    for part in body.split("\"stroke\":").skip(1) {
        let stroke = part.split('"').nth(1).unwrap();
        let out = part.split("\"out\":").nth(1).unwrap().split('"').nth(1).unwrap();
        let t = translate(stroke, State::default(), true).expect("ストロークとして読めません");
        let got: String = t.output.text.as_str().chars()
            .map(|c| match c { '?' => '？', '!' => '！', c => c }).collect();
        let ok = t.request == Request::Output && got == out;
        println!("{}  {:<14} {}{}", if ok { "OK" } else { "NG" }, stroke, got,
                 if ok { String::new() } else { format!("（JSONは「{out}」）") });
        if !ok { bad += 1; }
    }
    if bad > 0 { std::process::exit(1); }
}
