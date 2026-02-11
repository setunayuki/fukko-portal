import pandas as pd
from flask import Flask, render_template_string, abort
import os

app = Flask(__name__)

# --- 設定 ---
SHEET_ID = "1incBINNVhc64m6oRNCIKgkhMrUOTnUUF3v5MfS8eFkg"
# Sheet2を指定してCSV取得
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet2"

def get_all_data():
    try:
        # 2行目（Index 1）をヘッダーとして読み込む
        df = pd.read_csv(SHEET_URL, header=1)
        df.columns = df.columns.str.strip()
        
        # 列名の日本語マッピング
        mapping = {
            'ID': 'id', '店名': 'name', '画像URL': 'image_url',
            '状況': 'status', 'メッセージ': 'message',
            'おすすめ': 'recommendation', '通販URL': 'ec_url', '地図URL': 'map_url'
        }
        df = df.rename(columns=mapping)
        
        # データのクリーンアップ（店名がない行や見出し行を削除）
        df = df.dropna(subset=['name'])
        df = df[df['name'] != '店名']
        
        # IDを文字列に整える
        df['id'] = df['id'].astype(str).str.replace('.0', '', regex=False).str.strip()
        
        return df.fillna("未設定")
    except Exception as e:
        print(f"Error: {e}")
        return None

# --- HTML デザイン（温かみのあるオレンジ・ベージュ系） ---
LAYOUT = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <title>復興支援ポータル</title>
    <style>
        body { background-color: #fffaf0; } /* 温かみのあるアイボリー */
        .card-orange { border-top: 8px solid #ff8c00; }
    </style>
</head>
<body class="min-h-screen text-slate-800 pb-10">
    <nav class="bg-orange-600 text-white p-6 mb-8 shadow-lg text-center">
        <h1 class="text-2xl font-bold tracking-widest"><a href="/">復興支援ポータル</a></h1>
        <p class="text-xs mt-1 opacity-90">〜お店と支援者をつなぐ場所〜</p>
    </nav>

    <div class="max-w-md mx-auto px-4">
        {% if shop %}
        <div class="bg-white rounded-3xl shadow-xl overflow-hidden card-orange animate-fade-in">
            <div class="relative">
                <img src="{{ shop.image_url }}" class="w-full h-64 object-cover" onerror="this.src='https://images.unsplash.com/photo-1528605248644-14dd04022da1?auto=format&fit=crop&w=500&q=60'">
                <div class="absolute top-4 right-4">
                    <span class="px-4 py-1.5 rounded-full bg-white/90 text-orange-700 font-bold text-sm shadow-sm border border-orange-200">
                        {{ shop.status }}
                    </span>
                </div>
            </div>
            
            <div class="p-8">
                <h2 class="text-3xl font-extrabold text-slate-900 mb-4 leading-tight">{{ shop.name }}</h2>
                
                <div class="bg-orange-50 border-l-4 border-orange-400 p-4 mb-6 italic text-slate-700 leading-relaxed">
                    「{{ shop.message }}」
                </div>

                <div class="mb-8">
                    <p class="text-xs font-bold text-orange-500 uppercase tracking-wider mb-2">✨ 店主のおすすめ</p>
                    <p class="text-lg text-slate-800 font-medium">{{ shop.recommendation }}</p>
                </div>

                <div class="grid grid-cols-1 gap-4">
                    <a href="{{ shop.ec_url }}" target="_blank" class="flex items-center justify-center bg-orange-500 text-white py-4 rounded-2xl font-bold text-lg shadow-orange-200 shadow-lg hover:bg-orange-600 transition-all transform hover:-translate-y-1">
                        🛒 通販サイトでお買い物
                    </a>
                    
                    {% if shop.map_url != '未設定' %}
                    <div class="mt-4">
                        <p class="text-xs font-bold text-slate-400 mb-2 text-center">お店の場所（地図）</p>
                        <div class="rounded-2xl overflow-hidden border-2 border-slate-100 h-48">
                            <iframe 
                                width="100%" height="100%" frameborder="0" style="border:0"
                                src="https://www.google.com/maps/embed/v1/search?key=YOUR_API_KEY_OPTIONAL&q={{ shop.name }}" 
                                allowfullscreen>
                            </iframe>
                        </div>
                        <a href="{{ shop.map_url }}" target="_blank" class="block text-center mt-2 text-sm text-orange-600 font-bold underline">
                            大きな地図で開く
                        </a>
                    </div>
                    {% endif %}
                </div>

                <div class="mt-10 pt-6 border-t border-slate-100 text-center">
                    <a href="/" class="text-slate-400 hover:text-orange-500 font-bold text-sm transition">
                        ← ほかのお店も見てみる
                    </a>
                </div>
            </div>
        </div>
        {% else %}
        <div class="space-y-6">
            <p class="text-center text-slate-500 font-medium mb-4">いま、応援を必要としているお店</p>
            {% for s in all_shops %}
            <a href="/shop/{{ s.id }}" class="block bg-white rounded-2xl p-4 shadow-md border border-orange-100 hover:shadow-xl transition-all transform hover:-translate-y-1 group">
                <div class="flex items-center gap-4">
                    <div class="w-20 h-20 rounded-xl overflow-hidden shrink-0">
                        <img src="{{ s.image_url }}" class="w-full h-full object-cover" onerror="this.src='https://via.placeholder.com/100?text=No+Photo'">
                    </div>
                    <div class="flex-1">
                        <span class="text-[10px] font-bold text-orange-400">{{ s.status }}</span>
                        <h3 class="text-lg font-bold text-slate-800 group-hover:text-orange-600 transition">{{ s.name }}</h3>
                        <p class="text-xs text-slate-500 line-clamp-1 mt-1">{{ s.message }}</p>
                    </div>
                    <div class="text-orange-300 group-hover:translate-x-1 transition-transform">▶︎</div>
                </div>
            </a>
            {% endfor %}
        </div>
        {% endif %}
    </div>

    <footer class="mt-20 text-center text-slate-400 text-xs">
        &copy; 2026 復興支援ポータル 運営事務局
    </footer>
</body>
</html>
"""

@app.route('/')
def index():
    df = get_all_data()
    if df is not None and not df.empty:
        all_shops = df.to_dict(orient='records')
        return render_template_string(LAYOUT, shop=None, all_shops=all_shops)
    return "読み込み中、またはデータがありません。"

@app.route('/shop/<shop_id>')
def render_shop(shop_id):
    df = get_all_data()
    if df is None: abort(500)
    row = df[df['id'] == str(shop_id)]
    if row.empty: abort(404)
    return render_template_string(LAYOUT, shop=row.iloc[0].to_dict())

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
