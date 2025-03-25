# app.py
from flask import Flask, render_template, request, session, redirect, url_for
import random

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # session 需要的密鑰


@app.route('/', methods=['GET', 'POST'])
def index():
    """
    首頁：讓使用者輸入 n (5 <= n <= 9)，按下按鈕後導向 /grid。
    """
    if request.method == 'POST':
        n = request.form.get('n', 5)
        try:
            n = int(n)
        except ValueError:
            n = 5
        # 限制 n 在 [5, 9]
        n = max(5, min(9, n))

        # 初始化網格
        # 每個 cell 用字典儲存：{'color': 'white', 'number': X}
        # number 用來顯示該格的編號 (1~n*n)
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

        # 將網格與狀態存到 session
        session['n'] = n
        session['grid'] = grid
        # start_set, end_set 用來記錄「起點、終點」是否已經被設定
        session['start_set'] = False
        session['end_set'] = False

        return redirect(url_for('grid'))

    return render_template('index.html')


@app.route('/grid', methods=['GET', 'POST'])
def grid():
    """
    顯示 n x n 網格，可點擊改變顏色：
    1. 第一次點擊某個白色格子 -> 綠色(起點)
    2. 第二次點擊某個白色格子 -> 紅色(終點)
    3. 之後點擊白色格子 -> 灰色(障礙)
    已經被指定顏色的格子再次點擊，不做任何變更。
    """
    if 'grid' not in session:
        return redirect(url_for('index'))

    grid = session['grid']
    n = session['n']
    start_set = session['start_set']
    end_set = session['end_set']

    if request.method == 'POST':
        i = int(request.form.get('i'))
        j = int(request.form.get('j'))

        # 只有「白色」格子才需要處理
        if grid[i][j]['color'] == 'white':
            if not start_set:
                grid[i][j]['color'] = 'green'  # 起點
                start_set = True
            elif not end_set:
                grid[i][j]['color'] = 'red'  # 終點
                end_set = True
            else:
                grid[i][j]['color'] = 'gray'  # 障礙

        # 更新 session
        session['grid'] = grid
        session['start_set'] = start_set
        session['end_set'] = end_set

    return render_template('grid.html', grid=grid, n=n)


@app.route('/policy')
def policy():
    """
    顯示「策略矩陣」與「價值矩陣」。
    - 策略矩陣：每個格子一個箭頭（上、下、左、右）或障礙(X)
    - 價值矩陣：示範用隨機數代表 V(s)
    """
    if 'grid' not in session:
        return redirect(url_for('index'))

    n = session['n']
    grid = session['grid']

    # 隨機產生策略 (Policy)
    # policy[i][j] = '^' / 'v' / '<' / '>' (上/下/左/右)
    directions = ['↑', '↓', '←', '→']
    policy_matrix = []
    for i in range(n):
        row = []
        for j in range(n):
            if grid[i][j]['color'] == 'gray':
                row.append('X')  # 障礙
            else:
                row.append(random.choice(directions))
        policy_matrix.append(row)

    # 產生價值矩陣 (Value)，這裡用隨機數作示範
    value_matrix = []
    for i in range(n):
        row = []
        for j in range(n):
            if grid[i][j]['color'] == 'gray':
                row.append('障礙')
            else:
                val = round(random.uniform(-5, 5), 2)
                row.append(val)
        value_matrix.append(row)

    return render_template('policy.html',
                           n=n,
                           policy_matrix=policy_matrix,
                           value_matrix=value_matrix)


if __name__ == '__main__':
    app.run(debug=True)
