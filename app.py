import pandas as pd
from flask import Flask, render_template_string

app = Flask(__name__)

# --- 設定：あなたのスプレッドシートID ---
# ※共有設定が「リンクを知っている全員：編集者」になっていることを確認してください
SHEET_ID = "1incBINNVhc64m6oRNCIKgkhMrUOTnUUF3v5MfS8eFkg"
# Sheet2 を確実に読み込むための設定
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet2"

def get_data():
    """スプレッドシートからデータを安全に読み込む"""
    try:
        # スプレッドシートをCSV形式で読み込み
        df = pd.read_csv(SHEET_URL)
        # 列名の前後の空白を削除
        df.columns = df.columns.str.strip()
        # 空のセルを「未設定」で埋める
        return df.fillna("未設定")
    except Exception as e:
        print(f"DEBUG ERROR: {e}")
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
        復興支援ポータル
    </nav>
    <div class="max-w-md mx-auto px-4">
        {% block content %}{% endblock %}
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    df = get_data()
    if df is None or df.empty:
        return "データの読み込みに失敗しました。スプレッドシートの共有設定と、シート名が『Sheet2』であることを確認してください。"
    
    # スプレッドシートの最初のデータ行を取得
    row = df.iloc[0]
    
    # 項目を安全に取得（スプレッドシートの項目名に合わせる）
    shop = {
        "id": row.get('id', 'なし'),
        "name": row.get('name', '店名未設定'),
        "image_url": row.get('image_url', ''),
        "status": row.get('status', '不明'),
        "message": row.get('message', ''),
        "recommendation": row.get('recommendation', 'なし'),
        "ec_url": row.get('ec_url', '#'),
        "map_url": row.get('map_url', '#')
    }
    
    content = """
    {% extends "layout" %}
    {% block content %}
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
    {% endblock %}
    """
    return render_template_string(LAYOUT.replace('{% block content %}{% endblock %}', content), shop=shop)

if __name__ == '__main__':
    app.run()
