import pandas as pd
from flask import Flask, render_template_string, request
import os
import uuid

app = Flask(__name__)

# --- 設定：スプレッドシートIDと各シートのGID ---
SHEET_ID = "1incBINNVhc64m6oRNCIKgkhMrUOTnUUF3v5MfS8eFkg"
# Sheet2 (店舗情報) GID: 1191908203
S2_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1191908203"
# Sheet3 (コメント) GID: 317117230
S3_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=317117230"

def get_data():
    try:
        # header=1(2行目)を読み込み。engine='c'で高速化
        df = pd.read_csv(S2_URL, header=1, engine='c')
        df.columns = df.columns.str.strip()
        mapping = {'ID':'id','店名':'name','画像URL':'img','状況':'st','メッセージ':'msg','通販URL':'ec'}
        df = df.rename(columns=mapping).dropna(subset=['name'])
        df['id'] = df['id'].astype(str).str.replace('.0', '', regex=False).str.strip()
        
        try:
            # Sheet3の読み込み
            c_df = pd.read_csv(S3_URL, engine='c')
            c_df.columns = c_df.columns.str.strip()
        except:
            c_df = pd.DataFrame(columns=['店舗ID', '星評価', 'コメント'])
            
        return df.fillna("未設定"), c_df
    except:
        return pd.DataFrame(), pd.DataFrame()

# --- HTMLデザイン ---
LAYOUT = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <title>復興支援ポータル</title>
    <style>
        body { background-color: #fff9f2; }
        .st-営業中 { background-color: #dcfce7; color: #166534; }
        .st-営業予定 { background-color: #fef9c3; color: #854d0e; }
        .st-準備中 { background-color: #fee2e2; color: #991b1b; }
        .modal { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 50; }
        .modal-content { position: absolute; bottom: 0; width: 100%; max-width: 500px; left: 50%; transform: translateX(-50%); background: white; border-radius: 20px 20px 0 0; padding: 20px; }
    </style>
</head>
<body class="pb-20">
    <nav class="bg-orange-600 text-white p-4 text-center font-bold shadow-md">
        <a href="/">復興支援ポータル</a>
    </nav>

    <div class="flex bg-white shadow-sm mb-6">
        <a href="/?role=s" class="flex-1 py-3 text-center text-sm {{ 'text-orange-600 border-b-2 border-orange-600 font-bold' if role == 's' else 'text-slate-400' }}">支援者</a>
        <a href="/?role=o" class="flex-1 py-3 text-center text-sm {{ 'text-orange-600 border-b-2 border-orange-600 font-bold' if role == 'o' else 'text-slate-400' }}">事業者</a>
    </div>

    <div class="max-w-md mx-auto px-4">
        {% if role == 'o' %}
        <div class="bg-white p-6 rounded-2xl shadow text-center border-t-4 border-slate-700">
            <h2 class="font-bold mb-2">事業者様メニュー</h2>
            <p class="text-xs text-slate-500 mb-4">＋ボタンから申請内容を作成し、<br>コピーして管理者に送ってください。</p>
        </div>
        {% elif shop %}
        <div class="bg-white rounded-2xl shadow-lg overflow-hidden border-t-4 border-orange-500 mb-6">
            <img src="{{ shop.img }}" class="w-full h-48 object-cover" onerror="this.src='https://via.placeholder.com/400x200?text=No+Photo'">
            <div class="p-6">
                <span class="inline-block px-2 py-0.5 rounded-full text-[10px] font-bold st-{{ shop.st }} mb-2">{{ shop.st }}</span>
                <h2 class="text-2xl font-bold mb-3">{{ shop.name }}</h2>
                <p class="bg-orange-50 p-3 rounded-lg text-sm italic mb-6">「{{ shop.msg }}」</p>
                <a href="{{ shop.ec }}" target="_blank" class="block w-full py-3 bg-orange-600 text-white rounded-xl font-bold text-center">🛒 通販サイト</a>
                
                <div class="mt-6 pt-4 border-t border-slate-100 text-sm">
                    <h3 class="font-bold text-blue-600 mb-3 italic">📣 応援コメント</h3>
                    {% if comments %}
                        {% for c in comments %}
                        <div class="mb-3 p-3 bg-blue-50/50 rounded-xl text-xs">
                            <div class="text-orange-400 mb-1 font-bold">{{ "⭐" * c['星評価']|int }}</div>
                            <p>{{ c['コメント'] }}</p>
                        </div>
                        {% endfor %}
                    {% else %}
                        <p class="text-slate-400 italic">コメント募集中です</p>
                    {% endif %}
                </div>
            </div>
        </div>
        <a href="/?role=s" class="block text-center text-xs text-slate-400 font-bold">← 戻る</a>
        {% else %}
        <div class="space-y-3">
            {% for s in all %}
            <a href="/shop/{{ s.id }}?role=s" class="flex items-center p-3 bg-white rounded-xl shadow-sm border border-orange-50 active:scale-95 transition">
                <div class="w-12 h-12 rounded-lg overflow-hidden shrink-0"><img src="{{ s.img }}" class="w-full h-full object-cover" onerror="this.src='https://via.placeholder.com/100'"></div>
                <div class="ml-3 flex-1">
                    <span class="text-[8px] px-1.5 py-0.5 rounded-full font-bold st-{{ s.st }}">{{ s.st }}</span>
                    <h3 class="text-base font-bold text-slate-800">{{ s.name }}</h3>
                </div>
                <div class="text-orange-200">▶</div>
            </a>
            {% endfor %}
        </div>
        {% endif %}
    </div>

    {% if role == 'o' %}
    <button onclick="document.getElementById('m').style.display='block'" class="fixed bottom-6 right-6 w-14 h-14 bg-slate-800 text-white rounded-full shadow-xl text-2xl font-light">+</button>
    <div id="m" class="modal">
        <div class="modal-content shadow-2xl">
            <div class="flex justify-between items-center mb-4">
                <h3 class="font-bold">店舗申請</h3>
                <button onclick="document.getElementById('m').style.display='none'" class="text-slate-400 text-xs">Cancel</button>
            </div>
            <form onsubmit="copyR(event)" class="space-y-3 pb-6">
                <input type="text" id="fn" placeholder="店名 *" required class="w-full p-3 rounded-xl bg-slate-50 border outline-none text-sm">
                <select id="fs" class="w-full p-3 rounded-xl bg-slate-50 border text-sm"><option>営業中</option><option>営業予定</option><option>準備中</option></select>
                <textarea id="fm" placeholder="メッセージ" class="w-full p-3 rounded-xl bg-slate-50 border h-20 text-sm"></textarea>
                <button type="submit" class="w-full py-3 bg-slate-800 text-white rounded-xl font-bold shadow-md">Copy申請内容</button>
            </form>
        </div>
    </div>
    <script>
        function copyR(e){
            e.preventDefault();
            const r = `店名:${document.getElementById('fn').value}\\n状況:${document.getElementById('fs').value}\\nメッセージ:${document.getElementById('fm').value}`;
            navigator.clipboard.writeText(r);
            alert('コピーしました！管理者に送ってください。');
            document.getElementById('m').style.display='none';
        }
    </script>
    {% endif %}
</body>
</html>
"""

@app.route('/')
def index():
    role = request.args.get('role', 's')
    df, _ = get_data()
    all_s = df.to_dict(orient='records') if not df.empty else []
    return render_template_string(LAYOUT, role=role, all=all_s)

@app.route('/shop/<sid>')
def shop(sid):
    df, c_df = get_data()
    row = df[df['id'] == str(sid)]
    if row.empty: return "Not Found", 404
    cms = c_df[c_df['店舗ID'].astype(str) == str(sid)].to_dict(orient='records')
    return render_template_string(LAYOUT, role='s', shop=row.iloc[0].to_dict(), comments=cms)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
