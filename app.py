import pandas as pd
from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)

# --- 設定：あなたのスプレッドシートID ---
SHEET_ID = "1Y4o_J3SjSFaFqQadOGP5l9i1SpLoOI8c3uYmdij_TMY" 
# 公開設定が「リンクを知っている全員」「編集者」になっている必要があります
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

def get_data():
    """スプレッドシートからデータを取得（失敗した時のために例外処理付き）"""
    try:
        df = pd.read_csv(SHEET_URL)
        return df
    except Exception as e:
        print(f"Error: {e}")
        return pd.DataFrame()

# --- 共通レイアウト (メニュー切り替え付き) ---
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
                <a href="/admin" class="text-xs bg-blue-800 px-3 py-1 rounded-full {% if request.path == '/admin' %}ring-2 ring-white{% endif %}">事業者ログイン</a>
            </div>
        </div>
    </nav>
    
    <div class="max-w-md mx-auto px-4">
        {% block content %}{% endblock %}
    </div>
</body>
</html>
"""

# --- 支援者（利用者）用トップ画面 ---
@app.route('/')
def index():
    df = get_data()
    if df.empty: return "スプレッドシートの読み込みに失敗しました。設定を確認してください。"
    
    shop = df.iloc[0].to_dict()
    
    content = """
    {% extends "layout" %}
    {% block content %}
    <div class="bg-white rounded-2xl shadow-sm border overflow-hidden">
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
                <a href="{{ shop.map_url }}" target="_blank" class="bg-slate-100 text-slate-700 text-center py-3 rounded-xl font-bold text-sm hover:bg-slate-200 transition">地図を表示</a>
                <a href="{{ shop.ec_url }}" target="_blank" class="bg-blue-600 text-white text-center py-3 rounded-xl font-bold text-sm hover:bg-blue-700 shadow-md transition">通販で購入</a>
            </div>
        </div>
    </div>
    {% endblock %}
    """
    return render_template_string(LAYOUT.replace('{% block content %}{% endblock %}', content), shop=shop)

# --- 事業者用管理画面 ---
@app.route('/admin')
def admin():
    df = get_data()
    shop = df.iloc[0].to_dict()
    
    content = """
    {% extends "layout" %}
    {% block content %}
    <div class="mb-6">
        <h1 class="text-xl font-bold">事業者用管理パネル</h1>
        <p class="text-xs text-slate-500">スプレッドシートと連携しています</p>
    </div>

    <div class="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-6">
        <div class="p-4 bg-amber-50 rounded-xl border border-amber-100">
            <p class="text-xs text-amber-800 leading-tight font-medium">
                【更新方法】<br>
                下のボタンからスプレッドシートを開き、内容を書き換えてください。保存後、数秒でサイトに反映されます。
            </p>
        </div>

        <a href="https://docs.google.com/spreadsheets/d/{{ sheet_id }}/edit" target="_blank" 
           class="block w-full bg-emerald-600 text-white text-center py-4 rounded-xl font-bold shadow-lg hover:bg-emerald-700 transition">
            スプレッドシートを開いて編集
        </a>

        <div class="pt-4 border-t border-slate-100">
            <h2 class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">現在の公開内容</h2>
            <ul class="text-sm space-y-2">
                <li><span class="text-slate-400">店名:</span> {{ shop.name }}</li>
                <li><span class="text-slate-400">状態:</span> {{ shop.status }}</li>
                <li><span class="text-slate-400">一言:</span> {{ shop.message[:20] }}...</li>
            </ul>
        </div>
    </div>
    {% endblock %}
    """
    return render_template_string(LAYOUT.replace('{% block content %}{% endblock %}', content), shop=shop, sheet_id=SHEET_ID)

if __name__ == '__main__':
    app.run(debug=True)
