import pandas as pd
from flask import Flask, render_template_string
import os

app = Flask(__name__)

# --- 設定 ---
SHEET_ID = "1incBINNVhc64m6oRNCIKgkhMrUOTnUUF3v5MfS8eFkg"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet2"

def get_all_data():
    try:
        # スプレッドシートを読み込む（2行目をヘッダーとして指定）
        df = pd.read_csv(SHEET_URL, header=1)
        
        # 列名の前後の空白を削除
        df.columns = df.columns.str.strip()
        
        # スプレッドシートの項目名(日本語)をプログラム用の名前(英語)に変換
        mapping = {
            'ID': 'id', '店名': 'name', '画像URL': 'image_url',
            '状況': 'status', 'メッセージ': 'message',
            'おすすめ': 'recommendation', '通販URL': 'ec_url', '地図URL': 'map_url'
        }
        df = df.rename(columns=mapping)
        
        # IDをきれいな文字列にする
        if 'id' in df.columns:
            df['id'] = df['id'].astype(str).str.replace('.0', '', regex=False).str.strip()
        
        # 店名が入っていない行（空行）を削除
        df = df.dropna(subset=['name'])
        
        return df.fillna("未設定")
    except Exception as e:
        print(f"ERROR: {e}")
        return None

# --- HTML デザイン ---
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
                <a href="/" class="block text-center text-xs text-slate-400 hover:underline">← お店一覧に戻る</a>
            </div>
        </div>
        {% else %}
        <div class="bg-white rounded-2xl shadow-sm border p-6">
            <h2 class="text-lg font-bold mb-4 text-center">応援するお店を選んでください</h2>
            <div class="space-y-3">
                {% for s in all_shops %}
                <a href="/shop/{{ s.id }}" class="block p-4 bg-slate-50 rounded-xl border hover:border-blue-500 hover:bg-blue-50 transition">
                    <div class="font-bold">{{ s.name }}</div>
                    <div class="text-xs text-slate-500 mt-1">{{ s.status }}</div>
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
    return "データが見つかりませんでした。スプレッドシートの共有設定と内容を確認してください。"

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
