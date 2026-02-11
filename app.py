import pandas as pd
from flask import Flask, render_template_string, request
import os
import uuid

app = Flask(__name__)

# --- 設定：スプレッドシート情報 ---
SID = "1incBINNVhc64m6oRNCIKgkhMrUOTnUUF3v5MfS8eFkg"
# Sheet2 (店舗情報) / Sheet3 (支援者コメント)
S2_URL = f"https://docs.google.com/spreadsheets/d/{SID}/export?format=csv&gid=1191908203"
S3_URL = f"https://docs.google.com/spreadsheets/d/{SID}/export?format=csv&gid=317117230"

def get_data():
    try:
        # 起動を速くするため読み込みを最適化
        df = pd.read_csv(S2_URL, header=1, engine='c')
        df.columns = df.columns.str.strip()
        m = {'ID':'id','店名':'name','画像URL':'img','状況':'st','メッセージ':'msg','おすすめ':'rec','通販URL':'ec'}
        df = df.rename(columns=m).dropna(subset=['name'])
        df['id'] = df['id'].astype(str).str.replace('.0', '', regex=False).str.strip()
        
        try:
            c_df = pd.read_csv(S3_URL, engine='c')
            c_df.columns = c_df.columns.str.strip()
        except:
            c_df = pd.DataFrame(columns=['店舗ID', '星評価', 'コメント'])
            
        return df.fillna("未設定"), c_df
    except:
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
        body { background-color: #fffaf0; font-family: sans-serif; }
        .st-営業中 { background-color: #dcfce7; color: #166534; }
        .st-営業予定 { background-color: #fef9c3; color: #854d0e; }
        .st-準備中 { background-color: #fee2e2; color: #991b1b; }
        .modal { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 50; }
        .m-content { position: absolute; bottom: 0; width: 100%; max-width: 500px; left: 50%; transform: translateX(-50%); background: white; border-radius: 24px 24px 0 0; padding: 24px; max-height: 90vh; overflow-y: auto; }
    </style>
</head>
<body class="pb-20">
    <nav class="bg-orange-600 text-white p-5 text-center font-bold shadow-lg text-lg tracking-widest">復興支援ポータル</nav>
    
    <div class="flex bg-white shadow-sm mb-8">
        <a href="/?r=s" class="flex-1 py-4 text-center {{ 'text-orange-600 border-b-4 border-orange-600 font-bold' if r == 's' else 'text-slate-400' }}">支援者モード</a>
        <a href="/?r=o" class="flex-1 py-4 text-center {{ 'text-orange-600 border-b-4 border-orange-600 font-bold' if r == 'o' else 'text-slate-400' }}">事業者モード</a>
    </div>

    <div class="max-w-md mx-auto px-4">
        {% if r == 'o' %}
        <div class="bg-white p-8 rounded-3xl shadow-xl border-t-8 border-slate-800 text-center">
            <h2 class="font-bold text-lg mb-4">店舗情報の掲載申請</h2>
            <p class="text-sm text-slate-500 mb-8 leading-relaxed">右下の「＋」ボタンを押して情報を入力してください。<br>入力後に発行される内容を管理者に送ると、<br>サイトへ反映されます。</p>
        </div>
        {% elif shop %}
        <div class="bg-white rounded-3xl shadow-xl overflow-hidden border-t-8 border-orange-500 mb-8">
            <img src="{{ shop.img }}" class="w-full h-56 object-cover" onerror="this.src='https://via.placeholder.com/400x250?text=No+Photo'">
            <div class="p-8">
                <span class="inline-block px-3 py-1 rounded-full text-xs font-bold st-{{ shop.st }} mb-4">{{ shop.st }}</span>
                <h2 class="text-3xl font-black mb-4">{{ shop.name }}</h2>
                <div class="bg-orange-50 p-4 rounded-xl text-sm italic mb-10 text-slate-600 font-medium">「{{ shop.msg }}」</div>
                <a href="{{ shop.ec }}" target="_blank" class="block w-full py-4 bg-orange-500 text-white rounded-2xl font-bold text-center shadow-lg mb-10">🛒 通販サイトへ</a>
                
                <div class="pt-6 border-t border-slate-100">
                    <h3 class="text-lg font-bold text-blue-600 mb-6 italic">📣 支援者からの応援コメント</h3>
                    {% if comments %}
                        {% for c in comments %}
                        <div class="p-4 bg-blue-50/50 rounded-2xl border border-blue-100 mb-4">
                            <div class="text-orange-400 text-xs mb-1 font-bold">評価: {{ "⭐" * c['星評価']|int }}</div>
                            <p class="text-slate-700 text-sm leading-relaxed">{{ c['コメント'] }}</p>
                        </div>
                        {% endfor %}
                    {% else %}
                        <p class="text-xs text-slate-400 italic text-center py-4">まだ応援メッセージはありません。</p>
                    {% endif %}
                </div>
            </div>
        </div>
        <a href="/?r=s" class="block text-center text-xs text-slate-400 font-bold mb-10">← 一覧に戻る</a>
        {% else %}
        <div class="space-y-4">
            {% for i in all %}
            <a href="/shop/{{ i.id }}?r=s" class="flex items-center p-4 bg-white rounded-2xl shadow-md border border-orange-50 active:scale-95 transition">
                <div class="w-14 h-14 rounded-xl overflow-hidden shrink-0 border"><img src="{{ i.img }}" class="w-full h-full object-cover" onerror="this.src='https://via.placeholder.com/100'"></div>
                <div class="ml-4 flex-1">
                    <span class="text-[9px] px-2 py-0.5 rounded-full font-bold st-{{ i.st }}">{{ i.st }}</span>
                    <h3 class="text-lg font-bold text-slate-800 tracking-tight">{{ i.name }}</h3>
                </div>
                <div class="text-orange-200">▶</div>
            </a>
            {% endfor %}
        </div>
        {% endif %}
    </div>

    {% if r == 'o' %}
    <button onclick="document.getElementById('m').style.display='block'" class="fixed bottom-6 right-6 w-16 h-16 bg-slate-800 text-white rounded-full shadow-2xl text-3xl font-light">+</button>
    <div id="m" class="modal">
        <div class="m-content shadow-2xl">
            <div class="flex justify-between items-center mb-6"><h3 class="text-xl font-bold">店舗情報 入力フォーム</h3><button onclick="document.getElementById('m').style.display='none'" class="text-slate-400">Cancel</button></div>
            <form onsubmit="cp(event)" class="space-y-4 pb-8">
                <input type="text" id="fn" placeholder="正式な店名 *" required class="w-full p-4 rounded-2xl bg-slate-50 border outline-none focus:border-orange-500">
                <select id="fs" class="w-full p-4 rounded-2xl bg-slate-50 border font-bold">
                    <option value="営業中">営業中</option>
                    <option value="準備中">準備中</option>
                </select>
                <textarea id="fm" placeholder="支援者へのメッセージ" class="w-full p-4 rounded-2xl bg-slate-50 border h-28 outline-none focus:border-orange-500"></textarea>
                <input type="url" id="fi" placeholder="画像URL（Instagramなど）" class="w-full p-4 rounded-2xl bg-slate-50 border outline-none focus:border-orange-500">
                <button type="submit" class="w-full py-5 bg-slate-800 text-white rounded-2xl font-bold text-lg shadow-xl active:scale-95 transition">この内容をコピー</button>
            </form>
        </div>
    </div>
    <script>
        function cp(e){
            e.preventDefault();
            const r = `【掲載申請】\\n店名: ${document.getElementById('fn').value}\\n状況: ${document.getElementById('fs').value}\\nメッセージ: ${document.getElementById('fm').value}\\n画像URL: ${document.getElementById('fi').value}`;
            navigator.clipboard.writeText(r);
            alert('コピーしました！この内容を管理者に送ってください。管理者がシートに反映次第、サイトに表示されます。');
            document.getElementById('m').style.display='none';
        }
    </script>
    {% endif %}
</body>
</html>
"""

@app.route('/')
def index():
    r = request.args.get('r', 's')
    df, _ = get_data()
    all_s = df.to_dict(orient='records') if not df.empty else []
    return render_template_string(LAYOUT, r=r, all=all_s)

@app.route('/shop/<sid>')
def shop(sid):
    r = request.args.get('r', 's')
    df, c_df = get_data()
    row = df[df['id'] == str(sid)]
    if row.empty: return "お店が見つかりません", 404
    cms = c_df[c_df['店舗ID'].astype(str) == str(sid)].to_dict(orient='records')
    return render_template_string(LAYOUT, r=r, shop=row.iloc[0].to_dict(), comments=cms)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
