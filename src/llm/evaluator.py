# =============================================================================
# evaluator.py
# =============================================================================
# ベンチマーク結果を評価し，CSV と JSON ファイルとして保存するモジュール．
#
# 主な機能:
#   - 予測値と正解値を照合して正解率（accuracy）を計算する
#   - 結果詳細（チャレンジ，正解，予測値，正解判定）を CSV に保存する
#   - 実験メタデータ（設定値，正解率）を JSON に保存する
# =============================================================================

import os
import csv
import json
import logging
from datetime import datetime
from typing import Optional

import pandas as pd


# =============================================================================
# ログ設定
# =============================================================================
logger = logging.getLogger(__name__)


# =============================================================================
# BenchmarkRecord: 1問分の評価記録を保持するデータクラス（相当）
# =============================================================================

class BenchmarkRecord:
    """
    1つのテスト問題に対する評価記録を保持するクラス．

    Attributes:
        challenge   : チャレンジ（14個の整数リスト）．
        correct_ans : 正解のレスポンス（0〜9の整数）．
        predicted   : LLMの予測値（0〜9の整数，パース失敗時は None）．
        raw_response: APIから返ってきた生のレスポンステキスト．
        is_correct  : 正解判定（True / False / None）．
    """

    def __init__(
        self,
        challenge    : list[int],
        correct_ans  : int,
        predicted    : Optional[int],
        raw_response : str,
    ):
        self.challenge    = challenge
        self.correct_ans  = correct_ans
        self.predicted    = predicted
        self.raw_response = raw_response
        # パース失敗の場合（predicted が None）は不正解扱い
        self.is_correct   = (predicted is not None) and (predicted == correct_ans)

    def to_dict(self) -> dict:
        """
        CSV/JSON への書き出し用に，このレコードを辞書形式に変換する．

        Returns:
            カラム名 → 値 の辞書．
        """
        return {
            "challenge"   : str(self.challenge),   # リストを文字列として保存
            "correct_ans" : self.correct_ans,
            "predicted"   : self.predicted if self.predicted is not None else "PARSE_ERROR",
            "is_correct"  : self.is_correct,
            "raw_response": self.raw_response.replace("\n", "\\n"),  # CSV改行エスケープ
        }


# =============================================================================
# Evaluator クラス
# =============================================================================

class Evaluator:
    """
    ベンチマーク結果の収集・評価・保存を担当するクラス．

    使い方:
        evaluator = Evaluator(output_dir="outputs/llm_benchmark/run_xxx")
        evaluator.add_record(BenchmarkRecord(...))
        ...
        evaluator.save_results(metadata={...})
        accuracy = evaluator.accuracy()
    """

    # CSV ファイルのカラム定義
    CSV_COLUMNS: list[str] = [
        "challenge",
        "correct_ans",
        "predicted",
        "is_correct",
        "raw_response",
    ]

    def __init__(self, output_dir: str):
        """
        Evaluator を初期化し，出力ディレクトリを作成する．

        Args:
            output_dir : 結果ファイル（CSV, JSON）の保存先ディレクトリ의 パス．
        """
        self.output_dir : str = output_dir
        self.records    : list[BenchmarkRecord] = []

        # 出力ディレクトリを作成する（既存でも問題ない）
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info(f"Evaluator 初期化: 出力先={self.output_dir}")

    def add_record(self, record: BenchmarkRecord) -> None:
        """
        1問分の評価記録をリストに追加し，思考ログを即座に保存する．

        Args:
            record : 追加する BenchmarkRecord インスタンス．
        """
        self.records.append(record)
        # 思考ログをリアルタイムで保存（研究の利便性のため）
        self._save_single_record_log(record, len(self.records))

    def _save_single_record_log(self, record: BenchmarkRecord, index: int) -> None:
        """
        特定のレコードの思考ログをファイルとして保存する（内部メソッド）．
        """
        abs_output_dir = os.path.abspath(self.output_dir)
        log_dir = os.path.join(abs_output_dir, "reasoning_logs")
        os.makedirs(log_dir, exist_ok=True)

        status = "correct" if record.is_correct else ("parse_error" if record.predicted is None else "wrong")
        filename = f"case_{index:03d}_{status}.md"
        filepath = os.path.join(log_dir, filename)

        content = [
            f"# Test Case {index:03d}",
            f"- **Result**: {status.upper()}",
            f"- **Challenge**: `{record.challenge}`",
            f"- **Correct Answer**: `{record.correct_ans}`",
            f"- **Predicted**: `{record.predicted if record.predicted is not None else 'N/A'}`",
            "\n---",
            "\n## Raw LLM Response\n",
            record.raw_response
        ]

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(content))

    def accuracy(self) -> float:
        """
        これまでに追加されたレコードの正解率を計算して返す．

        Returns:
            正解率（0.0〜1.0 の float）．レコードが0件の場合は 0.0 を返す．
        """
        if not self.records:
            return 0.0
        correct_count = sum(1 for r in self.records if r.is_correct)
        return correct_count / len(self.records)

    def parse_error_count(self) -> int:
        """
        パースエラー（LLMが有効な数字を返せなかった件数）を返す．

        Returns:
            パースエラーの件数（int）．
        """
        return sum(1 for r in self.records if r.predicted is None)

    def save_results(self, metadata: dict) -> None:
        """
        ベンチマーク結果を CSV と JSON の2形式で保存する．

        Args:
            metadata : 実験設定や結果サマリーを含む辞書．
                       正解率（accuracy）と件数は自動的に付加される．
        """
        # ---- 正解率と統計情報をメタデータに追加 ----
        total       = len(self.records)
        correct     = sum(1 for r in self.records if r.is_correct)
        parse_errors= self.parse_error_count()

        metadata_with_results = {
            **metadata,
            "total_count"      : total,
            "correct_count"    : correct,
            "parse_error_count": parse_errors,
            "accuracy"         : round(self.accuracy(), 4),
        }

        # ---- CSV 保存 ----
        self._save_csv()

        # ---- JSON 保存 ----
        self._save_json(metadata_with_results)

        # ---- コンソールへのサマリー出力 ----
        print("\n" + "=" * 60)
        print("【ベンチマーク結果サマリー】")
        print(f"  テスト件数       : {total}")
        print(f"  正解数           : {correct}")
        print(f"  パースエラー数   : {parse_errors}")
        print(f"  正解率 (Accuracy): {self.accuracy():.2%}")
        print(f"  結果保存先       : {self.output_dir}")
        print("=" * 60 + "\n")

    def _save_csv(self) -> None:
        """
        全レコードを CSV ファイルに書き出す（内部メソッド）．
        出力先: {output_dir}/results.csv
        """
        csv_path = os.path.join(self.output_dir, "results.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.CSV_COLUMNS)
            writer.writeheader()
            for record in self.records:
                writer.writerow(record.to_dict())
        logger.info(f"CSV 保存完了: {csv_path}")

    def _save_json(self, metadata: dict) -> None:
        """
        実験メタデータ（設定と結果サマリー）を JSON ファイルに保存する（内部メソッド）．
        出力先: {output_dir}/metadata.json
        """
        json_path = os.path.join(self.output_dir, "metadata.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        logger.info(f"JSON 保存完了: {json_path}")


# =============================================================================
# ヘルパー関数: 出力ディレクトリ名の生成
# =============================================================================

def make_output_dir(base_dir: str, generator_name: str, model_name: str, paradigm: str = "pure") -> str:
    """
    モデル名・ジェネレータ名・手法（paradigm）ごとに階層化された実験出力ディレクトリのパスを生成する．

    構造: {base_dir}/{model_name}/{generator_name}/{paradigm}/run_{timestamp}
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # モデル名からファイルシステムに不適切な文字を除去
    safe_model_name = model_name.replace(":", "_").replace("/", "_")
    
    # 階層構造を構築
    path = os.path.join(base_dir, safe_model_name, generator_name, paradigm, f"run_{timestamp}")
    return path
