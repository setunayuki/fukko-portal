import pandas as pd
from flask import Flask, render_template_string

app = Flask(__name__)

# --- 設定：あなたのスプレッドシートID ---
SHEET_ID = "1Y4o_J3SjSFaFqQadOGP5l9i1SpLoOI8c3uYmdij_TMY"
# Sheet1を確実に指定し、CSV形式で読み込みます
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet1"

def get_data():
    try:
        # スプレッドシートを読み込み
        df = pd.read_csv(SHEET_URL)
        # 列名の前後の余計な空白を消す
        df.columns = df.columns.str.strip()
        return df.fillna("未設定")
    except Exception as e:
        print(f"ERROR: {e}")
        return None

LAYOUT = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <title>復興支援ポータル</title>
</head>
<body class="bg-slate-50 min-h-screen text-slate-800 pb-10">
    <nav class="bg-blue-700 text-white p-4 mb-6 shadow-md font-bold text-center">復興支援ポータル</nav>
    <div class="max-w-md mx-auto px-4">{% block content %}{% endblock %}</div>
</body>
</html>
"""

@app.route('/')
def index():
    df = get_data()
    if df is None or df.empty:
        return "データの読み込みに失敗しました。共有設定を確認してください。"
    
    # 列の名前を直接指定して安全に取り出す設定
    row = df.iloc[0]
    
    # もしスプレッドシートの項目名が違っていてもエラーにならないように保護
    def get_val(col_name):
        return row.get(col_name, "設定なし")

    shop = {
        "name": get_val('name'),
        "image_url": get_val('image_url'),
        "status": get_val('status'),
        "message": get_val('message'),
        "recommendation": get_val('recommendation'),
        "ec_url": get_val('ec_url'),
        "map_url": get_val('map_url')
    }
    
    content = """
    {% extends "layout" %}
    {% block content %}
    <div class="bg-white rounded-2xl shadow-sm border overflow-hidden">
        <img src="{{ shop.image_url }}" class="w-full h-48 object-cover" onerror="this.src='https://via.placeholder.com/400x200?text=No+Image'">
        <div class="p-6">
            <div class="flex justify-between items-center mb-4">
                <h1 class="text-xl font-bold">{{ shop.name }}</h1>
                <span class="text-xs px-2 py-1 rounded bg-emerald-100 text-emerald-600 font-bold border border-emerald-200">{{ shop.status }}</span>
            </div>
            <p class="text-sm text-slate-600 mb-6 leading-relaxed">{{ shop.message }}</p>
            <div class="bg-blue-50 p-4 rounded-xl mb-6 text-xs border border-blue-100">
                <p class="font-bold text-blue-800 mb-1">✨ おすすめ</p><p>{{ shop.recommendation }}</p>
            </div>
            <div class="grid grid-cols-2 gap-3">
                <a href="{{ shop.map_url }}" target="_blank" class="bg-slate-100 text-center py-3 rounded-xl font-bold text-sm">地図</a>
                <a href="{{ shop.ec_url }}" target="_blank" class="bg-blue-600 text-white text-center py-3 rounded-xl font-bold text-sm">通販</a>
            </div>
        </div>
    </div>
    {% endblock %}
    """
    return render_template_string(LAYOUT.replace('{% block content %}{% endblock %}', content), shop=shop)

if __name__ == '__main__':
    app.run()
