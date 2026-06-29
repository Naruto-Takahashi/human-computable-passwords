# Test Case 004
- **Result**: CORRECT
- **Challenge**: `[9, 3, 21, 17, 25, 11, 1, 9, 3, 13, 15, 14, 7, 13]`
- **Correct Answer**: `2`
- **Predicted**: `2`

---

## Raw LLM Response

まず、与えられたデータからパターンを見つけるために、各入力値がどのように処理されるかを理解します。具体的には：

1. 入力のX10, X11, X12, X13に対応するSGM_TABLEのインデックスを使用して、それぞれの計算用数値を取得します。
2. 取得した数値を使って、各項を計算します。具体的には、X10はその数値の4乗に1を掛け、X11は3乗に2を掛け、X12は2乗に3を掛け、X13は1乗に4を掛けています。
3. これらの結果を合計し、10で割った余りを求めます。

この手順に基づいてPython関数を作成します。以下がその実装です：

```python
def predict_z(X):
    SGM_TABLE = [6, 3, 7, 4, 6, 9, 2, 6, 7, 4, 3, 7, 7, 2, 5, 4, 1, 7, 5, 1, 4, 0, 9, 5, 8, 0]
    
    # X10, X11, X12, X13に対応するSGM_TABLEの値を取得
    sgm_x10 = SGM_TABLE[X[10]]
    sgm_x11 = SGM_TABLE[X[11]]
    sgm_x12 = SGM_TABLE[X[12]]
    sgm_x13 = SGM_TABLE[X[13]]

    # 各項を計算
    term_1 = 1 * (sgm_x10 ** 4)
    term_2 = 2 * (sgm_x11 ** 3)
    term_3 = 3 * (sgm_x12 ** 2)
    term_4 = 4 * sgm_x13

    # 合計を計算し、10で割った余りを求める
    total_sum = term_1 + term_2 + term_3 + term_4
    z = total_sum % 10
    
    return z

# 新しい入力に対するZの予測
input_data = [9, 3, 21, 17, 25, 11, 1, 9, 3, 13, 15, 14, 7, 13]
print(predict_z(input_data))
```

この関数は与えられた入力リストからZの値を計算します。上記のコードで新しい入力データに対するZの予測を行います。