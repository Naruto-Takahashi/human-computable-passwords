# 実験の棚卸し（どのパラメータで走らせたか）

`experiments/inventory.py` により自動生成（2026-09-20 13:54:34）．
一次データ: `results/inventory.csv`（学習 run 87 本）

**この表は「学習 run」が1行**．学習条件（件数・エポック・lr）と検証損失が見える．まだ評価していない run も載る．
評価そのものを一覧したいなら [summary_llm.md](summary_llm.md)（`make summarize`）を見ること（プロンプティング評価も含む，評価1件が1行）．

「離陸」は検証損失が 0.15 を下回った最初のエポック．`-` は最後まで下回らなかったこと（＝学習が始まっていないこと）を表す．詳しくは [docs/measurement_audit.md](../docs/measurement_audit.md)．

**この表は道具であって，読み物ではない．**「いま何が走っているか」と「直前に何が出たか」だけを詳細に出し，残りは要約に畳む．過去の結果を実験単位で追うなら [docs/experiment_index.md](../docs/experiment_index.md)，指標そのものの分布を見るなら `make corpus` を使うこと．

## いま動いている実験

### 実験9 段階3: 陽性対照・再現・項数の天井

| アルゴリズム | 鍵 | データ | 学習件数 | エポック | 評価件数 | 正解率 | 最終val損失 | 離陸ep | run |
|---|---|---|---|---|---|---|---|---|---|
| table_add4_k4 | 35 | 0 | 1000 | 20 | - | 未評価 | - | - | `run_20260920_125032` |

## 決着済みの実験（要約）

`--all` を付けると全 run の明細が出る。

| 実験 | run数 | アルゴリズム | 正解率の幅 |
|---|---|---|---|
| 実験9 段階2: 静的で位置6（交絡の切り分け） | 1 | table_add6_k4 | 10.6% 〜 10.6% |
| 実験9 段階1: 最小課題（鍵4マス） | 2 | narrowptr_k4_m1, narrowptr_k4_m2 | 100.0% 〜 100.0% |
| 実験8b 段階1: 参照範囲ラダー（予算を外す） | 2 | narrowptr_k10_m1, narrowptr_k10_m2 | 9.2% 〜 98.6% |
| 実験8a: 学習予算の探り | 4 | func_22_k10, table_add3_k10 | 11.4% 〜 100.0% |
| 実験7: seed ばらつきの検証 | 4 | table_add3_k10 | 98.2% 〜 100.0% |
| 実験6: 鍵の交絡 | 8 | func_22_k10, table_add3_k10 | 10.2% 〜 99.8% |
| 実験5b: 静的端点の検証 | 3 | table_add3_k10 | 10.6% 〜 99.6% |
| 実験5: 参照範囲ラダー（narrowptr） | 8 | narrowptr_k10_m1, narrowptr_k10_m2, narrowptr_k10_m3, narrowptr_k10_m5 | 9.0% 〜 19.8% |
| 実験4: 学習量スイープ | 2 | func_22_k10 | 12.2% 〜 12.6% |
| 実験3: 構造ラダー（dualptr / recptr） | 6 | dualptr_k10, func_22_k10, recptr_k10 | 10.4% 〜 20.0% |
| 実験2: 深さラダー（pointer_chain） | 8 | pointer_chain_k10_d1, pointer_chain_k10_d2, pointer_chain_k10_d3 | 24.2% 〜 44.0% |
| 7月: 難易度ラダーの探索（記憶・合成・動的参照） | 38 | func_22, lookup_k10, lookup_k26, lookup_k4 他10種 | 6.5% 〜 100.0% |

