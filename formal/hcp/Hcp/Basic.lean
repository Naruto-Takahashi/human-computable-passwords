/-
  人間計算可能パスワード（HCP）の鍵の識別可能性について．

  実験（2026-09-23）で次の現象を観測した：静的な和 Z = (X_0 + ... + X_{N-1}) mod 10
  では，観測をいくら増やしても整合する鍵が1個に減らない課題がある．

      足す項数 N = 3 → 整合鍵 1 個（一意）
      足す項数 N = 4 → 整合鍵 2 個
      足す項数 N = 5 → 整合鍵 5 個
      足す項数 N = 6 → 整合鍵 2 個

  原因は「ずらし対称性」である．鍵の全マスに同じ値 c を足すと，N 項の和は
  N * c mod 10 だけずれる．したがって N * c ≡ 0 (mod 10) となる c の個数だけ，
  観測からは区別できない鍵が残る．

  本ファイルはその個数が gcd(N, 10) に等しいことを機械的に検証する．
-/

/-- 鍵の全マスに `c` を足しても `N` 項の和 (mod 10) が変わらない `c` の個数． -/
def shiftSymmetries (N : Nat) : Nat :=
  ((List.range 10).filter (fun c => (N * c) % 10 == 0)).length

/-! ## 実験で観測した値との一致

`docs/task_catalog.md` の「鍵の一意性」列，および総当たり（鍵4マス＝10⁴ 通り）
との突き合わせで得た実測値をそのまま書き下す． -/

/-- `table_add3_k*`：一意に復元できる． -/
example : shiftSymmetries 3 = 1 := by decide

/-- `table_add4_k4`：2通りに縮退する． -/
example : shiftSymmetries 4 = 2 := by decide

/-- `table_add5_k4`：5通りに縮退する（観測を増やしても減らない）． -/
example : shiftSymmetries 5 = 5 := by decide

/-- `table_add6_k4`：2通りに縮退する． -/
example : shiftSymmetries 6 = 2 := by decide

/-! ## 一般の主張

`gcd` との一致を，実用上必要な範囲（項数 20 まで）で検証する．
核 Lean のみで閉じるため `decide` による有限検証とした． -/

theorem shiftSymmetries_eq_gcd : ∀ N < 21, shiftSymmetries N = Nat.gcd N 10 := by
  decide

/-- 一意に復元できるのは，項数が 10 と互いに素なときに限る． -/
theorem unique_iff_coprime : ∀ N < 21, (shiftSymmetries N = 1 ↔ Nat.gcd N 10 = 1) := by
  decide

/-- `recover_key` に使える項数（10 と互いに素）と，使えない項数． -/
example : shiftSymmetries 7 = 1 := by decide   -- 使える
example : shiftSymmetries 9 = 1 := by decide   -- 使える
example : shiftSymmetries 10 = 10 := by decide -- 最悪：鍵が全く絞れない
