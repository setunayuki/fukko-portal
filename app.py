import pandas as pd
from flask import Flask, render_template_string, request
import os

app = Flask(__name__)

# --- 設定：スプレッドシート情報 ---
SID = "1incBINNVhc64m6oRNCIKgkhMrUOTnUUF3v5MfS8eFkg"
# 店舗データ(Sheet2)と評価データ(Sheet3)
S2_URL = f"https://docs.google.com/spreadsheets/d/{SID}/export?format=csv&gid=1191908203"
S3_URL = f"https://docs.google.com/spreadsheets/d/{SID}/export?format=csv&gid=317117230"

# Googleフォーム送信先（事業者用）
FORM_ACTION_URL = "https://docs.google.com/forms/d/e/1FAIpQLSd7S7pBqS9YQWfLzX6vG7D6-9W3Z2M8y_Rj-ZJp-Xz5nK9p3A/formResponse"

def get_data():
    try:
        # --- Sheet2 (店舗情報) の読み込み ---
        # 1行目は説明文（A2, B2...）があるため、データ本体から読み込むように調整
        df_raw = pd.read_csv(S2_URL, engine='c')
        # 「id」が含まれる行を探して、そこから下のデータを取得
        df = df_raw.iloc[0:].copy() 
        df.columns = ['cell_info', 'item_name', 'value'] # 一旦仮の名前
        
        # 縦持ちデータを横持ちに変換（またはシンプルにマッピング）
        # ※送っていただいたSheet2の構造に合わせ、特定の行からデータを抽出します
        # ここでは以前の成功パターンに基づき、直接列を割り当てます
        df_final = pd.read_csv(S2_URL, skiprows=1, engine='c') 
        df_final.columns = ['cell', 'col_name', 'val']
        
        # --- Sheet3 (評価/コメント) の読み込み ---
        # 送っていただいたCSV: A列=店舗ID, B列=星評価, C列=コメント
        c_df = pd.read_csv(S3_URL, skiprows=1, engine='c')
        c_df.columns = ['店舗ID', '星評価', 'コメント']
        # 文字列に変換して照合しやすくする
        c_df['店舗ID'] = c_df['店舗ID'].astype(str).str.strip()
            
        # 店舗一覧用のダミーデータ（実際の運用ではSheet2の構造に合わせてループさせます）
        # テスト用にID: 2132 の店舗を表示できるように設定
        shops = [
            {'id': '2132', 'name': 'テスト店舗', 'img': 'https://via.placeholder.com/400x250', 'st': '営業中', 'msg': '応援ありがとうございます！'}
        ]
            
        return shops, c_df.fillna("")
    except Exception as e:
        print(f"Error: {e}")
        return [], pd.DataFrame()

LAYOUT = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <title>復興ポータル</title>
    <style>
        body { background-color: #fffaf0; }
        .st-営業中 { background-color: #dcfce7; color: #166534; }
        .st-準備中 { background-color: #fee2e2; color: #991b1b; }
    </style>
</head>
<body class="pb-20">
    <nav class="bg-orange-600 text-white p-5 text-center font-bold shadow-lg">復興支援ポータル</nav>
    
    <div class="flex bg-white shadow-sm mb-6">
        <a href="/?r=s" class="flex-1 py-4 text-center {{ 'text-orange-600 border-b-4 border-orange-600' if r == 's' else 'text-slate-400' }}">支援者</a>
        <a href="/?r=o" class="flex-1 py-4 text-center {{ 'text-orange-600 border-b-4 border-orange-600' if r == 'o' else 'text-slate-400' }}">事業者</a>
    </div>

    <div class="max-w-md mx-auto px-4">
        {% if r == 'o' %}
        <div class="bg-white p-8 rounded-3xl shadow-xl text-center">
            <h2 class="font-bold text-lg mb-4">お店の登録</h2>
            <p class="text-sm text-slate-500 mb-8">右下の「＋」から入力して送信してください。</p>
        </div>
        {% elif s %}
        <div class="bg-white rounded-3xl shadow-xl overflow-hidden border-t-8 border-orange-500 p-6">
            <h2 class="text-2xl font-bold mb-4">{{ s.name }}</h2>
            <span class="inline-block px-3 py-1 rounded-full text-xs font-bold st-{{ s.st }} mb-4">{{ s.st }}</span>
            <p class="bg-orange-50 p-4 rounded-xl text-sm italic mb-8">「{{ s.msg }}」</p>
            
            <div class="border-t pt-6">
                <h3 class="font-bold text-blue-600 mb-4">📣 支援者からの声（Sheet3より）</h3>
                {% if cms %}
                    {% for c in cms %}
                    <div class="mb-4 p-4 bg-blue-50/50 rounded-xl border border-blue-100">
                        <div class="text-orange-400 font-bold text-xs mb-1">評価: ⭐ {{ c['星評価'] }}</div>
                        <p class="text-slate-700 text-sm">{{ c['コメント'] }}</p>
                    </div>
                    {% endfor %}
                {% else %}
                    <p class="text-slate-400 text-xs italic">まだコメントはありません。</p>
                {% endif %}
            </div>
        </div>
        <a href="/?r=s" class="block text-center mt-6 text-slate-400 text-sm underline">一覧に戻る</a>
        {% else %}
        <div class="space-y-4">
            {% for i in all_s %}
            <a href="/shop/{{ i.id }}?r=s" class="flex items-center p-4 bg-white rounded-2xl shadow border">
                <div class="flex-1">
                    <h3 class="font-bold text-slate-800">{{ i.name }}</h3>
                    <span class="text-[10px] st-{{ i.st }} px-2 rounded">{{ i.st }}</span>
                </div>
                <div class="text-orange-300">▶</div>
            </a>
            {% endfor %}
        </div>
        {% endif %}
    </div>

    {% if r == 'o' %}
    <button onclick="document.getElementById('m').style.display='block'" class="fixed bottom-6 right-6 w-16 h-16 bg-slate-800 text-white rounded-full text-3xl shadow-2xl">+</button>
    <div id="m" class="fixed inset-0 bg-black/50 hidden z-50">
        <div class="absolute bottom-0 w-full bg-white p-8 rounded-t-3xl">
            <form action="{{ f_url }}" method="POST" target="_blank" onsubmit="location.reload();" class="space-y-4">
                <input type="text" name="entry.1643444005" placeholder="店名" required class="w-full p-4 border rounded-xl">
                <button type="submit" class="w-full py-4 bg-slate-800 text-white rounded-xl font-bold">送信して公開</button>
            </form>
            <button onclick="document.getElementById('m').style.display='none'" class="w-full mt-2 text-slate-400 text-sm">閉じる</button>
        </div>
    </div>
    {% endif %}
</body>
</html>
"""

@app.route('/')
def index():
    r = request.args.get('r', 's')
    shops, _ = get_data()
    return render_template_string(LAYOUT, r=r, all_s=shops, f_url=FORM_ACTION_URL)

@app.route('/shop/<sid>')
def shop(sid):
    shops, c_df = get_data()
    # 対象の店舗を取得
    s = next((item for item in shops if item["id"] == str(sid)), None)
    if not s: return "店舗が見つかりません", 404
    
    # Sheet3からこの店舗IDに一致するコメントを抽出
    cms = c_df[c_df['店舗ID'].astype(str) == str(sid)].to_dict(orient='records')
    return render_template_string(LAYOUT, r='s', s=s, cms=cms)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
