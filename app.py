import pandas as pd
from flask import Flask, render_template_string, request, redirect, url_for
import datetime

app = Flask(__name__)

# --- 設定：あなたのスプレッドシートID ---
SHEET_ID = "1Y4o_J3SjSFaFqQadOGP5l9i1SpLoOI8c3uYmdij_TMY"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet1"

def get_data():
    """データを安全に読み込む（エラー回避機能付き）"""
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip() # 列名の余計な空白を削除
        return df.fillna("なし") # 空欄を「なし」で埋めてエラーを防止
    except Exception as e:
        print(f"DEBUG ERROR: {e}")
        return pd.DataFrame()

comments_list = []

LAYOUT = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <title>復興支援ポータル</title>
</head>
<body class="bg-slate-50 min-h-screen text-slate-800 pb-10">
    <nav class="bg-blue-700 text-white shadow-md mb-6 p-4">
        <div class="max-w-md mx-auto flex justify-between items-center">
            <a href="/" class="font-bold">復興支援ポータル</a>
            <div class="flex gap-4 text-xs">
                <a href="/">支援者用</a>
                <a href="/admin" class="bg-blue-800 px-3 py-1 rounded-full">事業者用</a>
            </div>
        </div>
    </nav>
    <div class="max-w-md mx-auto px-4">{% block content %}{% endblock %}</div>
</body>
</html>
"""

@app.route('/')
def index():
    df = get_data()
    if df.empty:
        return "スプレッドシートを読み込めません。共有設定が「編集者」になっているか確認してください。"
    
    # どんな列名になっていても、順番でデータを取得するように修正
    row = df.iloc[0]
    shop = {
        "name": row[1] if len(row) > 1 else "店名未設定",
        "image_url": row[2] if len(row) > 2 else "",
        "status": row[3] if len(row) > 3 else "不明",
        "message": row[4] if len(row) > 4 else "",
        "recommendation": row[5] if len(row) > 5 else "なし",
        "ec_url": row[6] if len(row) > 6 else "#",
        "map_url": row[7] if len(row) > 7 else "#"
    }
    
    content = """
    {% extends "layout" %}
    {% block content %}
    <div class="bg-white rounded-2xl shadow-sm border overflow-hidden mb-6">
        <img src="{{ shop.image_url }}" class="w-full h-52 object-cover" onerror="this.src='https://via.placeholder.com/400x250?text=No+Image'">
        <div class="p-6">
            <div class="flex justify-between items-center mb-4">
                <h1 class="text-xl font-bold">{{ shop.name }}</h1>
                <span class="text-[10px] px-2 py-1 rounded font-bold bg-emerald-100 text-emerald-600 border border-emerald-200">{{ shop.status }}</span>
            </div>
            <p class="text-sm text-slate-600 mb-6 leading-relaxed">{{ shop.message }}</p>
            <div class="bg-blue-50 p-4 rounded-xl mb-6 text-sm border border-blue-100">
                <p class="font-bold text-blue-800 mb-1">✨ おすすめ</p>
                <p>{{ shop.recommendation }}</p>
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

@app.route('/admin')
def admin():
    return render_template_string(LAYOUT.replace('{% block content %}{% endblock %}', """
    {% extends "layout" %}
    {% block content %}
    <h1 class="text-xl font-bold mb-6 text-center">事業者管理画面</h1>
    <div class="bg-white p-8 rounded-2xl border text-center shadow-sm">
        <p class="text-sm mb-6 text-slate-600">Googleスプレッドシートを編集して保存してください。</p>
        <a href="https://docs.google.com/spreadsheets/d/{{ sheet_id }}/edit" target="_blank" class="block w-full bg-emerald-600 text-white py-4 rounded-xl font-bold">スプレッドシートを開く</a>
    </div>
    {% endblock %}
    """), sheet_id=SHEET_ID)

if __name__ == '__main__':
    app.run(debug=True)
