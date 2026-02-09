import pandas as pd
from flask import Flask, render_template_string, request, redirect, url_for
import datetime

app = Flask(__name__)

# --- 1. 設定：スプレッドシート連携 ---
SHEET_ID = "1Y4o_J3SjSFaFqQadOGP5l9i1SpLoOI8c3uYmdij_TMY"
# 最初のシート「Sheet1」を確実に読み込むURL
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet1"

def get_data():
    """スプレッドシートからデータを取得し、エラーを安全に処理する"""
    try:
        # スプレッドシートをCSV形式で読み込み
        df = pd.read_csv(SHEET_URL)
        # 空のセル(NaN)を空文字に変換してエラーを防止
        df = df.fillna("")
        return df
    except Exception as e:
        print(f"DEBUG ERROR: {e}")
        return pd.DataFrame()

# コメント保存用のリスト（Render再起動でリセットされますが、まずは表示を優先）
comments_list = []

# --- 2. 共通レイアウト (ナビゲーション付き) ---
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
            <a href="/" class="font-bold text-lg">復興支援ポータル</a>
            <div class="flex gap-4 items-center">
                <a href="/" class="text-xs {% if request.path == '/' %}underline font-bold{% endif %}">支援者用</a>
                <a href="/admin" class="text-xs bg-blue-800 px-3 py-1 rounded-full">事業者用</a>
            </div>
        </div>
    </nav>
    <div class="max-w-md mx-auto px-4">{% block content %}{% endblock %}</div>
</body>
</html>
"""

# --- 3. ルーティング処理 ---

@app.route('/')
def index():
    df = get_data()
    if df.empty:
        return "データの読み込みに失敗しました。スプレッドシートのID、共有設定(編集者)、タブ名(Sheet1)を再確認してください。"
    
    # 最初の行(index 0)を店舗データとして取得
    shop = df.iloc[0].to_dict()
    
    content = """
    {% extends "layout" %}
    {% block content %}
    <div class="bg-white rounded-2xl shadow-sm border overflow-hidden mb-6">
        <img src="{{ shop.image_url }}" class="w-full h-52 object-cover">
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
                <a href="{{ shop.map_url }}" target="_blank" class="bg-slate-100 text-center py-3 rounded-xl font-bold text-sm hover:bg-slate-200">地図</a>
                <a href="{{ shop.ec_url }}" target="_blank" class="bg-blue-600 text-white text-center py-3 rounded-xl font-bold text-sm shadow-md">通販サイト</a>
            </div>
        </div>
    </div>

    <h2 class="font-bold text-lg mb-4">応援コメント ({{ comments|length }}件)</h2>
    <div class="space-y-4 mb-8">
        {% for c in comments %}
        <div class="bg-white p-4 rounded-xl border shadow-sm text-sm border-l-4 border-yellow-400">
            <div class="text-yellow-500 font-bold mb-1">{% for i in range(c.rating) %}★{% endfor %}</div>
            <p class="text-slate-700">{{ c.content }}</p>
            <p class="text-[10px] text-slate-400 mt-2">{{ c.created_at }}</p>
        </div>
        {% endfor %}
    </div>

    <form action="/comment" method="POST" class="bg-white p-6 rounded-2xl border shadow-sm mb-10">
        <h3 class="font-bold text-sm mb-4 text-slate-500 uppercase tracking-wider">応援メッセージを送る</h3>
        <div class="mb-4">
            <label class="block text-xs font-bold text-slate-400 mb-1">星評価</label>
            <select name="rating" class="w-full border p-2 rounded-lg text-sm bg-slate-50">
                <option value="5">★★★★★ (最高！)</option>
                <option value="4">★★★★</option>
                <option value="3">★★★</option>
                <option value="2">★★</option>
                <option value="1">★</option>
            </select>
        </div>
        <div class="mb-4">
            <label class="block text-xs font-bold text-slate-400 mb-1">メッセージ</label>
            <textarea name="content" class="w-full border p-2 rounded-lg text-sm bg-slate-50" rows="3" placeholder="応援メッセージを入力してください" required></textarea>
        </div>
        <button class="w-full bg-slate-800 text-white py-3 rounded-xl font-bold hover:bg-slate-900 transition shadow-lg">投稿する</button>
    </form>
    {% endblock %}
    """
    return render_template_string(LAYOUT.replace('{% block content %}{% endblock %}', content), shop=shop, comments=comments_list)

@app.route('/comment', methods=['POST'])
def post_comment():
    # フォームから受け取ったデータを保存
    new_c = {
        "rating": int(request.form.get('rating')),
        "content": request.form.get('content'),
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    comments_list.insert(0, new_c) # 新しいコメントを一番上に
    return redirect(url_for('index'))

@app.route('/admin')
def admin():
    # 事業者用画面
    return render_template_string(LAYOUT.replace('{% block content %}{% endblock %}', """
    {% extends "layout" %}
    {% block content %}
    <h1 class="text-xl font-bold mb-6">事業者用管理パネル</h1>
    <div class="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm text-center">
        <p class="text-sm mb-8 text-slate-600 leading-relaxed">情報の更新は、以下のGoogleスプレッドシートを編集してください。変更は即座に公開サイトへ反映されます。</p>
        <a href="https://docs.google.com/spreadsheets/d/{{ sheet_id }}/edit" target="_blank" 
           class="block w-full bg-emerald-600 text-white py-4 rounded-xl font-bold shadow-lg hover:bg-emerald-700 transition">
            スプレッドシートを開いて編集
        </a>
    </div>
    {% endblock %}
    """), sheet_id=SHEET_ID)

if __name__ == '__main__':
    app.run(debug=True)
