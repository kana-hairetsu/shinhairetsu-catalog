/**
 * 物理キーボードの定義。typing-distance の「使えるキーID」に対応する。
 *   指キー   1234567890-= qwertyuiop[] asdfghjkl;' zxcvbnm,./
 *   親指キー henkan / kana / lthumb / muhenkan / rthumb / space
 *   シフト   lshift / rshift
 */
const FINGER = [
  { row: 0, x: 0.00, keys: [...'1234567890-='] },
  { row: 1, x: 0.38, keys: [...'qwertyuiop[]'] },
  { row: 2, x: 0.66, keys: [...'asdfghjkl;\''] },
  { row: 3, x: 1.04, keys: [...'zxcvbnm,./'] },
];

/** 既定の刻印。配列側で割り当てがなければ、これを薄い色で出す */
const MOD_KEYS = [
  { id: 'lshift', row: 3, x: -1.16, w: 2.2, cap: 'Shift' },
  { id: 'rshift', row: 3, x: 11.04, w: 2.2, cap: 'Shift' },
];
const THUMB_KEYS = [
  { id: 'lthumb',   row: 4, x: 1.40, w: 1.4, cap: '親指左' },
  { id: 'muhenkan', row: 4, x: 2.80, w: 1.4, cap: '無変換' },
  { id: 'space',    row: 4, x: 4.20, w: 3.0, cap: '空白' },
  { id: 'henkan',   row: 4, x: 7.20, w: 1.4, cap: '変換' },
  { id: 'kana',     row: 4, x: 8.60, w: 1.4, cap: 'かな' },
  { id: 'rthumb',   row: 4, x: 10.00, w: 1.4, cap: '親指右' },
];

/** カラムスタッガード：列ごとに縦へずらす量。中指列が最も高く、小指列が低い */
const COL_Y = [0.16, 0, -0.20, -0.06, 0.10, 0.10, -0.06, -0.20, 0, 0.16, 0.24, 0.30];

export const KEY_UNIT = 29.4;
export const KEY_SIZE = 27;
export const GEOMETRIES = ['row', 'ortho', 'column'];
export const DEFAULT_CAPS = Object.fromEntries(
  [...MOD_KEYS, ...THUMB_KEYS].map(k => [k.id, k.cap]));

/**
 * 物理キーの位置を決める。配列図・ヒートマップ・動画がすべてこれを使うので、
 * geometry を変えれば3つとも同じ並びになる。
 *   row    … ロウスタッガード（一般的なJIS/USキーボード）
 *   ortho  … オーソリニア（格子状）
 *   column … カラムスタッガード（列ごとに上下がずれる）
 *
 * cols   … 指キーの段ごとの列数。省略時は 11/10/10/10（従来と同じ見え方）
 * extras … 追加で描くキーID（lshift / henkan など）
 */
export function placeKeys(geometry = 'row', { cols = [11, 10, 10, 10], extras = [] } = {}) {
  const stagger = geometry === 'row';
  const colY = geometry === 'column' ? COL_Y : null;
  const want = new Set(extras);
  const keys = [];

  FINGER.forEach(({ row, x: off, keys: ids }) => {
    ids.slice(0, cols[row] ?? ids.length).forEach((id, c) => {
      keys.push({
        id, row, col: c, w: 1,
        x: +((stagger ? off : 0) + c).toFixed(3),
        y: +(row + (colY ? (colY[c] ?? 0) : 0)).toFixed(3),
      });
    });
  });

  [...MOD_KEYS, ...THUMB_KEYS].forEach(k => {
    if (!want.has(k.id)) return;
    keys.push({ id: k.id, row: k.row, col: null, w: k.w, x: k.x, y: k.row });
  });

  // 中指列やShiftが枠の外へ出るので、左上が 0 になるよう全体をずらす
  const minX = Math.min(...keys.map(k => k.x));
  const minY = Math.min(...keys.map(k => k.y));
  keys.forEach(k => {
    k.x = +(k.x - minX).toFixed(3);
    k.y = +(k.y - minY).toFixed(3);
  });
  return keys;
}

/** その配列が実際に使うキーだけを、追加分として拾う */
function extrasFrom(...maps) {
  const ids = new Set();
  [...MOD_KEYS, ...THUMB_KEYS].forEach(k => {
    if (maps.some(m => m && m[k.id] !== undefined)) ids.add(k.id);
  });
  return [...ids];
}

/** 指キーの段ごとの列数を、実際に使う範囲まで伸ばす */
function colsFrom(...maps) {
  return FINGER.map(({ row, keys: ids }) => {
    let last = [11, 10, 10, 10][row] - 1;
    ids.forEach((id, c) => {
      if (maps.some(m => m && m[id] !== undefined && m[id] !== '')) last = Math.max(last, c);
    });
    return last + 1;
  });
}

/**
 * 段ごとの印字文字列から配列図を組み立てる。
 *   rows    … 段ごとの印字（例 "1234567890/"）。段ごとに長さが違ってよい。
 *             5段目を書くとスペースキーの印字になる
 *   subRows … 裏レイヤー（シフト同時押し）の印字。省略可
 */
export function buildBoard({ rows, subRows = null, geometry = 'row' }) {
  if (!rows || !rows.length) return null;
  const withSpace = rows.length >= 5 && rows[4].trim() !== '';
  const cols = FINGER.map(({ row }) => Math.max([11, 10, 10, 10][row], [...(rows[row] ?? '')].length));
  return placeKeys(geometry, { cols, extras: withSpace ? ['space'] : [] }).map(k => {
    if (k.col === null) return { ...k, l: rows[4].trim(), s: '', dim: 0 };
    const l = [...(rows[k.row] ?? '')][k.col] ?? '';
    const s = [...((subRows && subRows[k.row]) ?? '')][k.col] ?? '';
    return {
      ...k,
      l: l === '　' ? '' : l,
      s: s && s !== '　' ? s : '',
      dim: k.row === 0 && /[0-9]/.test(l) ? 1 : 0,
    };
  });
}

/**
 * 印字の対応表（物理キーID -> 文字）から組み立てる。ヒートマップと動画で使う。
 * used には打鍵のあったキーIDを渡すと、割り当てが無くても盤面に含める。
 */
export function boardFromLabels(labels, subs = {}, geometry = 'row', used = null) {
  const usedMap = used ? Object.fromEntries([...used].map(id => [id, ''])) : null;
  const cols = colsFrom(labels, subs, usedMap);
  const extras = extrasFrom(labels, subs, usedMap);
  return placeKeys(geometry, { cols, extras }).map(k => {
    const assigned = labels[k.id];
    const l = assigned ?? DEFAULT_CAPS[k.id] ?? '';
    return {
      ...k,
      l,
      s: subs[k.id] ?? '',
      // 割り当てのないキー（数字や既定の刻印）は薄く出す
      dim: assigned === undefined ? 1 : (k.row === 0 && /[0-9]/.test(l) ? 1 : 0),
    };
  });
}

export function boardSize(keys) {
  return {
    w: Math.max(...keys.map(k => k.x + k.w)) * KEY_UNIT + 2,
    h: (Math.max(...keys.map(k => k.y)) + 1) * KEY_UNIT + 2,
  };
}
