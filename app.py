import pandas as pd
from flask import Flask, render_template_string, request, redirect, url_for
import os
import uuid # ID自動生成用

app = Flask(__name__)

# --- 設定 ---
SHEET_ID = "1incBINNVhc64m6oRNCIKgkhMrUOTnUUF3v5MfS8eFkg"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet2"

def get_all_data():
    try:
        df = pd.read_csv(SHEET_URL, header=1)
        df.columns = df.columns.str.strip()
        mapping = {
            'ID': 'id', '店名': 'name', '画像URL': 'image_url',
            '状況': 'status', 'メッセージ': 'message',
            'おすすめ': 'recommendation', '通販URL': 'ec_url', '地図URL': 'map_url'
        }
        df = df.rename(columns=mapping)
        df = df.dropna(subset=['id', 'name'])
        df['id'] = df['id'].astype(str).str.replace('.0', '', regex=False)
        return df.fillna("未設定")
    except:
        return pd.DataFrame()

# --- HTML デザイン ---
LAYOUT = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <title>復興支援ポータル</title>
    <style>
        body { background-color: #fffaf0; font-family: 'sans-serif'; }
        .status-営業中 { background-color: #d1fae5; color: #065f46; border: 1px solid #6ee7b7; }
        .status-営業予定 { background-color: #fef3c7; color: #92400e; border: 1px solid #fcd34d; }
        .status-準備中 { background-color: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; }
    </style>
</head>
<body class="min-h-screen pb-24">
    <nav class="bg-orange-600 text-white p-6 shadow-lg text-center mb-8">
        <h1 class="text-2xl font-bold"><a href="/">復興支援ポータル</a></h1>
    </nav>

    <div class="max-w-md mx-auto px-4">
        {% if mode == 'form' %}
        <div class="bg-white p-8 rounded-3xl shadow-xl border border-orange-100">
            <h2 class="text-xl font-bold mb-6 text-orange-600">事業者向け：新規登録</h2>
            <form action="/submit" method="POST" class="space-y-4">
                <div>
                    <label class="block text-xs font-bold text-slate-400 mb-1">店名</label>
                    <input type="text" name="name" required class="w-full p-3 rounded-xl bg-slate-50 border focus:border-orange-500 outline-none">
                </div>
                <div>
                    <label class="block text-xs font-bold text-slate-400 mb-1">営業状況</label>
                    <select name="status" class="w-full p-3 rounded-xl bg-slate-50 border">
                        <option value="営業中">営業中</option>
                        <option value="営業予定">営業予定</option>
                        <option value="準備中">準備中</option>
                    </select>
                </div>
                <div>
                    <label class="block text-xs font-bold text-slate-400 mb-1">メッセージ</label>
                    <textarea name="message" class="w-full p-3 rounded-xl bg-slate-50 border"></textarea>
                </div>
                <div>
                    <label class="block text-xs font-bold text-slate-400 mb-1">画像URL</label>
                    <input type="url" name="image_url" class="w-full p-3 rounded-xl bg-slate-50 border">
                </div>
                <button type="submit" class="w-full py-4 bg-orange-500 text-white rounded-2xl font-bold shadow-lg hover:bg-orange-600 transition">
                    この内容で登録する
                </button>
            </form>
        </div>
