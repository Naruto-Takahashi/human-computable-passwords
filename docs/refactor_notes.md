# リファクタリングノート（2026-07-12）

研究計画 v2（`plan_v2_draft.md`）への移行に伴い，コードベースの監査と全面リファクタリングを実施した．本ノートは (1) 監査で見つかった研究妥当性に関わる問題，(2) 新アーキテクチャ，(3) 運用手順をまとめる．

---

## 1. 監査結果：研究の意図と実装のずれ

### 重大（実験の妥当性に影響）

1. **鍵復元率（Key Recovery Rate）が未実装だった**
   `plan.md` §4 の主要評価指標だが，旧実装は応答予測の正解率しか測定していなかった．「鍵の逆推定」を主張するための直接証拠が存在しない状態だった．
   → 新タスク `recover_key` として実装（鍵テーブルを丸ごと出力させ，セル一致率・完全一致・held-out精度を測定）．predict と違い1条件1リクエストで済むため，APIコストも約1/50になる．

2. **アルゴリズム定義が4箇所に重複していた**
   計算本体（`core/generator.py`），値つき解説（同 `explain_logic`），ルール説明文（`llm_agent/prompt.py`），教師コード・rationale（`train_finetuning.py`）が独立に手書きされていた．PoT教師データへの鍵リークはこの重複の中で生じた．
   → `hcp/algorithms.py` に単一情報源化．`fn`（計算）と `reference_code`（コード表現）の整合性は `verify_all()` で機械検証できる（`make test`）．

3. **全実験が単一の鍵（seed=42）で行われていた**
   成功「率」や相転移を主張するには複数の鍵・データでの反復が必要だが，鍵とチャレンジが同一シードに束ねられており，独立に振ることができなかった．
   → `key_seed` と `data_seed` を分離．`--key_seeds 0-4` のように複数鍵での反復が1コマンドで書ける．

4. **FT の評価テスト問題が学習データと重複していた（ホールドアウト不成立）**
   旧 `train_finetuning.py` と旧 `run_prompting.py` は同一シードから同一のデータ列を生成するため，評価用テスト問題は FT の学習サンプルとほぼ同一集合だった．つまり従来の FT 評価（5〜20%）は「学習データ上での精度」であり，それでもこの水準だったことになる（モード崩壊の傍証でもある）．
   → 新 `train_finetuning.py` は学習チャレンジを `data_seed + 1,000,000` のシード空間から生成し，評価（素の `data_seed`）と互いに素にした．

5. **Ollama の `num_ctx=4096` 固定**
   N（観察ペア数）を26〜100に増やす相転移スイープでは，プロンプトが警告なしに切り捨てられ実験が無効になるところだった．
   → プロンプト長から必要コンテキストを自動計算（`OllamaClient._auto_num_ctx`）．

6. **プロンプトが保存されていなかった**
   先週の「lora 評価時に stage が 0 に強制リセットされるバグ」は，プロンプトの実物がログに残っていれば即座に発見できた類のもの．
   → 全実験でプロンプトを `prompt.txt` / `prompt_example.txt` として保存．`metrics.json` に git コミットハッシュと全設定を記録．

### 中程度

7. **MockClient が「80%正解」を装っていた**：実際には正解を知らず，実質ランダム（≈10%）だった．→ 疎通確認専用と明記し，正直な仕様に変更．
8. **旧 `core/generator.list_generators()` が空リストを返し，`train_baseline.py`（CNNベースライン）のループが一度も実行されない死にコードだった**．→ `hcp` に委譲するアダプタで修復．
9. **rclone 同期が各実験スクリプト内にハードコード**（ユーザー固有パス込み）．→ `ops/sync_results.sh` + `make sync` に分離．
10. **Stage 3 + rationale の組合せで，開示していない鍵セルの値が解説文に混入し得た**．→ 値つき解説は Stage 1（鍵全開示）のみに制限．

### 旧実装の結果への含意

- 旧 FT 実験（PoT: 見かけ100% / Pure: 5〜20%）は，鍵リーク（PoT）とホールドアウト不成立（全体）により**そのまま論文に使えない**．モード崩壊の解析過程は否定的知見として記述可能．
- 旧プロンプティング実験（stage1 等）は方法自体は有効だが，単一鍵・単一シードのため，本実験では新ハーネスで反復を取り直すべき．

### 旧実験成果物の整理（2026-07-16）

旧パイプラインで学習した FT モデルの重み（`results/finetuned_models/**/adapter/`, `checkpoints/`，計約3.2GB）は，鍵リーク・ホールドアウト不成立により再利用価値がないため削除した．以下は証拠として保全している（Google Drive `gdrive:human-computable-passwords-results` にも削除前の完全なバックアップあり）:

- `results/finetuned_models/**/train_metadata.json`, `summary.json`, `pipeline_*.log`（学習条件・損失曲線の一次資料）
- `results/evals/`（旧評価の生ログ一式．PoT 見かけ100% とモード崩壊の証拠）

---

## 2. 新アーキテクチャ

```
code/
├── hcp/                    # 中核パッケージ（単一情報源）
│   ├── algorithms.py       # Algorithm 定義（計算・ルール文・rationale・参照コード・解説）+ verify_all()
│   ├── dataset.py          # key_seed / data_seed 分離のデータ生成，shot/test の重複排除
│   ├── prompts.py          # Stage 0〜3 × タスク（predict pure/pot, recover_key）のプロンプト構築
│   ├── clients.py          # Gemini / Ollama（num_ctx自動）/ Mock / LoRA
│   ├── executor.py         # 回答パース（JSON/明示回答のみ），鍵テーブル抽出，生成コード実行
│   ├── evaluation.py       # 実験実行・採点・記録（プロンプト保存，決定的出力ディレクトリ）
│   └── solver.py           # 厳密ソルバー（MRV + 単位伝播 DFS）：整合鍵の数え上げ・復元
├── scripts/
│   ├── run_eval.py         # 統一評価ランナー（1条件×複数シード）
│   ├── sweep.py            # N×K×アルゴリズム×シードのスイープ（レジューム対応，--dry_run）
│   ├── info_limit.py       # 情報限界 N*_info の測定（results/theory/）
│   ├── summarize.py        # metrics.json（新）+ metadata.json（旧）の集計 → summary_llm.{md,csv}
│   ├── train_finetuning.py # QLoRA FT（pot教師は鍵リークのため廃止，ホールドアウト修正）
│   └── train_baseline.py 等 # 従来MLベースライン（既存のまま，generator アダプタ経由で復活）
└── legacy/                 # 旧実装（参照用，動作保証なし）
```

### 出力ディレクトリ（決定的・レジューム可能）

```
results/evals/{model}/{algorithm}/{task}/n{N}_stage{S}_k{K}/ks{key_seed}_ds{data_seed}/
├── metrics.json        # 設定・結果・gitコミット（これがあれば完了扱い＝スイープでスキップ）
├── prompt.txt          # recover_key のプロンプト実物（predict は prompt_example.txt）
├── results.csv         # predict の問題別結果
└── responses/          # 生レスポンス（001_CORRECT.md 等）
```

### ソルバーの性能特性（func_22, 26セル）

| 領域 | 挙動 |
|---|---|
| N ≲ 15（情報不足） | 解が爆発 → solution_cap で即打ち切り，下限を報告（秒オーダー） |
| N ≳ 100（制約十分） | 一意性を厳密証明し真の鍵を復元（N=100: 約30秒, N=200: 約20秒） |
| N ≈ 30〜60（遷移域） | 厳密数え上げは重い．node_budget 到達時は下限値として報告 |

遷移域の厳密化が必要になったら，Z3 / OR-Tools CP-SAT の導入（flake.nix への追加）か，線形アルゴリズム（func_13/22/31）に対する mod 10 線形代数（CRT: mod 2 × mod 5）特化ソルバーの実装が次の一手．
なお func_pow は N=100 でも整合鍵が2個残る（x^k mod 10 の縮退による原理的な非一意性）ことが判明した．鍵は一意特定不能だが応答予測には影響しない可能性が高く，考察の材料になる．

---

## 3. 運用（よく使うコマンド）

```bash
make test        # アルゴリズム自己検証 + ソルバー健全性
make smoke       # mock による E2E ドライラン（3タスク）
make summarize   # 集計（results/summary_llm.{md,csv}）
make sync        # Google Drive 同期（実験スクリプトからは分離済み）

# RQ1: Stage 2 の N スイープ（鍵復元，鍵5個で反復）
python3 code/scripts/sweep.py --task recover_key --provider ollama --model qwen2.5:7b \
    --algorithms func_22 --stage 2 --n_shots 10,20,30,40,50,75,100 --key_seeds 0-4

# RQ2: Stage 3 の K スイープ
python3 code/scripts/sweep.py --task recover_key --provider ollama --model qwen2.5:7b \
    --algorithms func_22 --stage 3 --n_shots 30 --k_values 0,6,13,20,26 --key_seeds 0-4

# 情報限界の基準線
python3 code/scripts/info_limit.py --algorithm func_22 --n_shots 5,10,15,20,26,30,40,50 --key_seeds 0-4

# FT（.venv が必要）
.venv/bin/python code/scripts/train_finetuning.py --model Qwen/Qwen2.5-3B-Instruct \
    --algorithm func_22 --paradigm rationale --stage 2 --n_train 200
```

スイープは中断しても同じコマンドで再開できる（完了済み条件は `metrics.json` の有無で自動スキップ）．計画確認は `--dry_run`．
