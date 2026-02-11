import pandas as pd
from flask import Flask, render_template_string
import os

app = Flask(__name__)

# --- 設定 ---
SHEET_ID = "1incBINNVhc64m6oRNCIKgkhMrUOTnUUF3v5MfS8eFkg"
# Sheet2を確実にCSVで取得するためのURL
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet2"

def get_all_data():
    try:
        # 1. データを読み込む（2行目を項目名として指定）
        df = pd.read_csv(SHEET_URL, header=1)
        
        # 2. 列名を強制的にきれいにし、不足している列があれば補う
        # 左から順番にこの役割だと決め打ちします
        expected_columns = ['id', 'name', 'image_url', 'status', 'message', 'recommendation', 'ec_url', 'map_url']
        
        # 現在読み込めている列数に合わせて、列名を上書き
        new_columns = list(df.columns)
        for i in range(min(len(new_columns), len(expected_columns))):
            new_columns[i] = expected_columns[i]
        df.columns = new_columns

        # 3. 「name」（店名）列が存在し、かつ中身が入っている行だけに絞り込む
        if 'name' in df.columns:
            df = df.dropna(subset=['name'])
            # 項目名自体がデータとして混じっている場合は除外
            df = df[df['name'] != '店名']
        else:
            return "スプレッドシートから『店名』が見つかりません。"
        
        # 4. IDをきれいな文字列にする（101.0 -> 101）
        if 'id' in df.columns:
            df['id'] = df['id'].astype(str).str.replace('.0', '', regex=False).str.strip()
        
        return df.fillna("未設定")
    except Exception as e:
        return f"読み込みエラー: {str(e)}"

# --- HTML デザイン ---
LAYOUT = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <title>能登復興支援ポータル</title>
</head>
<body class="bg-slate-50 min-h-screen text-slate-800 pb-10">
    <nav class="bg-blue-800 text-white p-4 mb-6 shadow-md font-bold text-center text-lg">
        <a href="/">能登復興支援ポータル</a>
    </nav>
    <div class="max-w-md mx-auto px-4">
        {% if error_msg %}
            <div class="bg-red-50 border border-red-200 p-4 rounded-xl text-red-600 text-sm">
                <strong>エラーが発生しました:</strong><br>{{ error_msg }}
            </div>
        {% elif shop %}
            <div class="bg-white rounded-2xl shadow-lg border overflow-hidden">
                <img src="{{ shop.image_url }}" class="w-full h-56 object-cover" onerror="this.src='https://via.placeholder.com/400x250?text=No+Image'">
                <div class="p-6">
                    <h1 class="text-2xl font-bold mb-2">{{ shop.name }}</h1>
                    <span class="inline-block mb-4 text-xs px-2 py-1 rounded bg-emerald-100 text-emerald-700 font-bold border border-emerald-200">
                        {{ shop.status }}
                    </span>
                    <p class="text-sm text-slate-600 mb-6 leading-relaxed">{{ shop.message }}</p>
                    <div class="bg-blue-50 p-4 rounded-xl mb-6 text-sm border border-blue-100">
                        <p class="font-bold text-blue-800 mb-1">✨ おすすめ商品</p>
                        <p class="text-slate-700">{{ shop.recommendation }}</p>
                    </div>
                    <div class="grid grid-cols-2 gap-3 mb-6">
                        <a href="{{ shop.map_url }}" target="_blank" class="bg-slate-100 text-center py-3 rounded-xl font-bold text-sm">地図を表示</a>
                        <a href="{{ shop.ec_url }}" target="_blank" class="bg-blue-600 text-white text-center py-3 rounded-xl font-bold text-sm shadow-md">通販サイト</a>
                    </div>
                    <a href="/" class="block text-center text-xs text-slate-400">← お店一覧に戻る</a>
                </div>
            </div>
        {% else %}
            <div class="bg-white rounded-2xl shadow-md border p-6">
                <h2 class="text-lg font-bold mb-4 text-center border-b pb-2">応援するお店を選ぶ</h2>
                <div class="space-y-3">
                    {% for s in all_shops %}
                    <a href="/shop/{{ s.id }}" class="flex items-center p-3 bg-slate-50 rounded-xl border hover:border-blue-400 hover:bg-blue-50 transition">
                        <div class="flex-1">
                            <div class="font-bold">{{ s.name }}</div>
                            <div class="text-xs text-slate-500 mt-1">{{ s.status }}</div>
                        </div>
                        <div class="text-slate-300">▶</div>
                    </a>
                    {% endfor %}
                </div>
            </div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    data = get_all_data()
    if isinstance(data, str):
        return render_template_string(LAYOUT, error_msg=data)
    if data is not None and not data.empty:
        all_shops = data.to_dict(orient='records')
        return render_template_string(LAYOUT, shop=None, all_shops=all_shops)
    return render_template_string(LAYOUT, error_msg="データが空です。スプレッドシートを確認してください。")

@app.route('/shop/<shop_id>')
def render_shop(shop_id):
    data = get_all_data()
    if isinstance(data, str):
        return render_template_string(LAYOUT, error_msg=data)
    row = data[data['id'] == str(shop_id)]
    if row.empty:
        return "お店が見つかりませんでした", 404
    return render_template_string(LAYOUT, shop=row.iloc[0].to_dict())

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
