import pandas as pd
from flask import Flask, render_template_string, abort
import os

app = Flask(__name__)

# --- 設定：スプレッドシートの情報 ---
SHEET_ID = "1incBINNVhc64m6oRNCIKgkhMrUOTnUUF3v5MfS8eFkg"
# header=1 (2行目) を項目名として読み込む設定をURLに付与
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet2"

def get_all_data():
    """スプレッドシートから全データを読み込む"""
    try:
        # skiprows=1 または header=1 で、スプレッドシートの2行目をヘッダーとして読み込む
        df = pd.read_csv(SHEET_URL, header=1)
        
        # 列名の空白を削除
        df.columns = df.columns.str.strip()
        
        # スプレッドシートの日本語名を、プログラムで使う英語名に変換
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
        
        # id列を文字列に変換（101などが数値として扱われないようにする）
        if 'id' in df.columns:
            df['id'] = df['id'].astype(str).str.replace('.0', '', regex=False)
            
        return df.fillna("未設定")
    except Exception as e:
        print(f"DEBUG ERROR: {e}")
        return None

# --- HTML デザイン (変更なし) ---
LAYOUT = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
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
                    <a href="{{ shop.map_url }}" target="_blank" class="bg-slate-100 text-center py-3 rounded-xl font-bold text-sm">地図を表示</a>
                    <a href="{{ shop.ec_url }}" target="_blank" class="bg-blue-600 text-white text-center py-3 rounded-xl font-bold text-sm shadow-md">通販サイト</a>
                </div>
            </div>
        </div>
        {% else %}
        <div class="text-center p-10 text-slate-500">
            データが読み込めませんでした。スプレッドシートの2行目に「ID, 店名...」があるか確認してください。
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
        return render_shop(df.iloc[0]['id'])
    return "データが見つかりません。"

@app.route('/shop/<shop_id>')
def render_shop(shop_id):
    df = get_all_data()
    if df is None: return "データエラー"
    
    # IDで検索
    row = df[df['id'] == str(shop_id)]
    
    if row.empty:
        return f"店舗ID {shop_id} は見つかりません。", 404
        
    return render_template_string(LAYOUT, shop=row.iloc[0].to_dict())

if __name__ == '__main__':
    # サーバー上での実行に対応
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
