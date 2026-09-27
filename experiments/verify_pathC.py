"""1.0000 が本物か，独立に確かめる．

疑う点を1つずつ潰す:
  A. 訓練とテストで同じチャレンジが出ていないか（漏洩）
  B. **新しく引いたチャレンジ**（分割とは無関係）で正解できるか
  C. ラベルをシャッフルした対照では床に落ちるか（配管が 1.0 を作っていないか）
  D. 学習した表が本当の鍵 σ と一致するか（攻撃の成否そのもの）
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
REPO = "/home/nalt/ghq/github.com/Naruto-Takahashi/human-computable-passwords"
sys.path.insert(0, os.path.join(REPO, "src"))
import keras
from hcp.algorithms import get_algorithm
from baseline_ml.models import Models

algo = get_algorithm("func_22")
SEED = 20260929
keras.utils.set_random_seed(SEED)
rng = np.random.default_rng(SEED)
key = rng.integers(0, 10, algo.key_size).tolist()
N = algo.challenge_domain()

def draw(n, r):
    ch = r.integers(0, N, (n, 14))
    z = np.array([algo.compute([int(v) for v in c], key) for c in ch])
    return ch, z

x, y = draw(50000, rng)
tr, va = slice(0, 40000), slice(40000, 45000)
xtr, ytr, xva, yva = x[tr], y[tr], x[va], y[va]

# A. 漏洩の確認（別の乱数で引いた検証集合との重複）
rng2 = np.random.default_rng(999_777)
xnew, ynew = draw(10000, rng2)
tr_set = set(map(tuple, xtr))
dup = sum(1 for c in map(tuple, xnew) if c in tr_set)
print(f"A. 新規10,000件のうち訓練集合と重複: {dup} 件")
print(f"   ラベル分布（最頻値の割合）: {np.bincount(ynew, minlength=10).max()/len(ynew):.4f}")

model = Models.embed_transformer(n_images=N, d_model=32, num_layers=2, readout="cls")
to_cat = keras.utils.to_categorical
h = model.fit(xtr, to_cat(ytr, 10), batch_size=64, epochs=int(os.environ.get("EP", 120)),
              validation_data=(xva, to_cat(yva, 10)), verbose=0).history
print(f"B. 訓練最終 {h['accuracy'][-1]:.4f} / 検証最終 {h['val_accuracy'][-1]:.4f}")
acc_new = model.evaluate(xnew, to_cat(ynew, 10), verbose=0)[1]
print(f"B. **新しく引いた10,000件** の正解率: {acc_new:.4f}")

# D. 学習した表が σ と一致するか
#    位置0だけを i に変え，j=0 になるチャレンジを作れば Z = σ(i) + X12 + X13 で，
#    σ(i) の差が Z の差として読める。σ を直接読み出さず，模型の出力から復元する。
#    簡便に: 全マス i について「i を位置0に置いた多数のチャレンジ」の予測平均が
#    σ(i) に沿って回るかを，真の Z との一致率で見る。
probe_rng = np.random.default_rng(4242)
hit = 0; tot = 0
for i in range(N):
    ch = probe_rng.integers(0, N, (200, 14))
    ch[:, 0] = i
    z = np.array([algo.compute([int(v) for v in c], key) for c in ch])
    pred = model.predict(ch, verbose=0).argmax(1)
    hit += int((pred == z).sum()); tot += len(z)
print(f"D. 各マスを位置0に固定した 200×{N} 件での正解率: {hit/tot:.4f}")

# C. ラベルを潰した対照
keras.utils.set_random_seed(SEED)
m2 = Models.embed_transformer(n_images=N, d_model=32, num_layers=2, readout="cls")
yshuf = np.random.default_rng(1).permutation(ytr)
h2 = m2.fit(xtr, to_cat(yshuf, 10), batch_size=64, epochs=30,
            validation_data=(xva, to_cat(yva, 10)), verbose=0).history
print(f"C. ラベルシャッフル対照: 訓練 {h2['accuracy'][-1]:.4f} / 検証 {h2['val_accuracy'][-1]:.4f}")
