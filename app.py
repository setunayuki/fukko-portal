import pandas as pd
from flask import Flask, render_template_string

app = Flask(__name__)

# --- 設定：あなたのスプレッドシートID ---
SHEET_ID = "1Y4o_J3SjSFaFqQadOGP5l9i1SpLoOI8c3uYmdij_TMY"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet1"

def get_data():
    try:
        # 確実にCSVとして読み込み、列名の空白を自動除去
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip()
        return df.fillna("未設定")
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        return None

LAYOUT = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <title>復興支援ポータル</title>
</head>
<body class="bg-slate-50 min-h-screen text-slate-800">
    <nav class="bg-blue-700 text-white p-4 mb-6 shadow-md"><div class="max-w-md mx-auto font-bold">復興支援ポータル</div></nav>
    <div class="max-w-md mx-auto px-4">{% block content %}{% endblock %}</div>
</body>
</html>
"""

@app.route('/')
def index():
    df = get_data()
    
    if df is None:
        return "【エラー】スプレッドシートにアクセスできません。共有設定が「リンクを知っている全員：編集者」になっているか確認してください。"
    if df.empty:
        return "【エラー】スプレッドシートのデータが空です。2行目に入力があるか確認してください。"
    
    # 項目名を直接指定して取得。もし名前が違ってもエラーで止まらないように保護
    row = df.iloc[0]
    shop = {
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
        <img src="{{ shop.image_url }}" class="w-full h-48 object-cover" onerror="this.src='https://via.placeholder.com/400x200?text=No+Image'">
        <div class="p-6">
            <div class="flex justify-between items-center mb-4">
                <h1 class="text-xl font-bold text-slate-900">{{ shop.name }}</h1>
                <span class="text-xs px-2 py-1 rounded bg-emerald-100 text-emerald-600 font-bold border border-emerald-200">{{ shop.status }}</span>
            </div>
            <p class="text-sm text-slate-600 mb-6 leading-relaxed">{{ shop.message }}</p>
            <div class="bg-blue-50 p-4 rounded-xl mb-6 text-xs border border-blue-100">
                <p class="font-bold text-blue-800 mb-1">✨ おすすめ</p><p>{{ shop.recommendation }}</p>
            </div>
            <div class="grid grid-cols-2 gap-3">
                <a href="{{ shop.map_url }}" target="_blank" class="bg-slate-100 text-center py-3 rounded-xl font-bold text-sm text-slate-700">地図</a>
                <a href="{{ shop.ec_url }}" target="_blank" class="bg-blue-600 text-white text-center py-3 rounded-xl font-bold text-sm shadow-md">通販</a>
            </div>
        </div>
    </div>
    {% endblock %}
    """
    return render_template_string(LAYOUT.replace('{% block content %}{% endblock %}', content), shop=shop)

if __name__ == '__main__':
    app.run()
