import os
import re
import requests
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta, timezone


# firestoreに保存するかどうかのフラグ
do_save = False

# firebase初期化
cred_key = 'serviceAccountKey.json'
if os.path.exists(cred_key):
    cred = credentials.Certificate(cred_key)
    firebase_admin.initialize_app(cred)
else:
    firebase_admin.initialize_app()
db = firestore.client()

# スクレイピング対象URL
target_url = 'https://webreserv.library.akishima.tokyo.jp/webReserv/AreaInfo/Login'

session = requests.Session()

# firestoreに保存するデータの雛形
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

    print('run [get_seat_data]')

    global do_save

    # ステータスコードが200以外だったらなんもしないで返す
    r = session.get(target_url)
    if r.status_code != 200:
        print(f'* target_urlへのリクエストに失敗しました')
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

        # 数字以外、満席以外（閉館、開館前、休館日）だった場合保存フラグをFalseにして返す
        if seat[0].isdecimal():
            do_save = True
            room['seats_num'] = int(seat[0])
        elif seat[0] == '満\u3000席':
            do_save = True
            room['seats_num'] = 0
        else:
            do_save = False
            print('* 現在は閉館時間です')
            return

        # web空き情報
        if seat[1] != '':
            room['web_seats_num'] = int(seat[1])

        # 座席総数
        room['total_seats_num'] = int(seat[2])

        # サイト内更新時間
        room['update'] = update

    print('* 各学習室の空席状況を取得しました')


def save_room_data_to_firestore():

    print('\nrun [save_room_data_to_firestore]')

    # ドキュメント・フィールド名の生成
    now = get_time()
    date = now.strftime('%Y%m%d')
    time = now.strftime('%H%M')

    # ドキュメントの存在確認を行いデータを保存
    rooms_ref = db.collection('rooms').document(date)
    if rooms_ref.get().exists:
        rooms_ref.update({time: rooms})
    else:
        rooms_ref.set({time: rooms})


def delete_room_data_from_firestore():

    print('\nrun [delete_room_data_from_firestore]')

    # ドキュメント数が30を上回ったら一番古いドキュメントを削除する
    doc_ids = sorted([i.id for i in db.collection('rooms').stream()])
    if len(doc_ids) > 30:
        db.collection('rooms').document(doc_ids[0]).delete()


def run(Request):

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