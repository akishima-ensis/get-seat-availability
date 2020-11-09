import requests
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta, timezone

# debug
# cred = credentials.Certificate('serviceAccountKey.json')
# firebase_admin.initialize_app(cred)

if len(firebase_admin._apps) == 0:
    firebase_admin.initialize_app()

db = firestore.client()

target_url = 'https://webreserv.library.akishima.tokyo.jp/webReserv/AreaInfo/Login'

'''
room_data
〜〜〜〜〜
name - 部屋の名前
status_code - 部屋の状態
    0: 空席有
    1: 満席
    2: 開館前
    3: 休館日
    4: データ取得の失敗
seats_num: 空席数
web_seats_num: web予約可能空席数
total_seats_num: 総座席数
update: サイト内更新時間
'''
room_data = {
    '1': {
        'name': '学習席（有線LAN有）',
        'status_code': 4,
        'seats_num': 0,
        'web_seats_num': 0,
        'total_seats_num': 0,
        'update': '0000/00/00 00:00'
    },

    '2': {
        'name': '学習席',
        'status_code': 4,
        'seats_num': 0,
        'web_seats_num': 0,
        'total_seats_num': 0,
        'update': '0000/00/00 00:00'
    },

    '3': {
        'name': '研究個室',
        'status_code': 4,
        'seats_num': 0,
        'web_seats_num': 0,
        'total_seats_num': 0,
        'update': '0000/00/00 00:00'
    },

    '4': {
        'name': 'インターネット・DB席',
        'status_code': 4,
        'seats_num': 0,
        'web_seats_num': 0,
        'total_seats_num': 0,
        'update': '0000/00/00 00:00'
    },

    '5': {
        'name': 'グループ学習室',
        'status_code': 4,
        'seats_num': 0,
        'web_seats_num': 0,
        'total_seats_num': 0,
        'update': '0000/00/00 00:00'
    },

    '6': {
        'name': 'ティーンズ学習室',
        'status_code': 4,
        'seats_num': 0,
        'web_seats_num': 0,
        'total_seats_num': 0,
        'update': '0000/00/00 00:00'
    },
}


def get_room_data():

    # ステータスコードが200以外だったらなんもしないで返す
    r = requests.get(target_url)
    if r.status_code != 200:
        return

    soup = BeautifulSoup(r.text, 'lxml')

    # 座席情報の取得
    data = soup.find(class_='seat').find_all('tr')

    # 更新時間の取得
    update_str = soup.find(class_='check_date text-danger').text
    update_strptime = datetime.strptime(update_str, '%Y/%m/%d %H:%M 更新')
    update = update_strptime.strftime('%Y/%m/%d %H:%M')

    for room_id in room_data:
        seats_data = [i.text for i in data[int(room_id)].find_all('div')]

        # 座席ステータス
        if seats_data[0] == '満\u3000席':
            room_data[room_id]['status_code'] = 1
        elif seats_data[0] == '開館前':
            room_data[room_id]['status_code'] = 2
        elif seats_data[0] == '休館日':
            room_data[room_id]['status_code'] = 3
        else:
            room_data[room_id]['status_code'] = 0

            # 空席数
            room_data[room_id]['seats_num'] = int(seats_data[0])

        # web空き情報
        if seats_data[1] != '':
            room_data[room_id]['web_seats_num'] = int(seats_data[1])

        # 座席総数
        room_data[room_id]['total_seats_num'] = int(seats_data[2])

        # サイト内更新時間
        room_data[room_id]['update'] = update


def save_room_data_to_firestore(Request):

    # 空席情報の取得
    get_room_data()

    jst = timezone(timedelta(hours=+9), 'JST')
    now = datetime.now(jst)
    date = now.strftime('%Y%m%d')
    time = now.strftime('%H%M')

    # ドキュメントの存在確認にしてデータを保存
    doc_ref = db.collection('room').document(date)
    doc = doc_ref.get()
    if doc.exists:
        db.collection('room').document(date).update({time: room_data})
    else:
        db.collection('room').document(date).set({time: room_data})

    return 'ok'


# debug
# save_room_data_to_firestore('ok')