import pandas as pd
from flask import Flask, render_template_string, request
import os

app = Flask(__name__)

# --- 設定：スプレッドシート情報 ---
SID = "1incBINNVhc64m6oRNCIKgkhMrUOTnUUF3v5MfS8eFkg"
# Sheet2 (店舗基本情報) / Sheet3 (支援者のコメント)
S2_URL = f"https://docs.google.com/spreadsheets/d/{SID}/export?format=csv&gid=1191908203"
S3_URL = f"https://docs.google.com/spreadsheets/d/{SID}/export?format=csv&gid=317117230"

def get_data():
    try:
        # 店舗情報の読み込み
        df = pd.read_csv(S2_URL, header=1, engine='c')
        df.columns = df.columns.str.strip()
        mapping = {'ID':'id','店名':'name','画像URL':'img','状況':'st','メッセージ':'msg'}
        df = df.rename(columns=mapping).dropna(subset=['name'])
        df['id'] = df['id'].astype(str).str.replace('.0', '', regex=False).str.strip()
        
        # Sheet3（コメント）の読み込み
        try:
            c_df = pd.read_csv(S3_URL, engine='c')
            c_df.columns = c_df.columns.str.strip()
            # 列名が「店舗ID」「星評価」「コメント」であることを前提にします
        except:
            c_df = pd.DataFrame(columns=['店舗ID', '星評価', 'コメント'])
            
        return df.fillna("未設定"), c_df
    except:
        return pd.DataFrame(), pd.DataFrame()

# --- デザイン ---
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
        .st-準備中 { background-color: #fee2e2; color: #991b1b; }
    </style>
</head>
<body class="pb-20">
    <nav class="bg-orange-600 text-white p-5 text-center font-bold shadow-lg text-lg">復興支援ポータル</nav>
    
    <div class="flex bg-white shadow-sm mb-8">
        <a href="/?r=s" class="flex-1 py-4 text-center {{ 'text-orange-600 border-b-4 border-orange-600 font-bold' if r == 's' else 'text-slate-400' }}">支援者モード</a>
        <a href="/?r=o" class="flex-1 py-4 text-center {{ 'text-orange-600 border-b-4 border-orange-600 font-bold' if r == 'o' else 'text-slate-400' }}">事業者モード</a>
    </div>

    <div class="max-w-md mx-auto px-4">
        {% if r == 'o' %}
        <div class="bg-white p-8 rounded-3xl shadow-xl border-t-8 border-slate-800 text-center">
            <h2 class="font-bold text-lg mb-4 text-slate-800">事業者の方へ</h2>
            <p class="text-sm text-slate-500 leading-relaxed">右下の「＋」から申請内容を作成し、<br>管理者に送って掲載を依頼してください。</p>
        </div>
        {% elif shop %}
        <div class="bg-white rounded-3xl shadow-xl overflow-hidden border-t-8 border-orange-500 mb-8">
            <img src="{{ shop.img }}" class="w-full h-56 object-cover" onerror="this.src='https://via.placeholder.com/400x250?text=No+Photo'">
            <div class="p-8">
                <span class="inline-block px-3 py-1 rounded-full text-xs font-bold st-{{ shop.st }} mb-4">{{ shop.st }}</span>
                <h2 class="text-3xl font-black mb-4">{{ shop.name }}</h2>
                <div class="bg-orange-50 p-4 rounded-xl text-sm italic mb-10">「{{ shop.msg }}」</div>
                
                <div class="pt-6 border-t border-slate-100">
                    <h3 class="text-lg font-bold text-blue-600 mb-6 italic">📣 支援者からの応援コメント</h3>
                    <div class="space-y-4">
                        {% if comments %}
                            {% for c in comments %}
                            <div class="p-4 bg-blue-50/50 rounded-2xl border border-blue-100 shadow-sm">
                                <div class="text-orange-400 text-xs mb-1 font-bold">評価: {{ "⭐" * c['星評価']|int }}</div>
                                <p class="text-slate-700 text-sm leading-relaxed">{{ c['コメント'] }}</p>
                            </div>
                            {% endfor %}
                        {% else %}
                            <p class="text-xs text-slate-400 italic text-center py-4">まだ応援コメントはありません。</p>
                        {% endif %}
                    </div>
                </div>
            </div>
        </div>
        <a href="/?r=s" class="block text-center text-xs text-slate-400 font-bold mb-10">← 他のお店も見る</a>

        {% else %}
        <div class="space-y-4">
            {% for i in all_shops %}
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
    <button onclick="alert('申請用フォームを起動します')" class="fixed bottom-6 right-6 w-16 h-16 bg-slate-800 text-white rounded-full shadow-2xl text-3xl font-light">+</button>
    {% endif %}
</body>
</html>
"""

@app.route('/')
def index():
    r = request.args.get('r', 's')
    df, _ = get_data()
    all_shops = df.to_dict(orient='records') if not df.empty else []
    return render_template_string(LAYOUT, r=r, all_shops=all_shops)

@app.route('/shop/<sid>')
def shop(sid):
    r = request.args.get('r', 's')
    df, c_df = get_data()
    row = df[df['id'] == str(sid)]
    if row.empty: return "お店が見つかりません", 404
    
    # Sheet3からこのお店のIDに一致するコメントを抽出
    cms = c_df[c_df['店舗ID'].astype(str) == str(sid)].to_dict(orient='records')
    
    return render_template_string(LAYOUT, r=r, shop=row.iloc[0].to_dict(), comments=cms)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
