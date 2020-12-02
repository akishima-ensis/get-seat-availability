import os
import re
import requests
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta, timezone


# firestoreに保存するかどうかのフラグ
do_save = False

# firestoreに保存するデータの雛形を入れる変数
rooms = []

# スクレイピング対象URL
target_url = 'https://webreserv.library.akishima.tokyo.jp/webReserv/AreaInfo/Login'

# 永続的な接続の確保
session = requests.Session()

# firebase初期化
sa_key_path = 'sa_key.json'
if os.path.exists(sa_key_path):
    cred = credentials.Certificate(sa_key_path)
    firebase_admin.initialize_app(cred)
else:
    firebase_admin.initialize_app()
db = firestore.client()


def init_rooms():
    print('\n### init_rooms ###')
    global rooms
    rooms = [
        {
            'id': 1,
            'name': '学習席（有線LAN有）',
            'seats_num': 0,
            'web_seats_num': 0,
            'total_seats_num': 0,
            'update': '0000/00/00 00:00'
        },
        {
            'id': 2,
            'name': '学習席',
            'seats_num': 0,
            'web_seats_num': 0,
            'total_seats_num': 0,
            'update': '0000/00/00 00:00'
        },
        {
            'id': 3,
            'name': '研究個室',
            'seats_num': 0,
            'web_seats_num': 0,
            'total_seats_num': 0,
            'update': '0000/00/00 00:00'
        },
        {
            'id': 4,
            'name': 'インターネット・DB席',
            'seats_num': 0,
            'web_seats_num': 0,
            'total_seats_num': 0,
            'update': '0000/00/00 00:00'
        },
        {
            'id': 5,
            'name': 'グループ学習室',
            'seats_num': 0,
            'web_seats_num': 0,
            'total_seats_num': 0,
            'update': '0000/00/00 00:00'
        },
        {
            'id': 6,
            'name': 'ティーンズ学習室',
            'seats_num': 0,
            'web_seats_num': 0,
            'total_seats_num': 0,
            'update': '0000/00/00 00:00'
        }
    ]


def get_time():
    jst = timezone(timedelta(hours=+9), 'JST')
    return datetime.now(jst)


def get_seat_data():
    print('\n### get_seat_data ###')

    global do_save
    do_save = True

    # リクエスト
    r = session.get(target_url)
    if r.status_code != 200:
        print(f'* target_urlへのリクエストに失敗しました')
        do_save = False
        return
    print(f'* target_urlへのリクエストに成功しました')

    soup = BeautifulSoup(r.text, 'lxml')

    # 座席情報の取得
    seats = soup.find(class_='seat').find_all('tr')

    # 更新時間の取得
    update_str = soup.find(class_='check_date text-danger').text
    update_str_re = re.findall('\d', update_str)
    if len(update_str_re) == 11:
        update_str_re.insert(8, '0')
    update_strptime = datetime.strptime(''.join(update_str_re), '%Y%m%d%H%M')
    update = update_strptime.strftime('%Y/%m/%d %H:%M')
    print(f'* update: {update}')

    for room in rooms:

        # 各部屋の座席情報を取得
        seat = [i.text for i in seats[room['id']].find_all('div')]

        # 空席数
        if seat[0].isdecimal():
            room['seats_num'] = int(seat[0])
        elif seat[0] == '満\u3000席':
            pass
        else:
            do_save = False
            print('* 現在は閉館時間です')
            return

        # web空き数
        if seat[1].isdecimal():
            room['web_seats_num'] = int(seat[1])

        # 座席総数
        room['total_seats_num'] = int(seat[2])

        # サイト内更新時間
        room['update'] = update


def save_room_data_to_firestore():
    print('\n### save_room_data_to_firestore ###')
    now = get_time()
    date = now.strftime('%Y%m%d')
    time = now.strftime('%H%M')
    rooms_ref = db.collection('rooms').document(date)
    if rooms_ref.get().exists:
        rooms_ref.update({time: rooms})
    else:
        rooms_ref.set({time: rooms})


def delete_room_data_from_firestore():
    print('\n### delete_room_data_from_firestore ###')
    doc_ids = sorted([i.id for i in db.collection('rooms').stream()])
    if len(doc_ids) > 30:
        db.collection('rooms').document(doc_ids[0]).delete()


def run(Request):
    print('run...')

    # 変数の初期化
    init_rooms()

    # 座席情報の取得
    get_seat_data()

    # 座席情報の保存
    if do_save:
        save_room_data_to_firestore()

    # 古い座席情報の削除
    now = get_time()
    if now.hour == 10 and now.minute == 0:
        delete_room_data_from_firestore()

    return 'ok'


# debug
# run(True)