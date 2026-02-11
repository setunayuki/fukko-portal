import pandas as pd
from flask import Flask, render_template_string
import os

app = Flask(__name__)

# --- 設定：スプレッドシート情報 ---
SHEET_ID = "1incBINNVhc64m6oRNCIKgkhMrUOTnUUF3v5MfS8eFkg"
# Sheet2を確実に指定
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet2"

def get_all_data():
    try:
        # 1. データを読み込む（2行目をヘッダーとして扱う）
        df = pd.read_csv(SHEET_URL, header=1)
        
        # 2. 列名の前後の余計な空白を削除
        df.columns = df.columns.str.strip()
        
        # 3. 日本語の項目名をプログラムが理解できる英語名に変換
        mapping = {
            'ID': 'id', '店名': 'name', '画像URL': 'image_url',
            '状況': 'status', 'メッセージ': 'message',
            'おすすめ': 'recommendation', '通販URL': 'ec_url', '地図URL': 'map_url'
        }
        df = df.rename(columns=mapping)
        
        # 4. 「店名」が入っていない空の行を削除
        df = df.dropna(subset=['name'])
        
        # 5. IDをきれいな文字列に整える（101.0 -> 101）
        df['id'] = df['id'].astype(str).str.replace('.0', '', regex=False).str.strip()
        
        return df.fillna("未設定")
    except Exception as e:
        print(f"DEBUG ERROR: {e}")
        return None

# --- HTML デザイン (一覧と詳細の切り替え式) ---
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
        {% if shop %}
        <div class="bg-white rounded-2xl shadow-lg border overflow-hidden">
            <img src="{{ shop.image_url }}" class="w-full h-56 object-cover" onerror="this.src='https://via.placeholder.com/400x250?text=No+Image'">
            <div class="p-6">
                <div class="flex justify-between items-start mb-4">
                    <h1 class="text-2xl font-bold text-slate-900 leading-tight">{{ shop.name }}</h1>
                    <span class="shrink-0 text-xs px-2 py-1 rounded bg-emerald-100 text-emerald-700 font-bold border border-emerald-200">
                        {{ shop.status }}
                    </span>
                </div>
                <p class="text-sm text-slate-600 mb-6 leading-relaxed">{{ shop.message }}</p>
                <div class="bg-blue-50 p-4 rounded-xl mb-6 text-sm border border-blue-100">
                    <p class="font-bold text-blue-800 mb-1">✨ おすすめ商品</p>
                    <p class="text-slate-700">{{ shop.recommendation }}</p>
                </div>
                <div class="grid grid-cols-2 gap-3 mb-6">
                    <a href="{{ shop.map_url }}" target="_blank" class="bg-slate-100 text-center py-3 rounded-xl font-bold text-sm hover:bg-slate-200">地図を表示</a>
                    <a href="{{ shop.ec_url }}" target="_blank" class="bg-blue-600 text-white text-center py-3 rounded-xl font-bold text-sm shadow-md hover:bg-blue-700">通販サイト</a>
                </div>
                <a href="/" class="block text-center text-xs text-slate-400 hover:text-blue-600 transition">← 他のお店も見る</a>
            </div>
        </div>
        {% else %}
        <div class="bg-white rounded-2xl shadow-md border p-6">
            <h2 class="text-lg font-bold mb-4 text-center border-b pb-2">応援するお店を選ぶ</h2>
            <div class="space-y-3">
                {% for s in all_shops %}
                <a href="/shop/{{ s.id }}" class="flex items-center p-3 bg-slate-50 rounded-xl border hover:border-blue-400 hover:bg-blue-50 transition group">
                    <div class="flex-1">
                        <div class="font-bold group-hover:text-blue-700">{{ s.name }}</div>
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
    df = get_all_data()
    if df is not None and not df.empty:
        all_shops = df.to_dict(orient='records')
        return render_template_string(LAYOUT, shop=None, all_shops=all_shops)
    return "スプレッドシートを読み込めませんでした。「Sheet2」の共有設定を確認してください。"

@app.route('/shop/<shop_id>')
def render_shop(shop_id):
    df = get_all_data()
    if df is None: return "データエラー"
    row = df[df['id'] == str(shop_id)]
    if row.empty: return "お店が見つかりませんでした", 404
    return render_template_string(LAYOUT, shop=row.iloc[0].to_dict())

if __name__ == '__main__':
    # サーバー実行用設定
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
