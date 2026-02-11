import pandas as pd
from flask import Flask, render_template_string, request
import os

app = Flask(__name__)

# --- 設定：スプレッドシート情報 ---
SID = "1incBINNVhc64m6oRNCIKgkhMrUOTnUUF3v5MfS8eFkg"
# 店舗データ(Sheet2)と評価データ(Sheet3)のCSV出力URL
S2_URL = f"https://docs.google.com/spreadsheets/d/{SID}/export?format=csv&gid=1191908203"
S3_URL = f"https://docs.google.com/spreadsheets/d/{SID}/export?format=csv&gid=317117230"

# Googleフォーム送信先（事業者用）
FORM_ACTION_URL = "https://docs.google.com/forms/d/e/1FAIpQLSd7S7pBqS9YQWfLzX6vG7D6-9W3Z2M8y_Rj-ZJp-Xz5nK9p3A/formResponse"

def get_data():
    try:
        # --- Sheet2 (店舗情報) の読み込み ---
        # 2行目のヘッダー(ID, 店名等)を基準に読み込み
        df = pd.read_csv(S2_URL, skiprows=1, engine='c')
        df.columns = ['id', 'name', 'img', 'st', 'msg', 'rec', 'ec', 'map']
        df['id'] = df['id'].astype(str).str.strip()
        
        # --- Sheet3 (評価/コメント) の読み込み ---
        # A列=店舗ID, B列=星評価, C列=コメント
        c_df = pd.read_csv(S3_URL, skiprows=1, engine='c')
        c_df.columns = ['店舗ID', '星評価', 'コメント']
        c_df['店舗ID'] = c_df['店舗ID'].astype(str).str.strip()
            
        return df.fillna(""), c_df.fillna("")
    except Exception as e:
        print(f"Error: {e}")
        return pd.DataFrame(), pd.DataFrame()

LAYOUT = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <title>復興支援ポータル</title>
    <style>
        body { background-color: #fffaf0; }
        .st-営業中 { background-color: #dcfce7; color: #166534; }
        .st-準備中 { background-color: #fee2e2; color: #991b1b; }
        .st-営業予定 { background-color: #fef9c3; color: #854d0e; }
    </style>
</head>
<body class="pb-20 font-sans">
    <nav class="bg-orange-600 text-white p-5 text-center font-bold shadow-lg text-lg">復興支援ポータル</nav>
    
    <div class="flex bg-white shadow-sm mb-6">
        <a href="/?r=s" class="flex-1 py-4 text-center {{ 'text-orange-600 border-b-4 border-orange-600 font-bold' if r == 's' else 'text-slate-400' }}">支援者として利用</a>
        <a href="/?r=o" class="flex-1 py-4 text-center {{ 'text-orange-600 border-b-4 border-orange-600 font-bold' if r == 'o' else 'text-slate-400' }}">事業者として利用</a>
    </div>

    <div class="max-w-md mx-auto px-4">
        {% if r == 'o' %}
        <div class="bg-white p-8 rounded-3xl shadow-xl text-center border-t-8 border-slate-800">
            <h2 class="font-bold text-lg mb-4 text-slate-800 italic">事業者の方へ</h2>
            <p class="text-sm text-slate-500 mb-8 leading-relaxed">
                右下の「＋」ボタンからお店を登録してください。<br>
                送信された内容は自動的にスプレッドシートに保存されます。
            </p>
        </div>
        {% elif s %}
        <div class="bg-white rounded-3xl shadow-xl overflow-hidden border-t-8 border-orange-500 p-8">
            <span class="inline-block px-3 py-1 rounded-full text-xs font-bold st-{{ s.st }} mb-4">{{ s.st }}</span>
            <h2 class="text-3xl font-black mb-4">{{ s.name }}</h2>
            <div class="bg-orange-50 p-5 rounded-2xl text-sm italic mb-10 text-slate-600 leading-relaxed">
                「{{ s.msg }}」
            </div>
            
            <div class="border-t pt-8">
                <h3 class="text-lg font-bold text-blue-600 mb-6 italic tracking-tight text-center">📣 支援者からの応援メッセージ</h3>
                <div class="space-y-4">
                {% if cms %}
                    {% for c in cms %}
                    <div class="p-4 bg-blue-50/50 rounded-2xl border border-blue-100 shadow-sm">
                        <div class="text-orange-400 text-xs mb-1 font-bold">
                            評価: {{ "⭐" * c['星評価']|int }} ({{ c['星評価'] }})
                        </div>
                        <p class="text-slate-700 text-sm leading-relaxed font-medium">{{ c['コメント'] }}</p>
                    </div>
                    {% endfor %}
                {% else %}
                    <p class="text-xs text-slate-400 italic text-center py-6">まだ応援コメントはありません。最初の一件を募集中です！</p>
                {% endif %}
                </div>
            </div>
        </div>
        <a href="/?r=s" class="block text-center mt-10 text-slate-400 text-sm font-bold underline">← お店一覧に戻る</a>
        {% else %}
        <div class="space-y-4">
            <p class="text-center text-slate-400 text-[10px] font-bold tracking-widest uppercase mb-4">復興を応援したいお店を選んでください</p>
            {% for i in all_s %}
            <a href="/shop/{{ i.id }}?r=s" class="flex items-center p-5 bg-white rounded-3xl shadow-sm border border-orange-50 active:scale-95 transition">
                <div class="flex-1">
                    <span class="text-[9px] font-bold st-{{ i.st }} px-2 py-0.5 rounded-full mb-1 inline-block">{{ i.st }}</span>
                    <h3 class="text-xl font-bold text-slate-800 tracking-tight">{{ i.name }}</h3>
                </div>
                <div class="text-orange-200 text-xl font-bold">▶</div>
            </a>
            {% endfor %}
        </div>
        {% endif %}
    </div>

    {% if r == 'o' %}
    <button onclick="document.getElementById('m').style.display='block'" class="fixed bottom-6 right-6 w-16 h-16 bg-slate-800 text-white rounded-full text-4xl shadow-2xl active:scale-90 transition">+</button>
    <div id="m" class="fixed inset-0 bg-black/50 hidden z-50 flex items-end justify-center">
        <div class="w-full max-w-md bg-white p-8 rounded-t-3xl shadow-2xl animate-slide-up">
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-xl font-bold text-slate-800">お店の情報を入力</h3>
                <button onclick="document.getElementById('m').style.display='none'" class="text-slate-300 text-sm">閉じる</button>
            </div>
            <form action="{{ f_url }}" method="POST" target="_blank" onsubmit="setTimeout(()=>location.reload(), 1000);" class="space-y-4">
                <input type="text" name="entry.1643444005" placeholder="店名 *" required class="w-full p-4 rounded-2xl bg-slate-50 border-none focus:ring-2 focus:ring-orange-500 outline-none">
                <select name="entry.198308709" class="w-full p-4 rounded-2xl bg-slate-50 border-none outline-none font-bold">
                    <option value="営業中">営業中</option>
                    <option value="準備中">準備中</option>
                    <option value="営業予定">営業予定</option>
                </select>
                <textarea name="entry.1448093113" placeholder="メッセージ" class="w-full p-4 rounded-2xl bg-slate-50 border-none h-28 outline-none"></textarea>
                <button type="submit" class="w-full py-5 bg-orange-600 text-white rounded-2xl font-bold text-lg shadow-xl active:scale-95 transition">送信してサイトに公開</button>
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
    shops = df.to_dict(orient='records') if not df.empty else []
    return render_template_string(LAYOUT, r=r, all_s=shops, f_url=FORM_ACTION_URL)

@app.route('/shop/<sid>')
def shop(sid):
    df, c_df = get_data()
    # 対象の店舗を取得
    s_row = df[df['id'] == str(sid)]
    if s_row.empty: return "店舗が見つかりません", 404
    
    s = s_row.iloc[0].to_dict()
    # Sheet3からこの店舗IDに一致するコメントを抽出
    cms = c_df[c_df['店舗ID'].astype(str) == str(sid)].to_dict(orient='records')
    return render_template_string(LAYOUT, r='s', s=s, cms=cms)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
