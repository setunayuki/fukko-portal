import pandas as pd
from flask import Flask, render_template_string
import os

app = Flask(__name__)

# --- 設定 ---
SHEET_ID = "1incBINNVhc64m6oRNCIKgkhMrUOTnUUF3v5MfS8eFkg"
# Sheet2を指定してCSVで取得
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet2"

def get_all_data():
    try:
        # 1. まず全データを読み込む
        df_raw = pd.read_csv(SHEET_URL, header=None)
        
        # 2. 「ID」という文字が入っている行をヘッダーとして探す（柔軟な対応）
        header_row_index = 0
        for i, row in df_raw.iterrows():
            if "ID" in row.values:
                header_row_index = i
                break
        
        # 3. 見つかったヘッダー行を基準にデータを切り出す
        df = df_raw.iloc[header_row_index + 1:].copy()
        df.columns = df_raw.iloc[header_row_index].str.strip()
        
        # 4. 列名を英語に変換（日本語のカラム名に100%合わせる）
        rename_map = {
            'ID': 'id', '店名': 'name', '画像URL': 'image_url',
            '状況': 'status', 'メッセージ': 'message',
            'おすすめ': 'recommendation', '通販URL': 'ec_url', '地図URL': 'map_url'
        }
        df = df.rename(columns=rename_map)
        
        # 5. データのクリーンアップ
        df = df.dropna(subset=['id', 'name']) # IDと店名がない行は消す
        df['id'] = df['id'].astype(str).str.replace('.0', '', regex=False).str.strip()
        
        return df.fillna("未設定")
    except Exception as e:
        print(f"DEBUG: 読み込みエラー {e}")
        return None

# --- デザイン (少し改良して一覧ボタンも追加) ---
LAYOUT = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <title>復興支援ポータル</title>
</head>
<body class="bg-slate-50 min-h-screen text-slate-800 pb-10">
    <nav class="bg-blue-700 text-white p-4 mb-6 shadow-md font-bold text-center text-lg">
        <a href="/">復興支援ポータル</a>
    </nav>
    <div class="max-w-md mx-auto px-4">
        {% if shop %}
        <div class="bg-white rounded-2xl shadow-sm border overflow-hidden">
            <img src="{{ shop.image_url }}" class="w-full h-52 object-cover" onerror="this.src='https://via.placeholder.com/400x250?text=No+Image'">
            <div class="p-6">
                <div class="flex justify-between items-center mb-4">
                    <h1 class="text-2xl font-bold text-slate-900">{{ shop.name }}</h1>
                    <span class="text-xs px-2 py-1 rounded bg-emerald-100 text-emerald-600 font-bold border border-emerald-200">
                        {{ shop.status }}
                    </span>
                </div>
                <p class="text-sm text-slate-600 mb-6 leading-relaxed">{{ shop.message }}</p>
                <div class="bg-blue-50 p-4 rounded-xl mb-6 text-sm border border-blue-100">
                    <p class="font-bold text-blue-800 mb-1">✨ おすすめ</p>
                    <p class="text-slate-700">{{ shop.recommendation }}</p>
                </div>
                <div class="grid grid-cols-2 gap-3 mb-4">
                    <a href="{{ shop.map_url }}" target="_blank" class="bg-slate-100 text-center py-3 rounded-xl font-bold text-sm">地図を表示</a>
                    <a href="{{ shop.ec_url }}" target="_blank" class="bg-blue-600 text-white text-center py-3 rounded-xl font-bold text-sm shadow-md">通販サイト</a>
                </div>
                <a href="/" class="block text-center text-xs text-slate-400 hover:underline">← 他の店も見る（トップへ）</a>
            </div>
        </div>
        {% else %}
        <div class="text-center p-10 bg-white rounded-xl border">
            <p class="font-bold">お店を選択してください</p>
            <div class="mt-4 space-y-2">
                {% for s in all_shops %}
                <a href="/shop/{{ s.id }}" class="block p-3 bg-slate-50 rounded-lg border hover:bg-blue-50 transition text-sm">
                    {{ s.name }} ({{ s.status }})
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
    df = get_all_data()
    if df is not None and not df.empty:
        all_shops = df.to_dict(orient='records')
        return render_template_string(LAYOUT, shop=None, all_shops=all_shops)
    return "データが見つかりません。"

@app.route('/shop/<shop_id>')
def render_shop(shop_id):
    df = get_all_data()
    if df is None: return "読み込みエラー"
    row = df[df['id'] == str(shop_id)]
    if row.empty: return "お店が見つかりません", 404
    return render_template_string(LAYOUT, shop=row.iloc[0].to_dict())

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
