import pandas as pd
from flask import Flask, render_template_string, request
import os

app = Flask(__name__)

# --- 設定 ---
SHEET_ID = "1incBINNVhc64m6oRNCIKgkhMrUOTnUUF3v5MfS8eFkg"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet2"

# ★あなたのGoogleフォームのURLをここに貼り付けてください★
GOOGLE_FORM_URL = "https://docs.google.com/forms/d/e/あなたのフォームID/viewform"

def get_all_data():
    try:
        # 2行目を見出しとして読み込む
        df = pd.read_csv(SHEET_URL, header=1)
        df.columns = df.columns.str.strip()
        
        # スプレッドシートの項目名をプログラム用に変換
        mapping = {
            'タイムスタンプ': 'timestamp', # フォームを使うと自動で入る列
            'ID': 'id', '店名': 'name', '画像URL': 'image_url',
            '状況': 'status', 'メッセージ': 'message',
            'おすすめ': 'recommendation', '通販URL': 'ec_url'
        }
        df = df.rename(columns=mapping)
        
        # 店名がない行を削除
        df = df.dropna(subset=['name'])
        
        # IDがフォームで入らない場合は、行番号などを仮のIDにする
        if 'id' not in df.columns or df['id'].isnull().all():
            df['id'] = range(101, 101 + len(df))
            
        df['id'] = df['id'].astype(str).str.replace('.0', '', regex=False).str.strip()
        return df.fillna("未設定")
    except Exception as e:
        print(f"Error: {e}")
        return pd.DataFrame()

# --- HTML デザイン ---
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
    <nav class="bg-orange-600 text-white p-5 shadow-lg text-center font-bold">
        <a href="/">復興支援ポータル</a>
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
        {% if role == 'owner' %}
        <div class="bg-white p-8 rounded-3xl shadow-xl text-center border-t-8 border-slate-800">
            <h2 class="text-xl font-bold mb-6 text-slate-800">事業者の方へ</h2>
            <p class="text-sm text-slate-500 mb-8 leading-relaxed">
                以下のボタンからお店の情報を登録・更新してください。<br>
                入力した内容は自動的にポータルサイトへ反映されます。
            </p>
            <a href="{{ form_url }}" target="_blank" class="block w-full py-4 bg-slate-800 text-white rounded-2xl font-bold shadow-lg hover:bg-black transition">
                📝 情報を登録・更新する
            </a>
            <p class="text-[10px] text-slate-400 mt-6">※Googleフォームが開きます</p>
        </div>

        {% elif shop %}
        <div class="bg-white rounded-3xl shadow-xl overflow-hidden mb-6 border-t-8 border-orange-500">
            <img src="{{ shop.image_url }}" class="w-full h-52 object-cover" onerror="this.src='https://via.placeholder.com/400x250?text=No+Photo'">
            <div class="p-8">
                <span class="inline-block px-3 py-1 rounded-full font-bold text-xs status-{{ shop.status }} mb-4">{{ shop.status }}</span>
                <h2 class="text-2xl font-black mb-4">{{ shop.name }}</h2>
                <div class="bg-orange-50 p-4 rounded-xl italic mb-6 text-sm">「{{ shop.message }}」</div>
                
                <div class="space-y-4">
                    <a href="{{ shop.ec_url }}" target="_blank" class="block w-full py-4 bg-orange-500 text-white rounded-2xl font-bold text-center shadow-lg">🛒 通販でお買い物</a>
                    
                    <div class="pt-6 border-t border-slate-100">
                        <h3 class="text-sm font-bold text-blue-600 mb-4 tracking-tighter text-center">お店を評価して応援コメントを送る</h3>
                        <div class="bg-blue-50 p-4 rounded-2xl text-center">
                            <p class="text-xs text-blue-800 mb-2 font-bold">0〜5の評価機能</p>
                            <p class="text-[10px] text-blue-400 leading-tight">現在、コメント投稿機能を準備中です。<br>公式SNSなどからも応援をお願いします！</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <a href="/?role=supporter" class="block text-center text-xs text-slate-400">← 一覧に戻る</a>

        {% else %}
        <div class="space-y-4">
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
    role = request.args.get('role', 'supporter')
    df = get_all_data()
    all_shops = df.to_dict(orient='records') if not df.empty else []
    return render_template_string(LAYOUT, role=role, all_shops=all_shops, form_url=GOOGLE_FORM_URL)

@app.route('/shop/<shop_id>')
def render_shop(shop_id):
    role = request.args.get('role', 'supporter')
    df = get_all_data()
    row = df[df['id'] == str(shop_id)]
    if row.empty: abort(404)
    return render_template_string(LAYOUT, role=role, shop=row.iloc[0].to_dict(), form_url=GOOGLE_FORM_URL)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
