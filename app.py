import pandas as pd
from flask import Flask, render_template_string
import os

app = Flask(__name__)

# --- 設定 ---
# スプレッドシートのID（URLから抽出したもの）
SHEET_ID = "1incBINNVhc64m6oRNCIKgkhMrUOTnUUF3v5MfS8eFkg"
# Sheet2を指定してCSV形式で読み込むURL
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet2"

def get_all_data():
    try:
        # 1. データを読み込む（2行目をヘッダーとする）
        # もしエラーが出る場合は、ここが原因の可能性が高い
        df = pd.read_csv(SHEET_URL, header=1)
        
        # 2. 列名の空白を削除
        df.columns = df.columns.str.strip()
        
        # 3. 列名を強制的に英語名に上書き（左からの順番を信じる）
        # スプレッドシートの列順：ID, 店名, 画像URL, 状況, メッセージ, おすすめ, 通販URL, 地図URL
        expected_cols = ['id', 'name', 'image_url', 'status', 'message', 'recommendation', 'ec_url', 'map_url']
        
        # 取得した列数が足りない場合の対策
        if len(df.columns) >= len(expected_cols):
            new_columns = list(df.columns)
            for i in range(len(expected_cols)):
                new_columns[i] = expected_cols[i]
            df.columns = new_columns
        
        # 4. 「店名」がない行を削除
        df = df.dropna(subset=['name'])
        
        # 5. IDをきれいな文字列にする
        df['id'] = df['id'].astype(str).str.replace('.0', '', regex=False).str.strip()
        
        return df.fillna("未設定")
    except Exception as e:
        # エラーが発生した際、その内容を保存して後で表示できるようにする
        return str(e)

# --- デザイン ---
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
                    <p class="text-sm text-slate-600 mb-6">{{ shop.message }}</p>
                    <div class="bg-blue-50 p-4 rounded-xl mb-6 text-sm border border-blue-100">
                        <p class="font-bold text-blue-800 mb-1">✨ おすすめ</p>
                        <p>{{ shop.recommendation }}</p>
                    </div>
                    <div class="grid grid-cols-2 gap-3 mb-6">
                        <a href="{{ shop.map_url }}" target="_blank" class="bg-slate-100 text-center py-3 rounded-xl font-bold text-sm">地図</a>
                        <a href="{{ shop.ec_url }}" target="_blank" class="bg-blue-600 text-white text-center py-3 rounded-xl font-bold text-sm shadow-md">通販</a>
                    </div>
                    <a href="/" class="block text-center text-xs text-slate-400">← 一覧に戻る</a>
                </div>
            </div>
        {% else %}
            <div class="bg-white rounded-2xl shadow-md border p-6">
                <h2 class="text-lg font-bold mb-4 text-center border-b pb-2">応援するお店を選ぶ</h2>
                <div class="space-y-3">
                    {% for s in all_shops %}
                    <a href="/shop/{{ s.id }}" class="flex items-center p-3 bg-slate-50 rounded-xl border hover:bg-blue-50 transition">
                        <div class="flex-1">
                            <div class="font-bold">{{ s.name }}</div>
                            <div class="text-xs text-slate-500">{{ s.status }}</div>
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
    return render_template_string(LAYOUT, error_msg="データが空です。スプレッドシートのSheet2に内容があるか確認してください。")

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
