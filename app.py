import pandas as pd
from flask import Flask, render_template_string, request, abort
import os
import uuid

app = Flask(__name__)

# --- 設定 ---
SHEET_ID = "1incBINNVhc64m6oRNCIKgkhMrUOTnUUF3v5MfS8eFkg"
# 読み込みを速めるため、不要なパラメータを削ったCSV用URL
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1191908203"

def get_all_data():
    try:
        # タイムアウト対策：2秒以内に読み込めない場合は諦める設定
        df = pd.read_csv(SHEET_URL, header=1, timeout=2)
        df.columns = df.columns.str.strip()
        
        mapping = {
            'ID': 'id', '店名': 'name', '画像URL': 'image_url',
            '状況': 'status', 'メッセージ': 'message',
            'おすすめ': 'recommendation', '通販URL': 'ec_url', '地図URL': 'map_url'
        }
        df = df.rename(columns=mapping)
        
        # 必要な列だけに絞って軽量化
        valid_cols = [c for c in mapping.values() if c in df.columns]
        df = df[valid_cols].dropna(subset=['name'])
        
        if 'id' in df.columns:
            df['id'] = df['id'].astype(str).str.replace('.0', '', regex=False).str.strip()
        
        return df.fillna("未設定")
    except Exception as e:
        print(f"Read error: {e}")
        return pd.DataFrame() # 空のデータを返してタイムアウトを防ぐ

# --- HTML デザイン（さらに軽量化） ---
LAYOUT = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <title>復興支援ポータル</title>
    <style>
        body { background-color: #fffaf0; }
        .status-営業中 { background-color: #d1fae5; color: #065f46; border: 1px solid #6ee7b7; }
        .status-営業予定 { background-color: #fef3c7; color: #92400e; border: 1px solid #fcd34d; }
        .status-準備中 { background-color: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; }
    </style>
</head>
<body class="min-h-screen text-slate-800 pb-10">
    <nav class="bg-orange-600 text-white p-6 mb-8 shadow-lg text-center font-bold text-xl">
        <a href="/">復興支援ポータル</a>
    </nav>

    <div class="max-w-md mx-auto px-4">
        {% if mode == 'form' %}
        <div class="bg-white p-8 rounded-3xl shadow-xl">
            <h2 class="text-xl font-bold mb-6 text-orange-600 text-center">新規登録フォーム</h2>
            <form action="/submit" method="POST" class="space-y-4">
                <input type="text" name="name" placeholder="店名" required class="w-full p-3 rounded-xl bg-slate-50 border outline-none">
                <select name="status" class="w-full p-3 rounded-xl bg-slate-50 border">
                    <option value="営業中">営業中</option>
                    <option value="営業予定">営業予定</option>
                    <option value="準備中">準備中</option>
                </select>
                <textarea name="message" placeholder="メッセージ" class="w-full p-3 rounded-xl bg-slate-50 border"></textarea>
                <input type="url" name="image_url" placeholder="画像URL" class="w-full p-3 rounded-xl bg-slate-50 border">
                <button type="submit" class="w-full py-4 bg-orange-500 text-white rounded-2xl font-bold shadow-lg">登録する</button>
            </form>
        </div>
        {% elif mode == 'success' %}
        <div class="bg-white p-8 rounded-3xl shadow-xl text-center">
            <h2 class="text-xl font-bold mb-4">登録を受け付けました</h2>
            <div class="flex items-center justify-center gap-2 mb-6">
                <code id="newId" class="bg-slate-100 px-4 py-2 rounded font-bold text-orange-600">{{ new_id }}</code>
                <button onclick="copyText()" class="bg-orange-100 text-orange-600 px-3 py-2 rounded text-xs font-bold">コピー</button>
            </div>
            <a href="/" class="text-orange-500 font-bold">トップページへ</a>
        </div>
        <script>function copyText(){navigator.clipboard.writeText(document.getElementById('newId').innerText);alert('IDをコピーしました！');}</script>
        {% elif shop %}
        <div class="bg-white rounded-3xl shadow-lg border-t-8 border-orange-500 overflow-hidden text-center p-8">
            <img src="{{ shop.image_url }}" class="w-full h-56 object-cover rounded-2xl mb-4" onerror="this.src='https://via.placeholder.com/400x250?text=No+Image'">
            <span class="inline-block px-3 py-1 rounded-full font-bold text-xs status-{{ shop.status }} mb-4">{{ shop.status }}</span>
            <h2 class="text-3xl font-black mb-4">{{ shop.name }}</h2>
            <p class="text-sm text-slate-600 mb-8 italic">「{{ shop.message }}」</p>
            <a href="{{ shop.ec_url }}" target="_blank" class="block w-full py-4 bg-orange-500 text-white rounded-2xl font-bold shadow-lg">🛒 通販サイト</a>
            <a href="/" class="block mt-6 text-xs text-slate-400">← 一覧に戻る</a>
        </div>
        {% else %}
        <div class="space-y-4">
            {% for s in all_shops %}
            <a href="/shop/{{ s.id }}" class="flex items-center p-4 bg-white rounded-2xl shadow-md border border-orange-50">
                <div class="w-16 h-16 rounded-xl overflow-hidden shrink-0"><img src="{{ s.image_url }}" class="w-full h-full object-cover" onerror="this.src='https://via.placeholder.com/100'"></div>
                <div class="ml-4 flex-1">
                    <span class="text-[10px] px-2 py-0.5 rounded-full font-bold status-{{ s.status }}">{{ s.status }}</span>
                    <h3 class="text-lg font-bold">{{ s.name }}</h3>
                </div>
            </a>
            {% endfor %}
        </div>
        {% endif %}
    </div>

    <a href="/add" class="fixed bottom-6 right-6 w-16 h-16 bg-slate-800 text-white rounded-full flex items-center justify-center shadow-2xl text-3xl font-light">+</a>
</body>
</html>
"""

@app.route('/')
def index():
    df = get_all_data()
    all_shops = df.to_dict(orient='records') if not df.empty else []
    return render_template_string(LAYOUT, all_shops=all_shops)

@app.route('/shop/<shop_id>')
def render_shop(shop_id):
    df = get_all_data()
    row = df[df['id'] == str(shop_id)] if not df.empty else pd.DataFrame()
    if row.empty: return redirect('/')
    return render_template_string(LAYOUT, shop=row.iloc[0].to_dict())

@app.route('/add')
def add_page():
    return render_template_string(LAYOUT, mode='form')

@app.route('/submit', methods=['POST'])
def submit():
    new_id = str(uuid.uuid4())[:4].upper()
    return render_template_string(LAYOUT, mode='success', new_id=new_id)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
