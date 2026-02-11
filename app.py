import pandas as pd
from flask import Flask, render_template_string
import os

app = Flask(__name__)

# --- 設定 ---
SHEET_ID = "1incBINNVhc64m6oRNCIKgkhMrUOTnUUF3v5MfS8eFkg"
# Sheet2を指定
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet2"

def get_all_data():
    try:
        # 1. データを読み込む（2行目を項目名として指定）
        df = pd.read_csv(SHEET_URL, header=1)
        
        # 2. 列名の空白を削除
        df.columns = df.columns.str.strip()
        
        # 3. 日本語の項目名をプログラム用の英語名に変換
        # シートの列：ID, 店名, 画像URL, 状況, メッセージ, おすすめ, 通販URL, 地図URL
        mapping = {
            'ID': 'id', '店名': 'name', '画像URL': 'image_url',
            '状況': 'status', 'メッセージ': 'message',
            'おすすめ': 'recommendation', '通販URL': 'ec_url', '地図URL': 'map_url'
        }
        df = df.rename(columns=mapping)
        
        # 4. 「店名」が入っていない行を削除
        if 'name' in df.columns:
            df = df.dropna(subset=['name'])
        else:
            # 万が一列名が認識できなかった時のための緊急回避
            return "スプレッドシートの2行目に『店名』という列が見つかりません。"
        
        # 5. IDをきれいな文字列にする
        if 'id' in df.columns:
            df['id'] = df['id'].astype(str).str.replace('.0', '', regex=False).str.strip()
        
        return df.fillna("未設定")
    except Exception as e:
        return f"読み込みエラー: {str(e)}"

# --- HTML デザイン ---
LAYOUT = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <title>能登復興支援ポータル</title>
</head>
<body class="bg-slate-50 min-h-screen text-slate-800 pb-10">
    <nav class="bg-blue-800 text-white p-4 mb-6 shadow-md font-bold text-center text-lg">
        <a href="/">能登復興支援ポータル</a>
    </nav>
    <div class="max-w-md mx-auto px-4">
        {% if error_msg %}
            <div class="bg-red-50 border border-red-200 p-4 rounded-xl text-red-600 text-sm">
                <strong>エラーが発生しました:</strong><br>{{ error_msg }}
            </div>
        {% elif shop %}
            <div class="bg-white rounded-2xl shadow-lg border overflow-hidden">
                <img src="{{ shop.image_url }}" class="w-full h-56 object-cover" onerror="this.src='https://via.placeholder.com/400x250?text=No+Image'">
                <div class="p-6">
                    <h1 class="text-2xl font-bold mb-2">{{ shop.name }}</h1>
                    <span class="inline-block mb-4 text-xs px-2 py-1 rounded bg-emerald-100 text-emerald-700 font-bold border border-emerald-200">
                        {{ shop.status }}
                    </span>
                    <p class="text-sm text-slate-600 mb-6 leading-relaxed">{{ shop.message }}</p>
                    <div class="bg-blue-50 p-4 rounded-xl mb-6 text-sm border border-blue-100">
                        <p class="font-bold text-blue-800 mb-1">✨ おすすめ商品</p>
                        <p class="text-slate-700">{{ shop.recommendation }}</p>
                    </div>
                    <div class="grid grid-cols-2 gap-3 mb-6">
                        <a href="{{ shop.map_url }}" target="_blank" class="bg-slate-100 text-center py-3 rounded-xl font-bold text-sm">地図</a>
                        <a href="{{ shop.ec_url }}" target="_blank" class="bg-blue-600 text-white text-center py-3 rounded-xl font-bold text-sm shadow-md">通販</a>
                    </div>
                    <a href="/" class="block text-center text-xs text-slate-400">← 一覧に戻る</a>
                </div>
            </div>
        {% else %}
            <div class="bg-white rounded-2xl shadow-md border p-6">
                <h2 class="text-lg font-bold mb-4 text-center border-b pb-2">応援するお店を選ぶ</h2>
                <div class="space-y-3">
