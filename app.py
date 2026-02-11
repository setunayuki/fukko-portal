import pandas as pd
from flask import Flask, render_template_string, request, redirect, url_for
import os
import uuid # ID自動生成用

app = Flask(__name__)

# --- 設定 ---
SHEET_ID = "1incBINNVhc64m6oRNCIKgkhMrUOTnUUF3v5MfS8eFkg"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet2"

def get_all_data():
    try:
        df = pd.read_csv(SHEET_URL, header=1)
        df.columns = df.columns.str.strip()
        mapping = {
            'ID': 'id', '店名': 'name', '画像URL': 'image_url',
            '状況': 'status', 'メッセージ': 'message',
            'おすすめ': 'recommendation', '通販URL': 'ec_url', '地図URL': 'map_url'
        }
        df = df.rename(columns=mapping)
        df = df.dropna(subset=['id', 'name'])
        df['id'] = df['id'].astype(str).str.replace('.0', '', regex=False)
        return df.fillna("未設定")
    except:
        return pd.DataFrame()

# --- HTML デザイン ---
LAYOUT = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <title>復興支援ポータル</title>
    <style>
        body { background-color: #fffaf0; font-family: 'sans-serif'; }
        .status-営業中 { background-color: #d1fae5; color: #065f46; border: 1px solid #6ee7b7; }
        .status-営業予定 { background-color: #fef3c7; color: #92400e; border: 1px solid #fcd34d; }
        .status-準備中 { background-color: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; }
    </style>
</head>
<body class="min-h-screen pb-24">
    <nav class="bg-orange-600 text-white p-6 shadow-lg text-center mb-8">
        <h1 class="text-2xl font-bold"><a href="/">復興支援ポータル</a></h1>
    </nav>

    <div class="max-w-md mx-auto px-4">
        {% if mode == 'form' %}
        <div class="bg-white p-8 rounded-3xl shadow-xl border border-orange-100">
            <h2 class="text-xl font-bold mb-6 text-orange-600">事業者向け：新規登録</h2>
            <form action="/submit" method="POST" class="space-y-4">
                <div>
                    <label class="block text-xs font-bold text-slate-400 mb-1">店名</label>
                    <input type="text" name="name" required class="w-full p-3 rounded-xl bg-slate-50 border focus:border-orange-500 outline-none">
                </div>
                <div>
                    <label class="block text-xs font-bold text-slate-400 mb-1">営業状況</label>
                    <select name="status" class="w-full p-3 rounded-xl bg-slate-50 border">
                        <option value="営業中">営業中</option>
                        <option value="営業予定">営業予定</option>
                        <option value="準備中">準備中</option>
                    </select>
                </div>
                <div>
                    <label class="block text-xs font-bold text-slate-400 mb-1">メッセージ</label>
                    <textarea name="message" class="w-full p-3 rounded-xl bg-slate-50 border"></textarea>
                </div>
                <div>
                    <label class="block text-xs font-bold text-slate-400 mb-1">画像URL</label>
                    <input type="url" name="image_url" class="w-full p-3 rounded-xl bg-slate-50 border">
                </div>
                <button type="submit" class="w-full py-4 bg-orange-500 text-white rounded-2xl font-bold shadow-lg hover:bg-orange-600 transition">
                    この内容で登録する
                </button>
            </form>
        </div>

        {% elif mode == 'success' %}
        <div class="bg-white p-8 rounded-3xl shadow-xl text-center">
            <div class="text-5xl mb-4">✅</div>
            <h2 class="text-xl font-bold mb-2">登録が完了しました</h2>
            <p class="text-sm text-slate-500 mb-6">あなたの店舗IDはこちらです：</p>
            <div class="flex items-center justify-center gap-2 mb-8">
                <code id="id-code" class="bg-slate-100 px-4 py-2 rounded-lg font-mono font-bold text-orange-600">{{ new_id }}</code>
                <button onclick="copyId()" class="text-xs bg-orange-100 text-orange-600 px-3 py-2 rounded-lg font-bold">コピー</button>
            </div>
            <a href="/" class="text-orange-500 font-bold">トップページへ戻る</a>
        </div>
        <script>
            function copyId() {
                const code = document.getElementById('id-code').innerText;
                navigator.clipboard.writeText(code);
                alert('IDをコピーしました！編集者へ伝えてください。');
            }
        </script>

        {% elif shop %}
        <div class="bg-white rounded-3xl overflow-hidden shadow-xl border-t-8 border-orange-500">
            <img src="{{ shop.image_url }}" class="w-full h-60 object-cover" onerror="this.src='https://via.placeholder.com/400x250?text=No+Image'">
            <div class="p-8">
                <div class="flex justify-between items-start mb-4">
                    <h2 class="text-3xl font-black text-slate-900">{{ shop.name }}</h2>
                    <span class="px-3 py-1 rounded-full font-bold text-xs status-{{ shop.status }}">{{ shop.status }}</span>
                </div>
                <p class="bg-orange-50 p-4 rounded-2xl italic text-slate-700 mb-6 border-l-4 border-orange-200">「{{ shop.message }}」</p>
                <div class="grid grid-cols-1 gap-4">
                    <a href="{{ shop.ec_url }}" target="_blank" class="flex items-center justify-center bg-orange-500 text-white py-4 rounded-2xl font-bold text-lg shadow-lg shadow-orange-100">🛒 通販サイトへ</a>
                </div>
                <div class="mt-8 pt-6 border-t text-center text-xs text-slate-400">
                    店舗ID: {{ shop.id }}
                </div>
            </div>
        </div>

        {% else %}
        <div class="space-y-4">
            {% for s in all_shops %}
            <a href="/shop/{{ s.id }}" class="flex items-center p-4 bg-white rounded-2xl shadow-md border border-orange-50 group transition hover:-translate-y-1">
                <div class="w-16 h-16 rounded-xl overflow-hidden shrink-0 border"><img src="{{ s.image_url }}" class="w-full h-full object-cover" onerror="this.src='https://via.placeholder.com/100'"></div>
                <div class="ml-4 flex-1">
                    <span class="text-[9px] px-2 py-0.5 rounded-full font-bold status-{{ s.status }}">{{ s.status }}</span>
                    <h3 class="text-lg font-bold text-slate-800 group-hover:text-orange-600">{{ s.name }}</h3>
                </div>
                <div class="text-orange-200 group-hover:translate-x-1 transition-transform">▶︎</div>
            </a>
            {% endfor %}
        </div>
        {% endif %}
    </div>

    <div class="fixed bottom-6 right-6 z-50">
        <a href="/add" class="flex items-center justify-center w-16 h-16 bg-slate-800 text-white rounded-full shadow-2xl hover:scale-110 active:scale-95 transition transform group">
            <span class="text-3xl">＋</span>
        </a>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    df = get_all_data()
    all_shops = df.to_dict(orient='records') if not df.empty else []
    return render_template_string(LAYOUT, mode='list', all_shops=all_shops)

@app.route('/shop/<shop_id>')
def render_shop(shop_id):
    df = get_all_data()
    row = df[df['id'] == str(shop_id)]
    if row.empty: abort(404)
    return render_template_string(LAYOUT, mode='detail', shop=row.iloc[0].to_dict())

@app.route('/add')
def add_form():
    return render_template_string(LAYOUT, mode='form')

@app.route('/submit', methods=['POST'])
def submit():
    # IDを自動生成（先頭4文字を使用）
    new_id = str(uuid.uuid4())[:4].upper()
    # ここで本来はスプレッドシートAPIを叩きますが、
    # 今回は仕組み上、管理者へIDを伝えて手動または自動連携させる流れを想定しています。
    # ※直接書き込みにはGoogle APIの設定が必要ですが、まずは画面の完成を優先しました。
    return render_template_string(LAYOUT, mode='success', new_id=new_id)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
