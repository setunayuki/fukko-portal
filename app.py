import pandas as pd
from flask import Flask, render_template_string, abort
import os

app = Flask(__name__)

# --- 設定 ---
# スプレッドシートのIDと直接編集用URL
SHEET_ID = "1incBINNVhc64m6oRNCIKgkhMrUOTnUUF3v5MfS8eFkg"
EDIT_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit#gid=1191908203"
# CSV取得用URL（2行目を見出しとして読み込む設定）
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet2"

def get_all_data():
    try:
        # データを読み込む
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip()
        
        # 列名の日本語マッピング（エラー回避のため、存在を確認しながら適用）
        mapping = {
            'ID': 'id', '店名': 'name', '画像URL': 'image_url',
            '状況': 'status', 'メッセージ': 'message',
            'おすすめ': 'recommendation', '通販URL': 'ec_url', '地図URL': 'map_url'
        }
        df = df.rename(columns=mapping)
        
        # IDを文字列に整える（空でないものに絞る）
        df = df.dropna(subset=['id'])
        df['id'] = df['id'].astype(str).str.replace('.0', '', regex=False).str.strip()
        
        return df.fillna("未設定")
    except Exception as e:
        print(f"Error reading sheet: {e}")
        return None

# --- HTML デザイン（温かみのあるアイボリー背景） ---
LAYOUT = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <title>復興支援ポータル</title>
    <style>
        body { background-color: #fffaf0; } /* 温かみのあるベージュ */
        .card-shadow { box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05); }
    </style>
</head>
<body class="min-h-screen text-slate-800 pb-24">
    <nav class="bg-orange-600 text-white p-6 mb-8 shadow-lg text-center">
        <h1 class="text-2xl font-bold tracking-widest"><a href="/">復興支援ポータル</a></h1>
        <p class="text-xs mt-1 opacity-90">〜大切な場所を、みんなで支える〜</p>
    </nav>

    <div class="max-w-md mx-auto px-4">
        {% if shop %}
        <div class="bg-white rounded-3xl overflow-hidden card-shadow border-t-8 border-orange-500">
            <div class="relative">
                <img src="{{ shop.image_url }}" class="w-full h-60 object-cover" onerror="this.src='https://images.unsplash.com/photo-1528605248644-14dd04022da1?auto=format&fit=crop&w=500&q=60'">
                <div class="absolute top-4 right-4 px-3 py-1 bg-white/90 rounded-full text-orange-700 font-bold text-xs shadow-sm">
                    {{ shop.status }}
                </div>
            </div>
            <div class="p-8">
                <h2 class="text-3xl font-black text-slate-900 mb-4">{{ shop.name }}</h2>
                <div class="bg-orange-50 rounded-2xl p-4 mb-6 italic text-slate-700 leading-relaxed border-l-4 border-orange-200">
                    「{{ shop.message }}」
                </div>
                <div class="mb-8">
                    <p class="text-[10px] font-bold text-orange-400 uppercase tracking-widest mb-1">✨ おすすめ商品</p>
                    <p class="text-lg text-slate-800 font-bold">{{ shop.recommendation }}</p>
                </div>
                <div class="grid grid-cols-1 gap-4">
                    <a href="{{ shop.ec_url }}" target="_blank" class="flex items-center justify-center bg-orange-500 text-white py-4 rounded-2xl font-bold text-lg hover:bg-orange-600 transition shadow-lg shadow-orange-100">
                        🛒 通販でお買い物
                    </a>
                    {% if shop.map_url != '未設定' %}
                    <a href="{{ shop.map_url }}" target="_blank" class="text-center py-2 text-sm text-slate-400 font-bold hover:text-orange-500 transition">
                        📍 地図で場所を確認
                    </a>
                    {% endif %}
                </div>
                <div class="mt-10 pt-6 border-t border-slate-50 text-center">
                    <a href="/" class="text-slate-300 hover:text-orange-500 font-bold text-xs transition">← お店一覧に戻る</a>
                </div>
            </div>
        </div>
        {% else %}
        <div class="space-y-4">
            <h2 class="text-center text-slate-400 font-bold text-sm tracking-widest mb-6">応援するお店を選ぶ</h2>
            {% for s in all_shops %}
            <a href="/shop/{{ s.id }}" class="flex items-center p-4 bg-white rounded-2xl card-shadow border border-orange-50 hover:border-orange-200 transition group">
                <div class="w-16 h-16 rounded-xl overflow-hidden shrink-0 border border-slate-50">
                    <img src="{{ s.image_url }}" class="w-full h-full object-cover" onerror="this.src='https://via.placeholder.com/100?text=Shop'">
                </div>
                <div class="ml-4 flex-1">
                    <span class="text-[9px] font-black text-orange-400">{{ s.status }}</span>
                    <h3 class="text-lg font-bold text-slate-800 group-hover:text-orange-600 transition">{{ s.name }}</h3>
                </div>
                <div class="text-orange-200 group-hover:translate-x-1 transition-transform">▶︎</div>
            </a>
            {% endfor %}
            
            {% if not all_shops %}
            <div class="text-center py-20 bg-white/50 rounded-3xl border-2 border-dashed border-orange-100">
                <p class="text-slate-400 font-bold text-sm">現在登録されているお店はありません</p>
            </div>
            {% endif %}
        </div>
        {% endif %}
    </div>

    <div class="fixed bottom-6 right-6 z-50">
        <a href="{{ edit_url }}" target="_blank" class="flex items-center justify-center w-14 h-14 bg-slate-800 text-white rounded-full shadow-2xl hover:scale-110 active:scale-95 transition transform group">
            <span class="text-2xl font-light">＋</span>
            <span class="absolute right-16 bg-slate-800 text-white text-[10px] px-3 py-1 rounded-lg opacity-0 group-hover:opacity-100 transition whitespace-nowrap pointer-events-none">
                事業者の方：情報を追加・修正
            </span>
        </a>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    df = get_all_data()
    all_shops = df.to_dict(orient='records') if df is not None else []
    return render_template_string(LAYOUT, shop=None, all_shops=all_shops, edit_url=EDIT_URL)

@app.route('/shop/<shop_id>')
def render_shop(shop_id):
    df = get_all_data()
    if df is None: abort(500)
    row = df[df['id'] == str(shop_id)]
    if row.empty: abort(404)
    return render_template_string(LAYOUT, shop=row.iloc[0].to_dict(), edit_url=EDIT_URL)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
