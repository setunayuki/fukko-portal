import pandas as pd
from flask import Flask, render_template_string, request, redirect, url_for
import datetime

app = Flask(__name__)

# --- 設定：スプレッドシート連携 ---
SHEET_ID = "1Y4o_J3SjSFaFqQadOGP5l9i1SpLoOI8c3uYmdij_TMY"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet1"

def get_data():
    """データを読み込み、空のセルがあってもエラーにしない処理"""
    try:
        df = pd.read_csv(SHEET_URL)
        df = df.fillna("未設定") # 空欄があれば「未設定」と表示させる
        return df
    except Exception as e:
        print(f"DEBUG ERROR: {e}")
        return pd.DataFrame()

# コメント保存用
comments_list = []

# 共通のデザイン設定
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
            <a href="/" class="font-bold text-lg">復興支援ポータル</a>
            <div class="flex gap-3 text-xs">
                <a href="/" class="underline">支援者用</a>
                <a href="/admin" class="bg-blue-800 px-2 py-1 rounded">事業者用</a>
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
        return "スプレッドシートが読み込めません。共有設定を確認してください。"
    
    # スプレッドシートの全項目(id, name, status等)を辞書にする
    shop = df.iloc[0].to_dict()
    
    content = """
    {% extends "layout" %}
    {% block content %}
    <div class="bg-white rounded-2xl shadow-sm border overflow-hidden mb-6">
        <img src="{{ shop.image_url }}" class="w-full h-52 object-cover">
        <div class="p-6">
            <div class="flex justify-between items-center mb-3">
                <h1 class="text-xl font-bold">{{ shop.name }}</h1>
                <span class="text-[10px] px-2 py-1 rounded font-bold bg-emerald-100 text-emerald-600 border border-emerald-200">
                    {{ shop.status }}
                </span>
            </div>
            <p class="text-sm text-slate-600 mb-6">{{ shop.message }}</p>
            <div class="bg-blue-50 p-4 rounded-xl mb-6 text-sm">
                <p class="font-bold text-blue-800 mb-1">✨ おすすめ</p>
                <p>{{ shop.recommendation }}</p>
            </div>
            <div class="grid grid-cols-2 gap-3">
                <a href="{{ shop.map_url }}" target="_blank" class="bg-slate-100 text-center py-3 rounded-xl font-bold text-sm">地図</a>
                <a href="{{ shop.ec_url }}" target="_blank" class="bg-blue-600 text-white text-center py-3 rounded-xl font-bold text-sm">通販</a>
            </div>
        </div>
    </div>

    <h2 class="font-bold mb-4">応援コメント ({{ comments|length }}件)</h2>
    <div class="space-y-3 mb-6">
        {% for c in comments %}
        <div class="bg-white p-4 rounded-xl border shadow-sm text-sm border-l-4 border-yellow-400">
            <div class="text-yellow-500 mb-1">{% for i in range(c.rating) %}★{% endfor %}</div>
            <p>{{ c.content }}</p>
            <p class="text-[10px] text-slate-400 mt-1">{{ c.created_at }}</p>
        </div>
        {% endfor %}
    </div>

    <form action="/comment" method="POST" class="bg-white p-6 rounded-2xl border">
        <p class="text-sm font-bold mb-3">応援を送る</p>
        <select name="rating" class="w-full border p-2 mb-2 rounded text-sm">
            <option value="5">★★★★★</option><option value="3">★★★</option><option value="1">★</option>
        </select>
        <textarea name="content" class="w-full border p-2 mb-2 rounded text-sm" placeholder="メッセージ" required></textarea>
        <button class="w-full bg-slate-800 text-white py-2 rounded font-bold">投稿する</button>
    </form>
    {% endblock %}
    """
    return render_template_string(LAYOUT.replace('{% block content %}{% endblock %}', content), shop=shop, comments=comments_list)

@app.route('/comment', methods=['POST'])
def post_comment():
    new_c = {
        "rating": int(request.form.get('rating')),
        "content": request.form.get('content'),
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    comments_list.insert(0, new_c)
    return redirect(url_for('index'))

@app.route('/admin')
def admin():
    return render_template_string(LAYOUT.replace('{% block content %}{% endblock %}', """
    {% extends "layout" %}
    {% block content %}
    <h1 class="text-xl font-bold mb-4">事業者用管理パネル</h1>
    <div class="bg-white p-8 rounded-2xl border text-center">
        <p class="text-sm mb-6">スプレッドシートで内容を書き換えてください</p>
        <a href="https://docs.google.com/spreadsheets/d/{{ sheet_id }}/edit" target="_blank" class="block w-full bg-emerald-600 text-white py-3 rounded font-bold">スプレッドシートを開く</a>
    </div>
    {% endblock %}
    """), sheet_id=SHEET_ID)

if __name__ == '__main__':
    app.run(debug=True)
