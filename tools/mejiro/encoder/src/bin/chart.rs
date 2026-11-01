//! 詳細ページの「基本入力の早見表」用のデータを、本家エンジンで引いて作る。
//!   cargo run --release --bin chart -- "メジロ式 v2.8.3（Plover版）" > ../chart.json
//! 引数はページに出す版の表記（Plover_Mejiro の setup.cfg の version に合わせる）
//! 表の中身を手で書かないので、エンジンの版が上がっても引き直すだけで揃う。
use mejiro_engine::{State, translate};

fn out(raw: &str) -> String {
    translate(raw, State::default(), true).map(|t| t.output.text.as_str().to_string()).unwrap_or_default()
}
fn q(s: &str) -> String { format!("\"{}\"", s.replace('"', "\\\"")) }
fn pairs(list: &[(&str, &str)], f: impl Fn(&str) -> String) -> String {
    let v: Vec<String> = list.iter().map(|(name, keys)|
        format!("{{\"name\":{},\"keys\":{},\"out\":{}}}", q(name), q(keys), q(&f(keys)))).collect();
    format!("[{}]", v.join(","))
}

fn main() {
    let conso = [("あ行", ""), ("か行", "K"), ("さ行", "S"), ("た行", "T"), ("な行", "N"),
        ("は行", "TK"), ("ま行", "SKN"), ("ら行", "ST"), ("わ行", "SK"), ("が行", "KN"),
        ("ざ行", "SN"), ("だ行", "TN"), ("ば行", "TKN"), ("ぱ行", "STK"), ("ふぁ行", "STKN"),
        ("小書き", "STN")];
    let vowel = [("あ段", "A"), ("い段", "I"), ("う段", "U"), ("え段", "IA"), ("お段", "AU"),
        ("や段", "YA"), ("ゆ段", "YU"), ("よ段", "YAU")];
    let diph = [("あい", "Y"), ("えい", "YIA"), ("うい", "IU"), ("よう", "YI"), ("ゆう", "YIU"),
        ("おう", "IAU"), ("うう", "YIAU")];
    let extra = [("ん", "n"), ("つ", "t"), ("く", "k"), ("ち", "nt"), ("き", "nk"), ("っ", "tk"), ("ー", "ntk")];
    let thumbs = [("", "t"), ("", "k"), ("", "tk"), ("", "nt"), ("", "nk"), ("", "ntk")];
    let desu = [("", "-TN"), ("", "-TNn"), ("", "-TNt"), ("", "-TNk"), ("", "-TNtk"), ("", "-TNnt"), ("", "-TNnk"), ("", "-TNntk")];
    let verb = [("", "-*"), ("", "-n*"), ("", "-t*"), ("", "-k*"), ("", "-nt*"), ("", "-tk*"), ("", "-nk*"), ("", "-ntk*")];

    let table: Vec<String> = conso.iter().map(|(_, c)| {
        let row: Vec<String> = vowel.iter().map(|(_, v)| q(&out(&format!("{c}{v}-")))).collect();
        format!("[{}]", row.join(","))
    }).collect();

    let version = std::env::args().nth(1).unwrap_or_default();
    println!("{{\"version\":{},\"conso\":{},\"vowel\":{},\"table\":[{}],\"diph\":{},\"extra\":{},\
\"particle_left\":{},\"particle_right\":{},\"desu\":{},\"verb\":{},\"example\":{}}}",
        q(&version),
        pairs(&conso, |_| String::new()),
        pairs(&vowel, |_| String::new()),
        table.join(","),
        pairs(&diph, |k| out(&format!("K{k}-"))),
        pairs(&extra, |k| out(&format!("KA{k}-"))),
        pairs(&thumbs, |k| out(&format!("{k}-"))),
        pairs(&thumbs, |k| out(&format!("-{k}"))),
        pairs(&desu, |k| out(k)),
        pairs(&verb, |k| out(k)),
        pairs(&[("", "TAk-SAn"), ("", "KYI-TYIAU"), ("", "SIAU-TN"), ("", "TNIAU-ntk*")], |k| out(k)));
}
