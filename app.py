import pandas as pd
from flask import Flask, render_template_string, request, redirect, url_for
import datetime

app = Flask(__name__)

# --- 設定：スプレッドシート連携 ---
SHEET_ID = "1Y4o_J3SjSFaFqQadOGP5l9i1SpLoOI8c3uYmdij_TMY"
# タブ名 Sheet1 を確実に指定して読み込むURL
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet1"

# 応援コメントを保存するリスト (無料版Renderでは再起動でリセットされます)
# 永続化したい場合はスプレッドシートの別のタブを使う必要がありますが、まずはこれで起動させます
comments_data = []

def get_shop_data():
    """スプレッドシートから店舗情報を取得"""
    try:
        # スプレッドシートから最新データを読み込み
        df = pd.read_csv(SHEET_URL)
        # 1行目(index 0)のデータを辞書形式で取得
        return df.iloc[0].to_dict()
    except Exception as e:
        print(f"DEBUG ERROR: {e}")
        return None

# --- HTML 共通レイアウト ---
LAYOUT = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <title>復興支援ポータル</title>
</head>
<body class="bg-slate-50 min-h-screen text-slate-800 pb-10">
    <nav class="bg-blue-700 text-white shadow-md mb-6 sticky top-0 z-50">
        <div class="max-w-md mx-auto flex justify-between items-center p-4">
            <a href="/" class="font-bold text-lg tracking-tight">復興支援ポータル</a>
            <div class="flex gap-4 items-center">
                <a href="/" class="text-xs {% if request.path == '/' %}underline font-bold{% endif %}">支援者用</a>
                <a href="/admin" class="text-xs bg-blue-800 px-3 py-1 rounded-full">事業者用</a>
            </div>
        </div>
    </nav>
    <div class="max-w-md mx-auto px-4">
        {% block content %}{% endblock %}
    </div>
</body>
</html>
"""

# --- 支援者用画面 ---
@app.route('/')
def index():
    shop = get_shop_data()
    if not shop:
        return "スプレッドシートの読み込みに失敗しました。1行目の項目名や共有設定を確認してください。"

    content = """
    {% extends "layout" %}
    {% block content %}
    <div class="bg-white rounded-2xl shadow-sm border overflow-hidden mb-8">
        <img src="{{ shop.image_url }}" class="w-full h-52 object-cover">
        <div class="p-6">
            <div class="flex justify-between items-start mb-3">
                <h1 class="text-2xl font-bold">{{ shop.name }}</h1>
                <span class="text-[10px] px-2 py-1 rounded-full font-bold bg-emerald-100 text-emerald-600 border border-emerald-200">
                    ● {{ shop.status }}
                </span>
            </div>
            <p class="text-sm text-slate-600 leading-relaxed mb-6">{{ shop.message }}</p>
            
            <div class="bg-blue-50 border border-blue-100 p-4 rounded-xl mb-6 text-sm">
                <p class="font-bold text-blue-800 mb-1">✨ おすすめ</p>
                <p class="text-slate-700">{{ shop.recommendation }}</p>
            </div>
            
            <div class="grid grid-cols-2 gap-3">
                <a href="{{ shop.map_url }}" target="_blank" class="bg-slate-100 text-slate-700 text-center py-3 rounded-xl font-bold text-sm">地図を表示</a>
                <a href="{{ shop.ec_url }}" target="_blank" class="bg-blue-600 text-white text-center py-3 rounded-xl font-bold text-sm shadow-md">通販で購入</a>
            </div>
        </div>
    </div>

    <h2 class="font-bold text-lg mb-4">応援コメント ({{ comments|length }}件)</h2>
    <div class="space-y-4 mb-8">
        {% for c in comments %}
        <div class="bg-white p-4 rounded-xl border-l-4 border-yellow-400 shadow-sm text-sm">
            <div class="text-yellow-500 font-bold mb-1">{% for i in range(c.rating) %}★{% endfor %}</div>
            <p class="text-slate-700">{{ c.content }}</p>
            <p class="text-[10px] text-slate-400 mt-2">{{ c.created_at }}</p>
        </div>
        {% endfor %}
    </div>

    <form action="/comment" method="POST" class="bg-white p-6 rounded-2xl border shadow-sm">
        <h3 class="font-bold text-sm mb-4">応援を送る</h3>
        <select name="rating" class="w-full border p-2 mb-3 rounded-lg text-sm bg-slate-50">
            <option value="5">★★★★★ (最高！)</option>
            <option value="3">★★★</option>
            <option value="1">★</option>
        </select>
        <textarea name="content" class="w-full border p-2 mb-3 rounded-lg text-sm bg-slate-50" placeholder="応援メッセージを入力..." required></textarea>
        <button class="w-full bg-slate-800 text-white py-3 rounded-xl font-bold">投稿する</button>
    </form>
    {% endblock %}
    """
    return render_template_string(LAYOUT.replace('{% block content %}{% endblock %}', content), shop=shop, comments=comments_data)

# --- コメント投稿処理 ---
@app.route('/comment', methods=['POST'])
def post_comment():
    new_c = {
        "rating": int(request.form.get('rating')),
        "content": request.form.get('content'),
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    comments_data.insert(0, new_c)
    return redirect(url_for('index'))

# --- 事業者用画面 ---
@app.route('/admin')
def admin():
    shop = get_shop_data()
    content = """
    {% extends "layout" %}
    {% block content %}
    <div class="mb-6">
        <h1 class="text-xl font-bold">事業者用管理パネル</h1>
        <p class="text-xs text-slate-500">店舗ID: {{ shop.id }}</p>
    </div>
    <div class="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm text-center">
        <p class="text-sm text-slate-600 mb-6">店舗情報の編集は下のスプレッドシートから直接行ってください。</p>
        <a href="https://docs.google.com/spreadsheets/d/{{ sheet_id }}/edit" target="_blank" 
           class="block w-full bg-emerald-600 text-white py-4 rounded-xl font-bold shadow-lg">
            スプレッドシートを開く
        </a>
    </div>
    {% endblock %}
    """
    return render_template_string(LAYOUT.replace('{% block content %}{% endblock %}', content), shop=shop, sheet_id=SHEET_ID)

if __name__ == '__main__':
    app.run(debug=True)
