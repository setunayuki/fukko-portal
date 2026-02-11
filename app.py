import pandas as pd
from flask import Flask, render_template_string, request
import os

app = Flask(__name__)

# --- 設定：スプレッドシート情報 ---
SID = "1incBINNVhc64m6oRNCIKgkhMrUOTnUUF3v5MfS8eFkg"
# 店舗データ(Sheet2)とコメントデータ(Sheet3)のCSV出力先
S2_URL = f"https://docs.google.com/spreadsheets/d/{SID}/export?format=csv&gid=1191908203"
S3_URL = f"https://docs.google.com/spreadsheets/d/{SID}/export?format=csv&gid=317117230"

# --- 設定：Googleフォーム送信先 ---
FORM_ACTION_URL = "https://docs.google.com/forms/d/e/1FAIpQLSd7S7pBqS9YQWfLzX6vG7D6-9W3Z2M8y_Rj-ZJp-Xz5nK9p3A/formResponse"

def get_data():
    try:
        # 店舗情報(Sheet2)の読み込み。engine='c'で高速化しタイムアウト対策
        df = pd.read_csv(S2_URL, header=1, engine='c')
        df.columns = df.columns.str.strip()
        m = {'ID':'id','店名':'name','画像URL':'img','状況':'st','メッセージ':'msg','おすすめ':'rec','通販URL':'ec'}
        df = df.rename(columns=m).dropna(subset=['name'])
        df['id'] = df['id'].astype(str).str.replace('.0', '', regex=False).str.strip()
        
        # 応援コメント(Sheet3)の読み込み
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
        .st-営業中 { background-color: #dcfce7; color: #166534; border: 1px solid #86efac; }
        .st-準備中 { background-color: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; }
        .st-営業予定 { background-color: #fef9c3; color: #854d0e; border: 1px solid #fde047; }
        .modal { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.4); z-index: 50; }
        .m-content { position: absolute; bottom: 0; width: 100%; max-width: 500px; left: 50%; transform: translateX(-50%); background: white; border-radius: 24px 24px 0 0; padding: 24px; max-height: 90vh; overflow-y: auto; }
    </style>
</head>
<body class="pb-20">
    <nav class="bg-orange-600 text-white p-5 text-center font-bold shadow-lg text-lg">能登復興支援ポータル</nav>
    
    <div class="flex bg-white shadow-sm mb-8 sticky top-0 z-10">
        <a href="/?r=s" class="flex-1 py-4 text-center {{ 'text-orange-600 border-b-4 border-orange-600 font-bold' if r == 's' else 'text-slate-400' }}">支援者</a>
        <a href="/?r=o" class="flex-1 py-4 text-center {{ 'text-orange-600 border-b-4 border-orange-600 font-bold' if r == 'o' else 'text-slate-400' }}">事業者</a>
    </div>

    <div class="max-w-md mx-auto px-4">
        {% if r == 'o' %}
        <div class="bg-white p-8 rounded-3xl shadow-xl border-t-8 border-slate-800 text-center">
            <h2 class="font-bold text-xl mb-4 text-slate-800">お店の掲載申請</h2>
            <p class="text-sm text-slate-500 mb-8 leading-relaxed">右下の「＋」から情報を入力してください。<br>送信すると自動でサイトに反映されます。</p>
        </div>
        {% elif shop %}
        <div class="bg-white rounded-3xl shadow-xl overflow-hidden border-t-8 border-orange-500 mb-8">
            <img src="{{ shop.img }}" class="w-full h-56 object-cover" onerror="this.src='https://via.placeholder.com/400x250?text=No+Photo'">
            <div class="p-8">
                <span class="inline-block px-3 py-1 rounded-full text-xs font-bold st-{{ shop.st }} mb-4">{{ shop.st }}</span>
                <h2 class="text-2xl font-black mb-4">{{ shop.name }}</h2>
                <div class="bg-orange-50 p-4 rounded-xl text-sm italic mb-10 text-slate-600">「{{ shop.msg }}」</div>
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
                        <p class="text-xs text-slate-400 italic text-center py-4">コメント募集中！</p>
                    {% endif %}
                </div>
            </div>
        </div>
        <a href="/?r=s" class="block text-center text-xs text-slate-400 font-bold mb-10 underline">一覧へ戻る</a>
        {% else %}
        <div class="space-y-4">
            {% for i in all %}
            <a href="/shop/{{ i.id }}?r=s" class="flex items-center p-4 bg-white rounded-2xl shadow-md border border-orange-50 active:scale-95 transition">
                <div class="w-14 h-14 rounded-xl overflow-hidden shrink-0 border"><img src="{{ i.img }}" class="w-full h-full object-cover" onerror="this.src='https://via.placeholder.com/100'"></div>
                <div class="ml-4 flex-1">
                    <span class="text-[9px] px-2 py-0.5 rounded-full font-bold st-{{ i.st }}">{{ i.st }}</span>
                    <h3 class="text-lg font-bold text-slate-800 tracking-tight">{{ i.name }}</h3>
                </div>
                <div class="text-orange-200 font-bold text-lg">▶</div>
            </a>
            {% endfor %}
        </div>
        {% endif %}
    </div>

    {% if r == 'o' %}
    <button onclick="document.getElementById('m').style.display='block'" class="fixed bottom-6 right-6 w-16 h-16 bg-slate-800 text-white rounded-full shadow-2xl text-4xl active:scale-90 transition">+</button>
    <div id="m" class="modal">
        <div class="m-content shadow-2xl">
            <div class="flex justify-between items-center mb-6"><h3 class="text-xl font-bold text-slate-800">掲載情報を入力</h3><button onclick="document.getElementById('m').style.display='none'" class="text-slate-400 text-sm">Cancel</button></div>
            <form action="{{ form_url }}" method="POST" target="_blank" onsubmit="alert('送信完了！数分で反映されます。');document.getElementById('m').style.display='none';" class="space-y-4 pb-10">
                <input type="text" name="entry.1643444005" placeholder="店名 *" required class="w-full p-4 rounded-2xl bg-slate-50 border outline-none focus:border-orange-500">
                <select name="entry.198308709" class="w-full p-4 rounded-2xl bg-slate-50 border font-bold">
                    <option value="営業中">営業中</option>
                    <option value="営業予定">営業予定</option>
                    <option value="準備中">準備中</option>
                </select>
                <textarea name="entry.1448093113" placeholder="支援者へのメッセージ" class="w-full p-4 rounded-2xl bg-slate-50 border h-28 outline-none focus:border-orange-500"></textarea>
                <input type="url" name="entry.669818856" placeholder="画像URL" class="w-full p-4 rounded-2xl bg-slate-50 border outline-none">
                <button type="submit" class="w-full py-5 bg-slate-800 text-white rounded-2xl font-bold text-lg shadow-xl">保存して公開する</button>
            </form>
        </div>
    </div>
    {% endif %}
</body>
</html>
"""

@app.route('/')
def index():
    r = request.args.get('r', 's')
    df, _ = get_data()
    all_s = df.to_dict(orient='records') if not df.empty else []
    return render_template_string(LAYOUT, r=r, all=all_s, form_url=FORM_ACTION_URL)

@app.route('/shop/<sid>')
def shop(sid):
    r = request.args.get('r', 's')
    df, c_df = get_data()
    row = df[df['id'] == str(sid)]
    if row.empty: return "Not Found", 404
    cms = c_df[c_df['店舗ID'].astype(str) == str(sid)].to_dict(orient='records')
    return render_template_string(LAYOUT, r=r, shop=row.iloc[0].to_dict(), comments=cms)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
