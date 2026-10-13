r"""鍵の「1変数信号」$I_1$ を学習なしで厳密に計算する．

$f_{k_1,k_2}$ では，チャレンジが一様なので各位置の数字 $D_i=\sigma(x_i)$ は鍵の数字
分布 $p$ に i.i.d. に従い，$z$ は $x_i$ に $D_i$ を通してしか依存しない．したがって
$I(z; x_i) = I(z; D_i)$ は $p$ だけから，$\mathbb{Z}_{10}$ 上の畳み込みで厳密に書ける．

- 加算項の位置: $I = H(p^{*(k_2+1)}) - H(p^{*k_2})$
- 参照先の位置 $i \in \lbrace 0..9\rbrace$: $j=i$ となる確率 $q_i$（$q=p^{*k_1}$）との混合
- ポインタ項の位置: **厳密に 0**（参照先の数字は $j$ によらず $p$ に従うため）

$I_1$ はこれを全位置で足したもの（bit）．実験C2・C2.1 で，基準線を統制しても
離陸率を予測し，$k_2 \ge 2$ ではエントロピーより強かった（docs/experiment_index.md）．
モンテカルロ（200万件）との一致を確認済み．
"""
import numpy as np


def _cpow(P, m):
    F = np.fft.fft(P, axis=-1) ** m
    return np.clip(np.real(np.fft.ifft(F, axis=-1)), 0, None)


def _H(Q):
    with np.errstate(divide="ignore", invalid="ignore"):
        L = np.where(Q > 0, np.log2(Q), 0.0)
    return -(Q * L).sum(-1)


def digit_dist(keys):
    """鍵（または鍵の配列）→ 数字分布 (…,10)．"""
    keys = np.atleast_2d(np.asarray(keys))
    counts = np.stack([np.bincount(k, minlength=10) for k in keys])
    return counts / keys.shape[1]


def first_order_signal(P, k1, k2):
    """P: (M,10) 数字分布．戻り値: (I1 [bit], 期待される最頻値基準線 max P(z))．"""
    P = np.atleast_2d(P)
    Pz, r, q = _cpow(P, k2 + 1), _cpow(P, k2), _cpow(P, k1)
    HPz = _H(Pz)
    total = k2 * (HPz - _H(r))
    shifts = np.stack([np.roll(r, d, axis=-1) for d in range(10)], axis=1)
    for i in range(10):
        mix = q[:, i, None, None] * shifts + (1 - q[:, i, None, None]) * Pz[:, None, :]
        total = total + (HPz - (P * _H(mix)).sum(-1))
    return total, Pz.max(-1)
