import pandas as pd
from flask import Flask, render_template_string, abort

app = Flask(__name__)

# --- 設定：スプレッドシートの情報 ---
# シート全体のID
SHEET_ID = "1incBINNVhc64m6oRNCIKgkhMrUOTnUUF3v5MfS8eFkg"
# Sheet2を指定してCSV形式で取得するURL
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet2"

def get_all_data():
    """スプレッドシートから全データを読み込む"""
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip()
        return df.fillna("未設定")
    except Exception as e:
        print(f"読み込みエラー: {e}")
        return None

# --- HTML デザイン (共通レイアウト) ---
LAYOUT = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <title>復興支援ポータル</title>
</head>
<body class="bg-slate-50 min-h-screen text-slate-800 pb-10">
    <nav class="bg-blue-700 text-white p-4 mb-6 shadow-md font-bold text-center text-lg">
        <a href="/">復興支援ポータル</a>
    </nav>
    <div class="max-w-md mx-auto px-4">
        {% if shop %}
        <div class="bg-white rounded-2xl shadow-sm border overflow-hidden">
            <img src="{{ shop.image_url }}" class="w-full h-52 object-cover" onerror="this.src='https://via.placeholder.com/400x250?text=No+Image'">
            <div class="p-6">
                <div class="flex justify-between items-center mb-4">
                    <h1 class="text-2xl font-bold text-slate-900">{{ shop.name }}</h1>
                    <span class="text-xs px-2 py-1 rounded bg-emerald-100 text-emerald-600 font-bold border border-emerald-200">
                        {{ shop.status }}
                    </span>
                </div>
                <p class="text-sm text-slate-600 mb-6 leading-relaxed">{{ shop.message }}</p>
                <div class="bg-blue-50 p-4 rounded-xl mb-6 text-sm border border-blue-100">
                    <p class="font-bold text-blue-800 mb-1">✨ おすすめ</p>
                    <p class="text-slate-700">{{ shop.recommendation }}</p>
                </div>
                <div class="grid grid-cols-2 gap-3">
                    <a href="{{ shop.map_url }}" target="_blank" class="bg-slate-100 text-center py-3 rounded-xl font
