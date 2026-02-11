import pandas as pd
from flask import Flask, render_template_string, abort
import os

app = Flask(__name__)

# --- 設定：スプレッドシートの情報 ---
SHEET_ID = "1incBINNVhc64m6oRNCIKgkhMrUOTnUUF3v5MfS8eFkg"
# Sheet2を指定
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet2"

def get_all_data():
    try:
        # 一旦ヘッダーなしで読み込んで、2行目（Index 1）を項目名としてセットする
        raw_df = pd.read_csv(SHEET_URL, header=None)
        
        # 2行目（1行目は見出しタイトルなので飛ばす）をカラム名にする
        df = raw_df.iloc[2:].copy()
        df.columns = raw_df.iloc[1].str.strip()
        
        # プログラムで使いやすいように日本語名を英語名にマッピング
        rename_map = {
            'ID': 'id',
            '店名': 'name',
            '画像URL': 'image_url',
            '状況': 'status',
            'メッセージ': 'message',
            'おすすめ': 'recommendation',
            '通販URL': 'ec_url',
            '地図URL': 'map_url'
        }
        df = df.rename(columns=rename_map)
        
        # ID列をきれいにする
        df['id'] = df['id'].astype(str).str.replace('.0', '', regex=False).str.strip()
        
        return df.fillna("未設定")
    except Exception as e:
        print(f"読み込みエラー発生: {e}")
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
                <div class="grid grid-cols-2 gap-3">
                    <a href="{{ shop.map_url }}" target="_blank" class="bg-slate-100 text-center py-3 rounded-xl font-bold text-sm">地図</a>
                    <a href="{{ shop.ec_url }}" target="_blank" class="bg-blue-600 text-white text-center py-3 rounded-xl font-bold text-sm shadow-md">通販</a>
                </div>
            </div>
        </div>
        {% else %}
        <div class="text-center p-10 bg-white rounded-xl border">
            <p class="text-red-500 font-bold">データが見つかりません</p>
            <p class="text-xs text-slate-400 mt-2">スプレッドシートの2行目が「ID, 店名...」になっているか確認してください。</p>
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
        # ループを避けるため、直接1番目のデータを表示
        shop_data = df.iloc[0].to_dict()
        return render_template_string(LAYOUT, shop=shop_data)
    return "スプレッドシートが読み込めませんでした。共有設定を確認してください。"

@app.route('/shop/<shop_id>')
def render_shop(shop_id):
    df = get_all_data()
    if df is None: return "データエラー"
    
    # IDを検索
    row = df[df['id'] == str(shop_id)]
    
    if row.empty:
        # IDが見
