import re
import requests
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import firestore
from datetime import datetime, timedelta, timezone


target_url = 'https://webreserv.library.akishima.tokyo.jp/webReserv/AreaInfo/Login'

seats = [
    # - id : 部屋のid
    # - name: 部屋の名前
    # - status_code: 部屋の状態（0: 空席有, 1: 満席,  2: 閉館, 3: 開館前, 4: 休館日 5: データ取得の失敗）
    # - seats_num: 空席数
    # - web_seats_num: web予約可能座席数
    # - total_seats_num: 総座席数
    # - update: サイト内更新時間

    {
        'id': 0,
        'name': '学習席（有線LAN有）',
        'status_code': 5,
        'seats_num': 0,
        'web_seats_num': 0,
        'total_seats_num': 0,
        'update': '0000/00/00 00:00'
    },

    {
        'id': 1,
        'name': '学習席',
        'status_code': 5,
        'seats_num': 0,
        'web_seats_num': 0,
        'total_seats_num': 0,
        'update': '0000/00/00 00:00'
    },

    {
        'id': 2,
        'name': '研究個室',
        'status_code': 5,
        'seats_num': 0,
        'web_seats_num': 0,
        'total_seats_num': 0,
        'update': '0000/00/00 00:00'
    },

    {
        'id': 3,
        'name': 'インターネット・DB席',
        'status_code': 5,
        'seats_num': 0,
        'web_seats_num': 0,
        'total_seats_num': 0,
        'update': '0000/00/00 00:00'
    },

    {
        'id': 4,
        'name': 'グループ学習室',
        'status_code': 5,
        'seats_num': 0,
        'web_seats_num': 0,
        'total_seats_num': 0,
        'update': '0000/00/00 00:00'
    },

    {
        'id': 5,
        'name': 'ティーンズ学習室',
        'status_code': 5,
        'seats_num': 0,
        'web_seats_num': 0,
        'total_seats_num': 0,
        'update': '0000/00/00 00:00'
    }
]


def get_seat_data():

    # ステータスコードが200以外だったらなんもしないで返す
    r = requests.get(target_url)
    if r.status_code != 200:
        return

    soup = BeautifulSoup(r.text, 'lxml')

    # 座席情報の取得
    data = soup.find(class_='seat').find_all('tr')

    # 更新時間の取得
    update_str = soup.find(class_='check_date text-danger').text
    update_str_re = re.findall('\d', update_str)
    if len(update_str_re) == 11:
        update_str_re.insert(7, '0')
    update_strptime = datetime.strptime(''.join(update_str_re), '%Y%m%d%H%M')
    update = update_strptime.strftime('%Y/%m/%d %H:%M')

    for seat_dict in seats:
        seats_data = [i.text for i in data[int(seat_dict['id']) + 1].find_all('div')]

        # 各部屋のdictionaryを取得
        seat = seats[seat_dict['id']]

        # 座席ステータス
        if seats_data[0] == '満\u3000席':
            seat['status_code'] = 1
        elif seats_data[0] == '閉\u3000館':
            seat['status_code'] = 2
        elif seats_data[0] == '開館前':
            seat['status_code'] = 3
        elif seats_data[0] == '休館日':
            seat['status_code'] = 4
        else:
            seat['status_code'] = 0

            # 空席数
            seat['seats_num'] = int(seats_data[0])

        # web空き情報
        if seats_data[1] != '':
            seat['web_seats_num'] = int(seats_data[1])

        # 座席総数
        seat['total_seats_num'] = int(seats_data[2])

        # サイト内更新時間
        seat['update'] = update


def save_seat_data_to_firestore(Request):

    # 空席情報の取得
    get_seat_data()

    # ドキュメント・フィールド名の生成
    jst = timezone(timedelta(hours=+9), 'JST')
    now = datetime.now(jst)
    date = now.strftime('%Y%m%d')
    time = now.strftime('%H%M')

    # firebaseの初期化（デバッグ時は以下2行をコメントアウト）
    if len(firebase_admin._apps) == 0:
        firebase_admin.initialize_app()
    db = firestore.client()

    # ドキュメントの存在確認を行いデータを保存
    doc_ref = db.collection('seat').document(date)
    doc = doc_ref.get()
    if doc.exists:
        db.collection('seat').document(date).update({time: seats})
    else:
        db.collection('seat').document(date).set({time: seats})

    return 'ok'


# debug
# from firebase_admin import credentials
# cred = credentials.Certificate('serviceAccountKey.json')
# firebase_admin.initialize_app(cred)
# save_seat_data_to_firestore('ok')
