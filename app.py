import pandas as pd
from flask import Flask, render_template_string, request, redirect, url_for
import os
import uuid

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
            'おすすめ': 'recommendation', '通販URL': 'ec_url'
        }
        df = df.rename(columns=mapping)
        df = df.dropna(subset=['id', 'name'])
        df['id'] = df['id'].astype(str).str.replace('.0', '', regex=False).str.strip()
        return df.fillna("未設定")
    except:
        return pd.DataFrame()

# --- HTML デザイン (切り替え機能付き) ---
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
        .tab-active { border-bottom: 4px solid #ea580c; color: #ea580c; font-weight: bold; }
    </style>
</head>
<body class="min-h-screen text-slate-800 pb-20">
    <nav class="bg-orange-600 text-white p-5 shadow-lg text-center">
        <h1 class="text-xl font-bold"><a href="/">復興支援ポータル</a></h1>
    </nav>

    <div class="flex bg-white shadow-sm mb-8">
        <a href="/?role=supporter" class="flex-1 py-4 text-center text-sm {{ 'tab-active' if role == 'supporter' else 'text-slate-400' }}">
            支援者として利用
        </a>
        <a href="/?role=owner" class="flex-1 py-4 text-center text-sm {{ 'tab-active' if role == 'owner' else 'text-slate-400' }}">
            事業者として利用
        </a>
    </div>

    <div class="max-w-md mx-auto px-4">
        {% if mode == 'success' %}
        <div class="bg-white p-10 rounded-3xl shadow-xl text-center">
            <h2 class="text-lg font-bold mb-4 text-orange-600">登録受付完了！</h2>
            <p class="text-xs text-slate-500 mb-2">生成された店舗ID（編集者に伝えてください）</p>
            <div class="flex items-center justify-center gap-2 mb-8">
                <code id="newId" class="bg-slate-100 px-4 py-2 rounded-lg font-bold text-orange-600 border border-orange-200">{{ new_id }}</code>
                <button onclick="navigator.clipboard.writeText('{{ new_id }}');alert('コピーしました')" class="bg-orange-500 text-white px-3 py-2 rounded-lg text-xs">コピー</button>
            </div>
            <a href="/?role=owner" class="text-orange-500 font-bold">事業者画面へ戻る</a>
        </div>

        {% elif shop %}
        <div class="bg-white rounded-3xl shadow-xl overflow-hidden mb-6 border-t-8 border-orange-500">
            <img src="{{ shop.image_url }}" class="w-full h-52 object-cover" onerror="this.src='https://via.placeholder.com/400x250?text=No+Photo'">
            <div class="p-8">
                <span class="inline-block px-3 py-1 rounded-full font-bold text-xs status-{{ shop.status }} mb-4">{{ shop.status }}</span>
                <h2 class="text-2xl font-black mb-4">{{ shop.name }}</h2>
                <p class="bg-orange-50 p-4 rounded-xl italic mb-6 text-sm">「{{ shop.message }}」</p>
                
                <div class="space-y-4">
                    <a href="{{ shop.ec_url }}" target="_blank" class="block w-full py-4 bg-orange-500 text-white rounded-2xl font-bold text-center shadow-lg">🛒 通販でお買い物</a>
                    
                    <div class="pt-6 border-t border-slate-100">
                        <h3 class="text-sm font-bold text-blue-600 mb-4">📣 応援メッセージを送る</h3>
                        <form action="/cheer" method="POST" class="space-y-3">
                            <input type="hidden" name="shop_id" value="{{ shop.id }}">
                            <select name="rating" class="w-full p-3 rounded-xl bg-slate-50 border text-orange-500 font-bold">
                                <option value="5">⭐⭐⭐⭐⭐ (5)</option>
                                <option value="4">⭐⭐⭐⭐ (4)</option>
                                <option value="3">⭐⭐⭐ (3)</option>
                                <option value="2">⭐⭐ (2)</option>
                                <option value="1">⭐ (1)</option>
                            </select>
                            <textarea name="comment" placeholder="メッセージを入力" class="w-full p-3 h-20 rounded-xl bg-slate-50 border text-sm"></textarea>
                            <button type="submit" class="w-full py-3 bg-blue-500 text-white rounded-xl font-bold shadow-md">送信する</button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
        <a href="/?role=supporter" class="block text-center text-xs text-slate-400">← 一覧に戻る</a>

        {% elif role == 'owner' %}
        <div class="bg-white p-8 rounded-3xl shadow-xl">
            <h2 class="text-lg font-bold mb-6 text-orange-600 border-b pb-2">店舗情報の新規登録</h2>
            <form action="/submit" method="POST" class="space-y-4">
                <input type="text" name="name" placeholder="店名" required class="w-full p-3 rounded-xl bg-slate-50 border outline-none">
                <select name="status" class="w-full p-3 rounded-xl bg-slate-50 border">
                    <option value="営業中">営業中（緑）</option>
                    <option value="営業予定">営業予定（黄）</option>
                    <option value="準備中">準備中（赤）</option>
                </select>
                <textarea name="message" placeholder="店主からのメッセージ" class="w-full p-3 h-24 rounded-xl bg-slate-50 border"></textarea>
                <input type="url" name="image_url" placeholder="写真のURL" class="w-full p-3 rounded-xl bg-slate-50 border">
                <input type="url" name="ec_url" placeholder="通販サイトのURL" class="w-full p-3 rounded-xl bg-slate-50 border">
                <button type="submit" class="w-full py-4 bg-slate-800 text-white rounded-2xl font-bold shadow-lg mt-4">情報を登録・更新する</button>
            </form>
            <p class="text-[10px] text-slate-400 mt-6 leading-relaxed text-center">
                ※入力した内容は編集者が確認後に反映します。
            </p>
        </div>

        {% else %}
        <div class="space-y-4">
            <p class="text-center text-slate-400 text-[10px] font-bold tracking-widest uppercase mb-6">応援したいお店を選んでください</p>
            {% for s in all_shops %}
            <a href="/shop/{{ s.id }}?role=supporter" class="flex items-center p-4 bg-white rounded-2xl shadow-md border border-orange-50 transition active:scale-95">
                <div class="w-14 h-14 rounded-xl overflow-hidden shrink-0 border"><img src="{{ s.image_url }}" class="w-full h-full object-cover" onerror="this.src='https://via.placeholder.com/100'"></div>
                <div class="ml-4 flex-1">
                    <span class="text-[9px] px-2 py-0.5 rounded-full font-bold status-{{ s.status }}">{{ s.status }}</span>
                    <h3 class="text-lg font-bold text-slate-800">{{ s.name }}</h3>
                </div>
                <div class="text-orange-200">▶</div>
            </a>
            {% endfor %}
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    role = request.args.get('role', 'supporter') # デフォルトは支援者
    df = get_all_data()
    all_shops = df.to_dict(orient='records') if not df.empty else []
    return render_template_string(LAYOUT, role=role, all_shops=all_shops, mode='list')

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

@app.route('/cheer', methods=['POST'])
def cheer():
    return "<h3>応援ありがとうございます！</h3><p>メッセージを送信しました。管理者が確認後に掲載します。</p><a href='/?role=supporter'>戻る</a>"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
