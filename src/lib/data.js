import raw from '../data/layouts.csv?raw';
import genres from '../data/genres.json';

/** 引用符・改行・BOM を扱う最小のCSVパーサ */
function parseCsv(text) {
  const s = text.replace(/^\uFEFF/, '');
  const rows = [];
  let row = [], cell = '', q = false;
  for (let i = 0; i < s.length; i++) {
    const c = s[i];
    if (q) {
      if (c === '"') { if (s[i + 1] === '"') { cell += '"'; i++; } else q = false; }
      else cell += c;
    } else if (c === '"') q = true;
    else if (c === ',') { row.push(cell); cell = ''; }
    else if (c === '\r') { /* 読み飛ばす */ }
    else if (c === '\n') { row.push(cell); rows.push(row); row = []; cell = ''; }
    else cell += c;
  }
  if (cell !== '' || row.length) { row.push(cell); rows.push(row); }
  const head = rows.shift();
  return rows.filter(r => r.some(v => v !== ''))
             .map(r => Object.fromEntries(head.map((h, i) => [h, (r[i] ?? '').trim()])));
}

function shape(r) {
  return {
    ...r,
    year: r.year ? Number(r.year) : null,
    keymapRows: r.keymap ? r.keymap.split('|') : null,
    keymapSubRows: r.keymap_sub ? r.keymap_sub.split('|') : null,
    resourceList: r.resources
      ? r.resources.split(';').filter(Boolean).map(x => {
          const [title, href] = x.split('^');
          return { title: (title || '').trim(), href: (href || '').trim() };
        })
      : [],
    aimIndex: r.q13 === '' ? null : Number(r.q13),
    learnIndex: r.q21 === '' ? null : Number(r.q21),
  };
}

export const GENRES = genres;
export const LAYOUTS = parseCsv(raw).map(shape);

const collator = new Intl.Collator('ja');

/** ジャンル別・五十音順。掲載順はここだけで決まる */
export function byGenre() {
  return GENRES.map(g => ({
    ...g,
    layouts: LAYOUTS.filter(l => l.genre === g.id).sort((a, b) => collator.compare(a.kana, b.kana)),
  }));
}

export function genreOf(id) {
  return GENRES.find(g => g.id === id) ?? { id, name: id, color: '#5E6167', desc: '' };
}

/** 同じジャンル内の前後（五十音順）。端では null */
export function neighbours(layout) {
  const list = LAYOUTS.filter(l => l.genre === layout.genre)
                      .sort((a, b) => collator.compare(a.kana, b.kana));
  const i = list.findIndex(l => l.id === layout.id);
  return { prev: list[i - 1] ?? null, next: list[i + 1] ?? null };
}

/** 各設問の下に出す出典表記。代理入力なら入力者名を名乗る */
export function attribution(l) {
  return l.proxy
    ? `代理入力者（${l.proxy}）からの申告によります。`
    : '作者ご本人による自己申告です。';
}

/** 本文末尾の注記 */
export function respondentNote(l) {
  return l.proxy
    ? `この配列の情報は代理入力者（${l.proxy}）にご回答いただいたものです。`
    : 'この配列の情報は作者ご本人にご回答いただいたものです。';
}

export const scaleLabels = {
  aim: ['速度を意識している', '快適さとの両立', '快適さを重視している'],
  learn: ['短め', '普通', '長め'],
};
