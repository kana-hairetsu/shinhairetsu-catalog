/** 物理キーボードの並び。数字段11キー＋3段 */
const PHYS = ['1234567890-', 'qwertyuiop', 'asdfghjkl;', 'zxcvbnm,./'].map(r => [...r]);

/** ロウスタッガード：段ごとに横へずらす量（キーピッチ＝1） */
const ROW_X = [0, 0.38, 0.66, 1.04];

/** カラムスタッガード：列ごとに縦へずらす量。中指列が最も高く、小指列が低い */
const COL_Y = [0.16, 0, -0.20, -0.06, 0.10, 0.10, -0.06, -0.20, 0, 0.16, 0.24];

const SPACE = { id: 'space', x: 3.6, y: 4, w: 5 };

export const KEY_UNIT = 29.4;
export const KEY_SIZE = 27;
export const GEOMETRIES = ['row', 'ortho', 'column'];

/**
 * 物理キーの位置だけを決める。配列図・ヒートマップ・動画はすべてこれを使うので、
 * geometry を変えれば3つとも同じ並びになる。
 *   row    … ロウスタッガード（一般的なJIS/USキーボード）
 *   ortho  … オーソリニア（格子状）
 *   column … カラムスタッガード（列ごとに上下がずれる）
 */
export function placeKeys(geometry = 'row', { space = false } = {}) {
  const rowX = geometry === 'row' ? ROW_X : [0, 0, 0, 0];
  const colY = geometry === 'column' ? COL_Y : null;
  const keys = [];
  PHYS.forEach((row, r) => row.forEach((id, c) => {
    keys.push({
      id, row: r, col: c, w: 1,
      x: +(rowX[r] + c).toFixed(3),
      y: +(r + (colY ? (colY[c] ?? 0) : 0)).toFixed(3),
    });
  }));
  if (space) keys.push({ ...SPACE, row: 4, col: null });
  // 中指列が上にはみ出すので、上端が0になるよう全体を下げる
  const minY = Math.min(...keys.map(k => k.y));
  if (minY < 0) keys.forEach(k => { k.y = +(k.y - minY).toFixed(3); });
  return keys;
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
  return placeKeys(geometry, { space: withSpace }).map(k => {
    if (k.id === 'space') return { ...k, l: rows[4].trim(), s: '', dim: 0 };
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

/** 印字の対応表（物理キー -> 文字）から組み立てる。ヒートマップと動画で使う */
export function boardFromLabels(labels, subs = {}, geometry = 'row') {
  return placeKeys(geometry, { space: true }).map(k => ({
    ...k,
    l: labels[k.id] ?? '',
    s: subs[k.id] ?? '',
    dim: k.row === 0 && /[0-9]/.test(labels[k.id] ?? '') ? 1 : 0,
  }));
}

export function boardSize(keys) {
  return {
    w: Math.max(...keys.map(k => k.x + k.w)) * KEY_UNIT + 2,
    h: (Math.max(...keys.map(k => k.y)) + 1) * KEY_UNIT + 2,
  };
}
