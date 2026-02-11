from flask import Flask, render_template_string

app = Flask(__name__)

# --- データをここに直接書く（スプレッドシートは使いません） ---
SHOP_DATA = {
    "name": "テスト店舗",
    "image_url": "https://via.placeholder.com/400x250",
    "status": "営業中",
    "message": "元気に営業しています！応援よろしくお願いします。",
    "recommendation": "本日のおすすめ商品です。",
    "ec_url": "https://example.com",
    "map_url": "https://goo.gl/maps/example"
}

LAYOUT = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <title>復興支援ポータル</title>
</head>
<body class="bg-slate-50 min-h-screen text-slate-800 pb-10">
    <nav class="bg-blue-700 text-white p-4 mb-6 shadow-md font-bold text-center text-lg">
        復興支援ポータル
    </nav>
    <div class="max-w-md mx-auto px-4">
        <div class="bg-white rounded-2xl shadow-sm border overflow-hidden">
            <img src="{{ shop.image_url }}" class="w-full h-52 object-cover">
            <div class="p-6">
                <div class="flex justify-between items-center mb-4">
                    <h1 class="text-2xl font-bold">{{ shop.name }}</h1>
                    <span class="text-xs px-2 py-1 rounded bg-emerald-100 text-emerald-600 font-bold border border-emerald-200">
                        {{ shop.status }}
                    </span>
                </div>
                <p class="text-sm text-slate-600 mb-6 leading-relaxed">{{ shop.message }}</p>
                <div class="bg-blue-50 p-4 rounded-xl mb-6 text-sm border border-blue-100">
                    <p class="font-bold text-blue-800 mb-1">✨ おすすめ</p>
                    <p>{{ shop.recommendation }}</p>
                </div>
                <div class="grid grid-cols-2 gap-3">
                    <a href="{{ shop.map_url }}" target="_blank" class="bg-slate-100 text-center py-3 rounded-xl font-bold text-sm">地図を表示</a>
                    <a href="{{ shop.ec_url }}" target="_blank" class="bg-blue-600 text-white text-center py-3 rounded-xl font-bold text-sm shadow-md">通販サイト</a>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(LAYOUT, shop=SHOP_DATA)

if __name__ == '__main__':
    app.run()
