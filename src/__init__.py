import os
from typing import Final
from datetime import timedelta, timezone

import requests
import firebase_admin
from firebase_admin import firestore


DEBUG = os.getenv('DEBUG')

# スクレイピング対象URL
url: Final[str] = 'https://webreserv.library.akishima.tokyo.jp/webReserv/AreaInfo/Login'

# ヘッダー
headers = {
    'referer': 'https://www.google.com/',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'
}

# 永続的な接続の確保
session = requests.Session()

# 日本標準時
jst = timezone(timedelta(hours=+9), 'JST')

# firebase初期化
if DEBUG:
    from firebase_admin import credentials
    sa_key_path = './ServiceAccountKey.json'
    cred = credentials.Certificate(sa_key_path)
    firebase_admin.initialize_app(cred)
else:
    firebase_admin.initialize_app()
db = firestore.client()