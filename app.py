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
    if 'grid' not in session:
        return redirect(url_for('index'))

    grid = session['grid']
    n = session['n']
    start_set = session['start_set']
    end_set = session['end_set']

    if request.method == 'POST':
        i = int(request.form.get('i'))
        j = int(request.form.get('j'))

        # 只有「白色」格子才處理
        if grid[i][j]['color'] == 'white':
            if not start_set:
                grid[i][j]['color'] = 'green'  # 起點
                start_set = True
            elif not end_set:
                grid[i][j]['color'] = 'red'  # 終點
                end_set = True
            else:
                # 計算目前已有多少個障礙
                obstacle_count = sum(cell['color'] == 'gray' for row in grid for cell in row)
                if obstacle_count < (n - 2):
                    grid[i][j]['color'] = 'gray'  # 障礙
                else:
                    # 障礙物數量已達上限，這裡可以選擇不做處理或回傳提示訊息
                    pass

        # 更新 session
        session['grid'] = grid
        session['start_set'] = start_set
        session['end_set'] = end_set

    return render_template('grid.html', grid=grid, n=n)



def value_iteration(grid, gamma=0.9, theta=1e-4):
    """
    假設已實作好的「價值迭代」函式，返回:
    V: dict, 例如 {(i, j): value, ...}
    policy: dict, 例如 {(i, j): 'up'/'down'/'left'/'right', ...}
    """
    n = len(grid)
    V = {}
    # 初始化
    for i in range(n):
        for j in range(n):
            if grid[i][j]['color'] != 'gray':
                V[(i, j)] = 0.0

    # 找目標(終點)
    goal = None
    for i in range(n):
        for j in range(n):
            if grid[i][j]['color'] == 'red':
                goal = (i, j)
                break
        if goal:
            break

    # 若找不到紅色終點，可視情況自行定義(略)

    actions = {
        'up': (-1, 0),
        'down': (1, 0),
        'left': (0, -1),
        'right': (0, 1)
    }

    while True:
        delta = 0
        for s in V.keys():
            # 終點不更新
            if s == goal:
                continue

            best_value = float('-inf')
            best_action = None

            for a, (di, dj) in actions.items():
                i, j = s
                ni, nj = i + di, j + dj
                # 邊界或障礙就留在原地
                if not (0 <= ni < n and 0 <= nj < n) or grid[ni][nj]['color'] == 'gray':
                    next_s = s
                else:
                    next_s = (ni, nj)

                # 假設走一步 -1，到達終點 0
                r = 0 if next_s == goal else -1
                q_value = r + gamma * V[next_s]
                if q_value > best_value:
                    best_value = q_value
                    best_action = a

            delta = max(delta, abs(best_value - V[s]))
            V[s] = best_value
            # 把最佳動作暫存在 V 以外的地方也行，這裡先一起存
            # 你可以分開用 policy dict
        if delta < theta:
            break

    # 單獨建立一個 policy dict
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
    """
    根據 policy，從「綠色起點」一路走到「紅色終點」，
    回傳經過的狀態清單 best_path。
    """
    n = len(grid)
    # 找出起點
    start = None
    end = None
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
            # 到終點就結束
            break
        action = policy.get(current)
        if not action:
            # 該狀態沒有定義動作(可能是障礙或終點)
            break
        di, dj = {
            'up': (-1, 0),
            'down': (1, 0),
            'left': (0, -1),
            'right': (0, 1)
        }[action]
        next_i, next_j = current[0] + di, current[1] + dj
        # 邊界檢查
        if not (0 <= next_i < n and 0 <= next_j < n):
            break
        # 障礙檢查
        if grid[next_i][next_j]['color'] == 'gray':
            break
        next_s = (next_i, next_j)
        # 防止死循環
        if next_s in visited:
            break
        current = next_s

    return best_path


@app.route('/policy')
def policy():
    if 'grid' not in session:
        return redirect(url_for('index'))

    grid = session['grid']
    n = session['n']

    # 1. 用價值迭代拿到 V, policy
    V, optimal_policy = value_iteration(grid)

    # 2. 找出「最佳路徑」(從起點到終點)
    best_path = find_path(grid, optimal_policy)

    # 3. 把 policy 轉成箭頭符號、把 V 四捨五入
    arrow_map = {
        'up': '↑',
        'down': '↓',
        'left': '←',
        'right': '→',
        None: ''  # 終點等可以不顯示
    }

    policy_matrix = []
    value_matrix = []
    for i in range(n):
        p_row = []
        v_row = []
        for j in range(n):
            if grid[i][j]['color'] == 'gray':
                # 障礙
                p_row.append('X')
                v_row.append('障礙')
            else:
                # 轉換箭頭
                action = optimal_policy.get((i, j), None)
                arrow = arrow_map.get(action, '')
                p_row.append(arrow)
                # 狀態價值
                v_val = V.get((i, j), 0)
                v_row.append(round(v_val, 2))
        policy_matrix.append(p_row)
        value_matrix.append(v_row)

    # 4. 在 render_template 時，把 best_path 傳給前端
    return render_template('policy.html',
                           n=n,
                           policy_matrix=policy_matrix,
                           value_matrix=value_matrix,
                           best_path=best_path)

if __name__ == '__main__':
    app.run(debug=True)
