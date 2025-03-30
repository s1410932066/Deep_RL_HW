以下是一份更新後的完整報告範本，內容涵蓋格子世界環境的生成、使用者互動設定（包括起點、終點、以及障礙物限制最多 n-2 個），以及價值迭代與最佳策略推導的部分。請參考後依需求做進一步調整。

---

# 強化深度學習 HW1 \& HW2 報告

## 一、前言

本專案旨在利用 Flask 框架建構一個動態產生的格子世界 (Grid World) 環境，並實現以下兩大功能：

1. **HW1**：
    - 根據使用者輸入的網格大小 (n×n，n 介於 5～9) 生成網格。
    - 使用者可互動設定：
        - **起點**：第一次點擊白色格子，標示為綠色。
        - **終點**：第二次點擊白色格子，標示為紅色。
        - **障礙物**：後續點擊白色格子，標示為灰色，但限制障礙物數量最多為 n-2，防止過多障礙影響後續演算法運算。
    - 顯示隨機產生的策略矩陣與價值矩陣，以供後續強化學習算法整合。
2. **HW2**：
    - 進一步利用價值迭代 (Value Iteration) 算法，計算每個狀態的最佳價值函數 $V(s)$ 與對應最佳策略。
    - 根據最佳策略，從起點沿著最佳路徑搜尋至終點，並在前端高亮顯示該路徑，直觀展示最優走法。

---

## 二、系統架構與專案結構

整個系統以 Python 的 Flask 作為後端框架，前端則採用 HTML、CSS 搭配少量 JavaScript 進行網頁渲染與互動。專案主要結構如下：

```
.
├── app.py              ← Flask 主程式，負責網格初始化、使用者點擊事件處理與價值迭代
└── templates
    ├── index.html      ← 首頁：提供使用者輸入網格大小 n (5～9)
    ├── grid.html       ← 顯示 n×n 網格，支援點擊設定起點、終點及障礙（並限制障礙數量至 n-2）
    └── policy.html     ← 顯示策略矩陣與價值矩陣，並以顏色高亮展示最佳路徑
```

在 `app.py` 中，除了基本的網格生成與互動設定外，我們新增了價值迭代與最佳策略推導的功能；並在互動設定部分加入了障礙物數量限制的邏輯，防止使用者放置超過 n-2 個障礙。

---

## 三、程式設計與實作細節

### 3.1 格子世界生成與互動設定 (HW1)

1. **網格初始化**
使用者在 `index.html` 輸入網格大小 n（介於 5 至 9），後端根據該數字生成一個二維陣列，每個格子以字典儲存狀態（預設為白色）及唯一編號。此資料利用 session 傳遞，供不同路由間共用。
2. **互動式點擊設定**
在 `grid.html` 中，每個格子皆以 `<button>` 呈現。當使用者點擊白色格子時，依照以下邏輯更新狀態：
    - **第一個點擊**：若尚未設定起點，該格變為綠色（起點）。
    - **第二個點擊**：若起點已設定但終點尚未設定，該格變為紅色（終點）。
    - **隨後點擊**：若起點與終點皆已設定，則嘗試將該白色格子設為障礙物（灰色）。

**障礙物限制機制：**
    - 為避免使用者放置超過 n-2 個障礙物，在點擊白色格子準備設為障礙前，後端會先統計目前灰色格子的數量。
    - 若障礙物數量未達 n-2，才允許更新顏色為灰色；反之則不做變更（或可提示使用者）。
3. **隨機策略與價值展示 (HW1 範例版)**
在 `/policy` 路由中，根據當前網格狀態隨機生成策略矩陣（箭頭符號表示，障礙物標示為 "X"）與隨機產生的價值矩陣（非障礙顯示隨機浮點數，障礙顯示「障礙」），作為後續演算法展示前的初步示範。

### 3.2 價值迭代與最佳策略推導 (HW2)

1. **價值迭代算法**
    - 為所有非障礙狀態初始化 $V(s) = 0$。
    - 定義四個動作（上、下、左、右），若移動到邊界或障礙物則狀態保持不變。
    - 每走一步設定懲罰 -1，若移動到終點則獎勵為 0，並將該狀態視為終止狀態。
    - 透過迭代更新 $V(s)$ 直到所有狀態變化值小於預設閾值 $\theta$。
2. **最佳政策與路徑搜尋**
    - 根據收斂後的 $V(s)$，對每個狀態選取使 $Q(s,a)$ 最大的動作作為最佳策略。
    - 從起點（綠色格子）出發，依據最佳策略步步搜尋至終點（紅色格子），並將沿途經過的狀態存入最佳路徑列表。
    - 前端在展示策略與價值矩陣時，對屬於最佳路徑的格子加上特定 CSS 樣式以高亮顯示。

---

## 四、主要程式碼範例

### 4.1 app.py 核心部分

```python
from flask import Flask, render_template, request, session, redirect, url_for
import random

app = Flask(__name__)
app.secret_key = 'your_secret_key'

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        n = request.form.get('n', 5)
        try:
            n = int(n)
        except ValueError:
            n = 5
        n = max(5, min(9, n))
        grid = []
        cell_index = 1
        for i in range(n):
            row = []
            for j in range(n):
                row.append({
                    'color': 'white',
                    'number': cell_index
                })
                cell_index += 1
            grid.append(row)
        session['n'] = n
        session['grid'] = grid
        session['start_set'] = False
        session['end_set'] = False
        return redirect(url_for('grid'))
    return render_template('index.html')

@app.route('/grid', methods=['GET', 'POST'])
def grid():
    if 'grid' not in session:
        return redirect(url_for('index'))
    grid = session['grid']
    n = session['n']
    start_set = session['start_set']
    end_set = session['end_set']
    if request.method == 'POST':
        i = int(request.form.get('i'))
        j = int(request.form.get('j'))
        if grid[i][j]['color'] == 'white':
            if not start_set:
                grid[i][j]['color'] = 'green'  # 設為起點
                start_set = True
            elif not end_set:
                grid[i][j]['color'] = 'red'    # 設為終點
                end_set = True
            else:
                # 檢查目前障礙物數量，限制最多 n-2 個
                obstacle_count = sum(cell['color'] == 'gray' for row in grid for cell in row)
                if obstacle_count < (n - 2):
                    grid[i][j]['color'] = 'gray'  # 設為障礙物
                else:
                    # 可選擇回傳提示訊息，目前不做狀態更新
                    pass
        session['grid'] = grid
        session['start_set'] = start_set
        session['end_set'] = end_set
    return render_template('grid.html', grid=grid, n=n)

def value_iteration(grid, gamma=0.9, theta=1e-4):
    n = len(grid)
    V = {}
    for i in range(n):
        for j in range(n):
            if grid[i][j]['color'] != 'gray':
                V[(i, j)] = 0.0
    # 找出終點 (紅色格子)
    goal = None
    for i in range(n):
        for j in range(n):
            if grid[i][j]['color'] == 'red':
                goal = (i, j)
                break
        if goal:
            break
    actions = {'up': (-1, 0), 'down': (1, 0), 'left': (0, -1), 'right': (0, 1)}
    while True:
        delta = 0
        for s in V.keys():
            if s == goal:
                continue
            best_value = float('-inf')
            for a, (di, dj) in actions.items():
                i, j = s
                ni, nj = i + di, j + dj
                if not (0 <= ni < n and 0 <= nj < n) or grid[ni][nj]['color'] == 'gray':
                    next_s = s
                else:
                    next_s = (ni, nj)
                r = 0 if next_s == goal else -1
                q_value = r + gamma * V[next_s]
                best_value = max(best_value, q_value)
            delta = max(delta, abs(best_value - V[s]))
            V[s] = best_value
        if delta < theta:
            break
    policy = {}
    for s in V.keys():
        if s == goal:
            policy[s] = None
            continue
        best_value = float('-inf')
        best_action = None
        for a, (di, dj) in actions.items():
            i, j = s
            ni, nj = i + di, j + dj
            if not (0 <= ni < n and 0 <= nj < n) or grid[ni][nj]['color'] == 'gray':
                next_s = s
            else:
                next_s = (ni, nj)
            r = 0 if next_s == goal else -1
            q_value = r + gamma * V[next_s]
            if q_value > best_value:
                best_value = q_value
                best_action = a
        policy[s] = best_action
    return V, policy

def find_path(grid, policy):
    n = len(grid)
    start, end = None, None
    for i in range(n):
        for j in range(n):
            if grid[i][j]['color'] == 'green':
                start = (i, j)
            elif grid[i][j]['color'] == 'red':
                end = (i, j)
    if not start or not end:
        return []
    best_path = []
    current = start
    visited = set()
    while True:
        best_path.append(current)
        visited.add(current)
        if current == end:
            break
        action = policy.get(current)
        if not action:
            break
        di, dj = {'up': (-1, 0), 'down': (1, 0), 'left': (0, -1), 'right': (0, 1)}[action]
        next_s = (current[0] + di, current[1] + dj)
        if not (0 <= next_s[0] < n and 0 <= next_s[1] < n) or grid[next_s[0]][next_s[1]]['color'] == 'gray':
            break
        if next_s in visited:
            break
        current = next_s
    return best_path

@app.route('/policy')
def policy():
    if 'grid' not in session:
        return redirect(url_for('index'))
    n = session['n']
    grid = session['grid']
    V, optimal_policy = value_iteration(grid)
    best_path = find_path(grid, optimal_policy)
    arrow_map = {'up': '↑', 'down': '↓', 'left': '←', 'right': '→', None: ''}
    policy_matrix = []
    value_matrix = []
    for i in range(n):
        p_row = []
        v_row = []
        for j in range(n):
            if grid[i][j]['color'] == 'gray':
                p_row.append('X')
                v_row.append('障礙')
            else:
                action = optimal_policy.get((i, j), None)
                p_row.append(arrow_map.get(action, ''))
                v_row.append(round(V.get((i, j), 0), 2))
        policy_matrix.append(p_row)
        value_matrix.append(v_row)
    return render_template('policy.html',
                           n=n,
                           policy_matrix=policy_matrix,
                           value_matrix=value_matrix,
                           best_path=best_path)

if __name__ == '__main__':
    app.run(debug=True)
```


### 4.2 HTML 模板

#### index.html

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>網格生成器</title>
</head>
<body>
    <h1>產生 n x n 網格</h1>
    <form method="POST">
        <label>請輸入 5 至 9 之間的數字：</label>
        <input type="number" name="n" min="5" max="9" required>
        <button type="submit">生成網格</button>
    </form>
</body>
</html>
```


#### grid.html

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>網格世界</title>
    <style>
        .grid {
            display: grid;
            grid-template-columns: repeat({{n}}, 60px);
            grid-gap: 5px;
        }
        .cell {
            width: 60px;
            height: 60px;
            text-align: center;
            line-height: 60px;
            border: 1px solid #ccc;
            cursor: pointer;
            font-weight: bold;
        }
        .white { background-color: white; }
        .green { background-color: green; color: white; }
        .red   { background-color: red; color: white; }
        .gray  { background-color: gray; color: white; }
    </style>
</head>
<body>
    <h1>{{n}} x {{n}} 網格</h1>
    <p>
      點擊規則：<br>
      1. 第一次點擊白色格子 → 起點 (綠色)<br>
      2. 第二次點擊白色格子 → 終點 (紅色)<br>
      3. 後續點擊白色格子 → 障礙物 (灰色)（最多 {{ n - 2 }} 個）
    </p>
    <div class="grid">
        {% for i in range(n) %}
            {% for j in range(n) %}
                <form method="POST" style="margin:0; padding:0;">
                    <input type="hidden" name="i" value="{{ i }}">
                    <input type="hidden" name="j" value="{{ j }}">
                    <button type="submit" class="cell {{ grid[i][j].color }}">
                        {{ grid[i][j].number }}
                    </button>
                </form>
            {% endfor %}
        {% endfor %}
    </div>
    <p>
      <a href="{{ url_for('policy') }}">前往顯示策略與價值</a>
    </p>
</body>
</html>
```


#### policy.html

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>策略與價值</title>
    <style>
        .matrix-container {
            display: flex;
            gap: 50px;
        }
        .matrix {
            display: grid;
            grid-template-columns: repeat({{n}}, 60px);
            grid-gap: 5px;
            margin-top: 20px;
        }
        .cell {
            width: 60px;
            height: 60px;
            text-align: center;
            line-height: 60px;
            border: 1px solid #ccc;
            font-weight: bold;
        }
        /* 高亮最佳路徑 */
        .best-path {
            background-color: #6AC259;
        }
    </style>
</head>
<body>
    <h1>策略與價值</h1>
    <div class="matrix-container">
        <div>
            <h2>策略矩陣</h2>
            <div class="matrix">
            {% for i in range(n) %}
                {% for j in range(n) %}
                    {% set in_best = (i, j) in best_path %}
                    <div class="cell {% if in_best %}best-path{% endif %}">
                        {{ policy_matrix[i][j] }}
                    </div>
                {% endfor %}
            {% endfor %}
            </div>
        </div>
        <div>
            <h2>價值矩陣</h2>
            <div class="matrix">
            {% for i in range(n) %}
                {% for j in range(n) %}
                    {% set in_best = (i, j) in best_path %}
                    <div class="cell {% if in_best %}best-path{% endif %}">
                        {{ value_matrix[i][j] }}
                    </div>
                {% endfor %}
            {% endfor %}
            </div>
        </div>
    </div>
    <p><a href="{{ url_for('grid') }}">返回網格</a></p>
</body>
</html>
```

---

## 五、使用流程與測試結果

1. **啟動應用程式**
在終端機中執行 `python app.py`，Flask 伺服器將在預設埠 5000 運行。
2. **生成網格**
開啟瀏覽器，進入 [http://127.0.0.1:5000/](http://127.0.0.1:5000/)，輸入網格大小（例如 5），點選「生成網格」後，系統會建立一個 5×5 的網格，每個格子顯示唯一編號。
![original image](https://cdn.mathpix.com/snip/images/ve_FuzsRrvgENDGOMwRDEJ-s2zNQNkaRN012gX8z6ow.original.fullsize.png)
3. **互動設定**
    - 點擊第一個白色格子，該格變為綠色（起點）。
    - 點擊第二個白色格子，該格變為紅色（終點）。
    - 之後點擊其他白色格子，僅允許設定障礙物（灰色）至多 3 個（5-2 = 3）；超過數量限制後，其他點擊將不再變更狀態。
![original image](https://cdn.mathpix.com/snip/images/piKfZe_IRq1e3GJ0IAcHItv337U9O6Zp8tHZ1BU3ulQ.original.fullsize.png)
4. **策略與價值展示**
點選連結進入策略頁面後，系統會根據目前網格狀態：
    - 使用價值迭代算法計算每個狀態的最佳價值與策略。
    - 將最佳策略以箭頭顯示在策略矩陣中，並將狀態價值以浮點數顯示在價值矩陣中。
    - 根據從起點到終點的最佳路徑，高亮該路徑上的格子（例如背景變綠），以直觀展示最佳走法。

![original image](https://cdn.mathpix.com/snip/images/y6zs0b7r4bmj0Nu0j4ynvLTtihvYmiM-hmWTu5M8Za0.original.fullsize.png)

## 六、實際操作影片
[錄製_2025_03_30_15_16_56_241.mp4](..%2F..%2F..%2FDocuments%2FoCam%2F%E9%8C%84%E8%A3%BD_2025_03_30_15_16_56_241.mp4)