import pandas as pd
from flask import Flask, render_template_string, request
import os
import uuid

app = Flask(__name__)

# --- 設定 ---
SHEET_ID = "1incBINNVhc64m6oRNCIKgkhMrUOTnUUF3v5MfS8eFkg"
# エラー回避：URLの最後に &headers=1 を追加して確実に読み込ませる
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1191908203&headers=1"

def get_all_data():
    try:
        # タイムアウト対策：engineに'python'を指定し、安定性を高める
        df = pd.read_csv(SHEET_URL, header=1, engine='python', on_bad_lines='skip')
        df.columns = df.columns.str.strip()
        
        mapping = {
            'ID': 'id', '店名': 'name', '画像URL': 'image_url',
            '状況': 'status', 'メッセージ': 'message',
            'おすすめ': 'recommendation', '通販URL': 'ec_url'
        }
        df = df.rename(columns=mapping)
        df = df.dropna(subset=['name'])
        df['id'] = df['id'].astype(str).str.replace('.0', '', regex=False).str.strip()
        return df.fillna("未設定")
    except Exception as e:
        print(f"Error reading sheet: {e}")
        return pd.DataFrame()

# --- デザイン (スマホアプリ風フォーム搭載) ---
LAYOUT = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <title>復興支援ポータル</title>
    <style>
        body { background-color: #fffaf0; }
        .status-営業中 { background-color: #dcfce7; color: #166534; border: 1px solid #86efac; }
        .status-営業予定 { background-color: #fef9c3; color: #854d0e; border: 1px solid #fde047; }
        .status-準備中 { background-color: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; }
        .modal { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 100; }
        .modal-content { position: absolute; bottom: 0; width: 100%; max-width: 500px; left: 50%; transform: translateX(-50%); background: white; border-radius: 24px 24px 0 0; padding: 24px; }
    </style>
</head>
<body class="min-h-screen text-slate-800 pb-20">
    <nav class="bg-orange-600 text-white p-5 shadow-lg text-center font-bold text-xl">
        <a href="/">復興支援ポータル</a>
    </nav>

    <div class="flex bg-white shadow-sm mb-8">
        <a href="/?role=supporter" class="flex-1 py-4 text-center text-sm font-bold {{ 'text-orange-600 border-b-4 border-orange-600' if role == 'supporter' else 'text-slate-400' }}">支援者</a>
        <a href="/?role=owner" class="flex-1 py-4 text-center text-sm font-bold {{ 'text-orange-600 border-b-4 border-orange-600' if role == 'owner' else 'text-slate-400' }}">事業者</a>
    </div>

    <div class="max-w-md mx-auto px-4">
        {% if mode == 'success' %}
        <div class="bg-white p-10 rounded-3xl shadow-xl text-center">
            <h2 class="text-xl font-bold mb-4 text-emerald-600">申請完了</h2>
            <p class="text-xs mb-6">店舗ID: <span class="font-bold text-orange-600">{{ new_id }}</span></p>
            <a href="/" class="inline-block px-6 py-2 bg-orange-500 text-white rounded-full font-bold">戻る</a>
        </div>
        {% elif shop %}
        <div class="bg-white rounded-3xl shadow-xl overflow-hidden border-t-8 border-orange-500">
            <img src="{{ shop.image_url }}" class="w-full h-52 object-cover" onerror="this.src='https://via.placeholder.com/400x250?text=No+Image'">
            <div class="p-8">
                <span class="inline-block px-3 py-1 rounded-full font-bold text-xs status-{{ shop.status }} mb-4">{{ shop.status }}</span>
                <h2 class="text-2xl font-black mb-4">{{ shop.name }}</h2>
                <div class="bg-orange-50 p-4 rounded-xl italic mb-8 text-sm">「{{ shop.message }}」</div>
                <a href="{{ shop.ec_url }}" target="_blank" class="block w-full py-4 bg-orange-500 text-white rounded-2xl font-bold text-center">🛒 通販サイト</a>
            </div>
        </div>
        {% else %}
        <div class="space-y-4">
            {% for s in all_shops %}
            <a href="/shop/{{ s.id }}?role=supporter" class="flex items-center p-4 bg-white rounded-2xl shadow-sm border border-orange-50 active:scale-95 transition">
                <div class="w-14 h-14 rounded-xl overflow-hidden shrink-0 border"><img src="{{ s.image_url }}" class="w-full h-full object-cover" onerror="this.src='https://via.placeholder.com/100'"></div>
                <div class="ml-4 flex-1">
                    <span class="text-[9px] px-2 py-0.5 rounded-full font-bold status-{{ s.status }}">{{ s.status }}</span>
                    <h3 class="text-lg font-bold">{{ s.name }}</h3>
                </div>
                <div class="text-orange-200 font-bold">▶</div>
            </a>
            {% endfor %}
        </div>
        {% endif %}
    </div>

    {% if role == 'owner' %}
    <button onclick="document.getElementById('formModal').style.display='block'" class="fixed bottom-6 right-6 w-16 h-16 bg-slate-900 text-white rounded-full flex items-center justify-center shadow-2xl text-3xl font-light">+</button>
    {% endif %}

    <div id="formModal" class="modal">
        <div class="modal-content">
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-xl font-bold">店舗情報 登録</h3>
                <button onclick="document.getElementById('formModal').style.display='none'" class="text-slate-400">Cancel</button>
            </div>
            <form action="/submit" method="POST" class="space-y-4">
                <div>
                    <label class="block text-xs font-bold text-slate-400 mb-1">店名 *</label>
                    <input type="text" name="name" required class="w-full p-3 rounded-xl bg-slate-50 border outline-none focus:border-orange-500">
                </div>
                <div>
                    <label class="block text-xs font-bold text-slate-400 mb-1">ジャンル *</label>
                    <input type="text" name="genre" required class="w-full p-3 rounded-xl bg-slate-50 border outline-none">
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
                    <textarea name="message" class="w-full p-3 rounded-xl bg-slate-50 border h-24"></textarea>
                </div>
                <button type="submit" class="w-full py-4 bg-orange-600 text-white rounded-2xl font-bold shadow-lg">Save</button>
            </form>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    role = request.args.get('role', 'supporter')
    df = get_all_data()
    all_shops = df.to_dict(orient='records') if not df.empty else []
    return render_template_string(LAYOUT, role=role, all_shops=all_shops)

@app.route('/shop/<shop_id>')
def render_shop(shop_id):
    role = request.args.get('role', 'supporter')
    df = get_all_data()
    row = df[df['id'] == str(shop_id)]
    if row.empty: return "お店が見つかりません", 404
    return render_template_string(LAYOUT, role=role, shop=row.iloc[0].to_dict())

@app.route('/submit', methods=['POST'])
def submit():
    new_id = str(uuid.uuid4())[:4].upper()
    return render_template_string(LAYOUT, mode='success', new_id=new_id, role='owner')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
