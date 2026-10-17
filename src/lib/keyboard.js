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
/* シフトと親指キーは文字段の下に1段まとめる。
   文字段の並びを崩さないため、また使わない配列では段ごと省くため。 */
const EXTRA_KEYS = [
  { id: 'lshift',   row: 4, x: 0.00,  w: 2.2, cap: 'Shift' },
  { id: 'lthumb',   row: 4, x: 2.40,  w: 1.4, cap: '親指左' },
  { id: 'muhenkan', row: 4, x: 3.80,  w: 1.4, cap: '無変換' },
  { id: 'space',    row: 4, x: 5.20,  w: 2.6, cap: '空白' },
  { id: 'henkan',   row: 4, x: 7.80,  w: 1.4, cap: '変換' },
  { id: 'kana',     row: 4, x: 9.20,  w: 1.4, cap: 'かな' },
  { id: 'rthumb',   row: 4, x: 10.60, w: 1.4, cap: '親指右' },
  { id: 'rshift',   row: 4, x: 12.00, w: 2.2, cap: 'Shift' },
];

/** カラムスタッガード：列ごとに縦へずらす量。中指列が最も高く、小指列が低い */
const COL_Y = [0.16, 0, -0.20, -0.06, 0.10, 0.10, -0.06, -0.20, 0, 0.16, 0.24, 0.30];

/**
 * グリップ（左右5キーずつの専用機）。左は外側から、右は内側から並べるので、
 * 画面上は左右とも「外側＝小指、内側＝親指」になる。
 * 親指のキーは最も内側にあるため、1段下げて描く。
 */
const GRIP_KEYS = [
  { id: 'l1', x: 0.0, y: 0, finger: '小指',   hand: 'L' },
  { id: 'l2', x: 1.0, y: 0, finger: '薬指',   hand: 'L' },
  { id: 'l3', x: 2.0, y: 0, finger: '中指',   hand: 'L' },
  { id: 'l4', x: 3.0, y: 0, finger: '人差指', hand: 'L' },
  { id: 'l5', x: 4.0, y: 1, finger: '親指',   hand: 'L' },
  { id: 'r1', x: 5.4, y: 1, finger: '親指',   hand: 'R' },
  { id: 'r2', x: 6.4, y: 0, finger: '人差指', hand: 'R' },
  { id: 'r3', x: 7.4, y: 0, finger: '中指',   hand: 'R' },
  { id: 'r4', x: 8.4, y: 0, finger: '薬指',   hand: 'R' },
  { id: 'r5', x: 9.4, y: 0, finger: '小指',   hand: 'R' },
];

export const KEY_UNIT = 29.4;
export const KEY_SIZE = 27;
export const GEOMETRIES = ['row', 'ortho', 'column', 'grip'];
export const GRIP_IDS = GRIP_KEYS.map(k => k.id);
export const GRIP_HAND = Object.fromEntries(GRIP_KEYS.map(k => [k.id, k.hand]));
export const GRIP_THUMBS = GRIP_KEYS.filter(k => k.finger === '親指').map(k => k.id);
export const DEFAULT_CAPS = {
  // 数字段は物理キーの刻印をそのまま薄く出す。割り当てがあればそちらが優先される
  ...Object.fromEntries(FINGER[0].keys.map(id => [id, id])),
  ...Object.fromEntries(EXTRA_KEYS.map(k => [k.id, k.cap])),
};

/**
 * 物理キーの位置を決める。配列図・ヒートマップ・動画がすべてこれを使うので、
 * geometry を変えれば3つとも同じ並びになる。
 *   row    … ロウスタッガード（一般的なJIS/USキーボード）
 *   ortho  … オーソリニア（格子状）
 *   column … カラムスタッガード（列ごとに上下がずれる）
 *
 * 指キー（文字キー）は常に全部描く。使用頻度や割り当ての有無では省かない。
 * extras … 追加で描くキーID（lshift / henkan など）。使う配列でだけ現れる
 */
export function placeKeys(geometry = 'row', { extras = [] } = {}) {
  if (geometry === 'grip') {
    return GRIP_KEYS.map((k, i) => ({
      id: k.id, row: k.y, col: i, w: 1, x: k.x, y: k.y,
      finger: k.finger, hand: k.hand,
    }));
  }
  const stagger = geometry === 'row';
  const colY = geometry === 'column' ? COL_Y : null;
  const want = new Set(extras);
  const keys = [];

  FINGER.forEach(({ row, x: off, keys: ids }) => {
    ids.forEach((id, c) => {
      keys.push({
        id, row, col: c, w: 1,
        x: +((stagger ? off : 0) + c).toFixed(3),
        y: +(row + (colY ? (colY[c] ?? 0) : 0)).toFixed(3),
      });
    });
  });

  EXTRA_KEYS.forEach(k => {
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
  EXTRA_KEYS.forEach(k => {
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

  // グリップは2段だけ。1段目に左手5キー、2段目に右手5キーの印字を書く
  if (geometry === 'grip') {
    const left = [...(rows[0] ?? '')];
    const right = [...(rows[1] ?? '')];
    const sub = { L: [...((subRows && subRows[0]) ?? '')], R: [...((subRows && subRows[1]) ?? '')] };
    return placeKeys('grip').map(k => {
      const n = Number(k.id[1]) - 1;
      const l = (k.hand === 'L' ? left : right)[n] ?? '';
      const s = sub[k.hand][n] ?? '';
      return { ...k, l: l === '　' ? '' : l, s: s && s !== '　' ? s : '', dim: 0 };
    });
  }

  const withSpace = rows.length >= 5 && rows[4].trim() !== '';
  return placeKeys(geometry, { extras: withSpace ? ['space'] : [] }).map(k => {
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
  const extras = extrasFrom(labels, subs, usedMap);
  return placeKeys(geometry, { extras }).map(k => {
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
