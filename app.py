import pandas as pd
from flask import Flask, render_template_string, request
import os
import uuid

app = Flask(__name__)

# --- 設定：スプレッドシート情報 ---
SHEET_ID = "1incBINNVhc64m6oRNCIKgkhMrUOTnUUF3v5MfS8eFkg"
# Sheet2 (店舗基本情報)
SHEET2_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1191908203&headers=1"
# Sheet3 (支援者の評価とコメント) ★新しく教えてもらったGIDを反映しました
SHEET3_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=317117230"

def get_data():
    try:
        # 1. 店舗データの読み込み (Sheet2)
        df = pd.read_csv(SHEET2_URL, header=1, engine='python')
        df.columns = df.columns.str.strip()
        mapping = {
            'ID': 'id', '店名': 'name', '画像URL': 'image_url',
            '状況': 'status', 'メッセージ': 'message',
            'おすすめ': 'recommendation', '通販URL': 'ec_url'
        }
        df = df.rename(columns=mapping).dropna(subset=['name'])
        df['id'] = df['id'].astype(str).str.replace('.0', '', regex=False).str.strip()
        
        # 2. 応援コメントの読み込み (Sheet3)
        try:
            comments_df = pd.read_csv(SHEET3_URL, engine='python')
            comments_df.columns = comments_df.columns.str.strip()
            # 項目名が「店舗ID」「星評価」「コメント」であることを想定
        except:
            comments_df = pd.DataFrame(columns=['店舗ID', '星評価', 'コメント'])
            
        return df.fillna("未設定"), comments_df
    except Exception as e:
        print(f"読み込みエラー: {e}")
        return pd.DataFrame(), pd.DataFrame()

# --- HTML デザイン ---
LAYOUT = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <title>復興支援ポータル</title>
    <style>
        body { background-color: #fff9f2; }
        .status-営業中 { background-color: #dcfce7; color: #166534; border: 1px solid #86efac; }
        .status-営業予定 { background-color: #fef9c3; color: #854d0e; border: 1px solid #fde047; }
        .status-準備中 { background-color: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; }
        .modal { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 100; }
        .modal-content { position: absolute; bottom: 0; width: 100%; max-width: 500px; left: 50%; transform: translateX(-50%); background: white; border-radius: 24px 24px 0 0; padding: 24px; max-height: 90vh; overflow-y: auto; }
    </style>
</head>
<body class="min-h-screen text-slate-800 pb-20 font-sans">
    <nav class="bg-orange-600 text-white p-5 shadow-lg text-center font-bold text-xl">
        <a href="/">復興支援ポータル</a>
    </nav>

    <div class="flex bg-white shadow-sm mb-8">
        <a href="/?role=supporter" class="flex-1 py-4 text-center text-sm font-bold {{ 'text-orange-600 border-b-4 border-orange-600' if role == 'supporter' else 'text-slate-400' }}">支援者モード</a>
        <a href="/?role=owner" class="flex-1 py-4 text-center text-sm font-bold {{ 'text-orange-600 border-b-4 border-orange-600' if role == 'owner' else 'text-slate-400' }}">事業者モード</a>
    </div>

    <div class="max-w-md mx-auto px-4">
        {% if role == 'owner' %}
        <div class="bg-white p-6 rounded-3xl shadow-md border-t-8 border-slate-800 text-center">
            <h2 class="text-xl font-bold mb-4 italic">事業者様へ</h2>
            <p class="text-sm text-slate-500 mb-6 leading-relaxed">右下の「＋」からお店を登録してください。<br>Save後に内容がコピーされますので、<br>それを編集者に送ると反映されます。</p>
        </div>
        
        {% elif shop %}
        <div class="bg-white rounded-3xl shadow-xl overflow-hidden border-t-8 border-orange-500 mb-8">
            <img src="{{ shop.image_url }}" class="w-full h-52 object-cover" onerror="this.src='https://via.placeholder.com/400x250?text=No+Photo'">
            <div class="p-8">
                <span class="inline-block px-3 py-1 rounded-full font-bold text-xs status-{{ shop.status }} mb-4">{{ shop.status }}</span>
                <h2 class="text-3xl font-black mb-4">{{ shop.name }}</h2>
                <div class="bg-orange-50 p-4 rounded-xl italic mb-6 text-sm text-slate-600 font-medium">「{{ shop.message }}」</div>
                <a href="{{ shop.ec_url }}" target="_blank" class="block w-full py-4 bg-orange-600 text-white rounded-2xl font-bold text-center shadow-lg mb-8">🛒 通販サイトへ</a>
                
                <div class="pt-6 border-t border-slate-100">
                    <h3 class="text-lg font-bold text-blue-600 mb-4 tracking-tighter italic">📣 支援者からの応援コメント</h3>
                    {% if comments %}
                        {% for c in comments %}
                        <div class="mb-4 p-4 bg-blue-50/50 rounded-2xl border border-blue-100">
                            <div class="text-orange-400 text-xs mb-1 font-bold">評価: {{ "⭐" * c['星評価']|int }}</div>
                            <p class="text-sm text-slate-700 font-medium leading-relaxed">{{ c['コメント'] }}</p>
                        </div>
                        {% endfor %}
                    {% else %}
                        <p class="text-xs text-slate-400 italic py-4">まだコメントはありません。最初の応援を送りましょう！</p>
                    {% endif %}
                </div>
            </div>
        </div>
        <a href="/?role=supporter" class="block text-center text-xs text-slate-400 font-bold mb-10">← 他のお店も見る</a>

        {% else %}
        <div class="space-y-4">
            <p class="text-center text-slate-400 text-[10px] font-bold tracking-widest uppercase mb-4">いま応援を必要としているお店</p>
            {% for s in all_shops %}
            <a href="/shop/{{ s.id }}?role=supporter" class="flex items-center p-4 bg-white rounded-2xl shadow-sm border border-orange-50 active:scale-95 transition">
                <div class="w-14 h-14 rounded-xl overflow-hidden shrink-0 border"><img src="{{ s.image_url }}" class="w-full h-full object-cover" onerror="this.src='https://via.placeholder.com/100'"></div>
                <div class="ml-4 flex-1">
                    <span class="text-[9px] px-2 py-0.5 rounded-full font-bold status-{{ s.status }}">{{ s.status }}</span>
                    <h3 class="text-lg font-bold text-slate-800 tracking-tight">{{ s.name }}</h3>
                </div>
                <div class="text-orange-200">▶</div>
            </a>
            {% endfor %}
        </div>
        {% endif %}
    </div>

    {% if role == 'owner' %}
    <button onclick="document.getElementById('formModal').style.display='block'" class="fixed bottom-6 right-6 w-16 h-16 bg-slate-900 text-white rounded-full flex items-center justify-center shadow-2xl text-3xl">+</button>
    <div id="formModal" class="modal">
        <div class="modal-content shadow-2xl">
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-xl font-bold">店舗情報の登録申請</h3>
                <button onclick="document.getElementById('formModal').style.display='none'" class="text-slate-400 text-sm">Cancel</button>
            </div>
            <form onsubmit="generateReport(event)" class="space-y-4 pb-10">
                <input type="text" id="f-name" placeholder="店名 *" required class="w-full p-4 rounded-2xl bg-slate-50 border outline-none focus:border-orange-500">
                <select id="f-status" class="w-full p-4 rounded-2xl bg-slate-50 border font-bold">
                    <option value="営業中">営業中</option>
                    <option value="営業予定">営業予定</option>
                    <option value="準備中">準備中</option>
                </select>
                <textarea id="f-message" placeholder="支援者へのメッセージ" class="w-full p-4 rounded-2xl bg-slate-50 border h-28 outline-none focus:border-orange-500"></textarea>
                <input type="url" id="f-image" placeholder="画像URL（Instagramのリンクなど）" class="w-full p-4 rounded-2xl bg-slate-50 border outline-none focus:border-orange-500">
                <button type="submit" class="w-full py-5 bg-slate-800 text-white rounded-2xl font-bold text-lg shadow-xl active:scale-95 transition">Save & Copy</button>
            </form>
        </div>
    </div>
    {% endif %}

    <script>
        function generateReport(e) {
            e.preventDefault();
            const name = document.getElementById('f-name').value;
            const status = document.getElementById('f-status').value;
            const msg = document.getElementById('f-message').value;
            const img = document.getElementById('f-image').value;
            const report = `【新規申請】\\n店名: ${name}\\n状況: ${status}\\nメッセージ: ${msg}\\n画像: ${img}`;
            navigator.clipboard.writeText(report);
            alert('申請内容をコピーしました！この内容を管理者に送ってください。反映後、サイトに表示されます。');
            document.getElementById('formModal').style.display = 'none';
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    role = request.args.get('role', 'supporter')
    df, _ = get_data()
    all_shops = df.to_dict(orient='records') if not df.empty else []
    return render_template_string(LAYOUT, role=role, all_shops=all_shops)

@app.route('/shop/<shop_id>')
def render_shop(shop_id):
    role = request.args.get('role', 'supporter')
    df, comments_df = get_data()
    row = df[df['id'] == str(shop_id)]
    if row.empty: return "お店が見つかりませんでした", 404
    
    # Sheet3から、この店舗IDに一致するコメントを抽出
    shop_comments = comments_df[comments_df['店舗ID'].astype(str) == str(shop_id)].to_dict(orient='records')
    
    return render_template_string(LAYOUT, role=role, shop=row.iloc[0].to_dict(), comments=shop_comments)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
