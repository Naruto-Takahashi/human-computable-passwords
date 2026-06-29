# Test Case 003
- **Result**: CORRECT
- **Challenge**: `[6, 18, 21, 1, 9, 12, 24, 20, 5, 11, 11, 19, 10, 25]`
- **Correct Answer**: `0`
- **Predicted**: `0`

---

## Raw LLM Response

観察したデータから、出力 \( Z \) の計算方法は以下の手順で行われていることがわかります：

1. **テーブル値の参照**：各入力 \( X_i \) に対して、SGM_TABLE[X_i] の値を取得します。
2. **各項の計算**：各テーブル値を以下のように計算します：
   - 第1項: \( 1 \times SGM_TABLE[X_{10}]^4 \)
   - 第2項: \( 2 \times SGM_TABLE[X_{11}]^3 \)
   - 第3項: \( 3 \times SGM_TABLE[X_{12}]^2 \)
   - 第4項: \( 4 \times SGM_TABLE[X_{13}]^1 \)

3. **合計の計算**：上記の各項を足し合わせます。
4. **余りの算出**：合計を10で割った余りを求めます。

これらの手順に基づいて、Python 関数 `predict_z(X)` を定義します。

```python
def predict_z(X):
    # SGM_TABLE の定義
    SGM_TABLE = [6, 3, 7, 4, 6, 9, 2, 6, 7, 4, 3, 7, 7, 2, 5, 4, 1, 7, 5, 1, 4, 0, 9, 5, 8, 0]
    
    # 各項の計算
    term_1 = SGM_TABLE[X[10]] ** 4
    term_2 = 2 * (SGM_TABLE[X[11]]) ** 3
    term_3 = 3 * (SGM_TABLE[X[12]]) ** 2
    term_4 = 4 * SGM_TABLE[X[13]]
    
    # 合計の計算
    total = term_1 + term_2 + term_3 + term_4
    
    # 余りの算出
    result = total % 10
    
    return result

# テスト用の入力データ
X_test = [6, 18, 21, 1, 9, 12, 24, 20, 5, 11, 11, 19, 10, 25]
print(predict_z(X_test))
```

この関数は与えられた入力リスト \( X \) から出力を計算し、その結果を返します。テスト用の入力データに対して実行すると、期待される出力が得られるはずです。