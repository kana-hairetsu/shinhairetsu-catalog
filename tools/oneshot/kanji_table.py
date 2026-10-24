# 一打漢直の対応表。キー位置は QWERTY 名（q..p, a..;, z../）
L_ROWS = ["qwert", "asdfg", "zxcvb"]
R_ROWS = ["yuiop", "hjkl;", "nm,./"]
def grid(rows, s):
    s = s.split()
    out = {}
    for r, row in enumerate(rows):
        for c, k in enumerate(row):
            ch = s[r][c]
            if ch not in '_×':
                out[ch] = k
    return out
TABLE = {}
def add(kind, rows, s, desc):
    for ch, k in grid(rows, s).items():
        assert ch not in TABLE, ch
        TABLE[ch] = (kind, k, desc)
# 主漢字面 単打（変換＋キー）
add('tan', L_ROWS, "気的出知字 全見取感書 方人話_自", '単打')
add('tan', R_ROWS, "漢覚良意入 来会言打部 思_考分風", '単打')
# 同手2打：変換+V のあと左手キー／変換+M のあと右手キー
add('pre_v', L_ROWS, "個決定赤青 手系事黒暗 本発場×回", '同手')
add('pre_m', R_ROWS, "銀金色動用 明白行使運 々×何悪体", '同手')
# 逆手2打：変換+M のあと左手キー／変換+V のあと右手キー
add('pre_m', L_ROWS, "聞効点面時 線計撮間描 初早離始速", '逆手')
add('pre_v', R_ROWS, "対起解味変 大合者詰深 多慣難笑所", '逆手')
# 機能漢字面 同時1（中段3キー＋逆手）
add('mid_r', L_ROWS, "外昇上前内 終左以右今 次降下後先", '同時1')   # J K L を押しながら左手キー
add('mid_l', R_ROWS, "数789年 歳456月 0123日", '同時1')           # S D F を押しながら右手キー
# 機能漢字面 同時2（下段3キー＋逆手）
add('bot_r', L_ROWS, "進遠止同高 停小中最異 退近心違低", '同時2')   # M , . を押しながら左手キー
add('bot_l', R_ROWS, "百七八九億 十四五六万 〇一二三千", '同時2')   # X C V を押しながら右手キー
HOLD = {'mid_r': ['j', 'k', 'l'], 'mid_l': ['s', 'd', 'f'],
        'bot_r': ['m', ',', '.'], 'bot_l': ['x', 'c', 'v']}
if __name__ == '__main__':
    print(len(TABLE))
