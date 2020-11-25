import re
import requests
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import firestore
from datetime import datetime, timedelta, timezone


class GetSeatAvailability:

    def __init__(self, debug=False):

        self.debug = debug

        # firestoreに保存するためのフラグ
        self.do_save = False

        # firestore初期化
        self.db = self.initialize_firebase()

        # データ元URL
        self.target_url = 'https://webreserv.library.akishima.tokyo.jp/webReserv/AreaInfo/Login'

        self.rooms = [
            {
                'id': 0,
                'name': '学習席（有線LAN有）',
                'seats_num': 0,
                'web_seats_num': 0,
                'total_seats_num': 0,
                'update': '0000/00/00 00:00'
            },

            {
                'id': 1,
                'name': '学習席',
                'seats_num': 0,
                'web_seats_num': 0,
                'total_seats_num': 0,
                'update': '0000/00/00 00:00'
            },

            {
                'id': 2,
                'name': '研究個室',
                'seats_num': 0,
                'web_seats_num': 0,
                'total_seats_num': 0,
                'update': '0000/00/00 00:00'
            },

            {
                'id': 3,
                'name': 'インターネット・DB席',
                'seats_num': 0,
                'web_seats_num': 0,
                'total_seats_num': 0,
                'update': '0000/00/00 00:00'
            },

            {
                'id': 4,
                'name': 'グループ学習室',
                'seats_num': 0,
                'web_seats_num': 0,
                'total_seats_num': 0,
                'update': '0000/00/00 00:00'
            },

            {
                'id': 5,
                'name': 'ティーンズ学習室',
                'seats_num': 0,
                'web_seats_num': 0,
                'total_seats_num': 0,
                'update': '0000/00/00 00:00'
            }
        ]


    def initialize_firebase(self):
        print('\nrun [initialize_firebase]')

        if self.debug:
            from firebase_admin import credentials
            cred = credentials.Certificate('serviceAccountKey.json')
            firebase_admin.initialize_app(cred)
            return firestore.client()
        else:
            firebase_admin.initialize_app()
            return firestore.client()


    def get_seat_data(self):
        print('\nrun [get_seat_data]')

        # ステータスコードが200以外だったらなんもしないで返す
        r = requests.get(self.target_url)
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

        for room in self.rooms:

            # 各部屋の座席情報を取得
            seat = [i.text for i in seats[room['id'] + 1].find_all('div')]

            # 数字以外、満席以外（閉館、開館前、休館日）だった場合保存フラグをFalseにして返す
            if seat[0].isdecimal():
                self.do_save = True
                room['seats_num'] = int(seat[0])
            elif seat[0] == '満\u3000席':
                self.do_save = True
            else:
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


    def save_room_data_to_firestore(self):
        print('\nrun [save_room_data_to_firestore]')

        # ドキュメント・フィールド名の生成
        jst = timezone(timedelta(hours=+9), 'JST')
        now = datetime.now(jst)
        date = now.strftime('%Y%m%d')
        time = now.strftime('%H%M')

        # ドキュメントの存在確認を行いデータを保存
        doc_ref = self.db.collection('rooms').document(date)
        doc = doc_ref.get()
        if doc.exists:
            doc_ref.update({time: self.rooms})
        else:
            doc_ref.set({time: self.rooms})


    def delete_room_data_from_firestore(self):
        print('\nrun [delete_room_data_from_firestore]')

        # ドキュメント数が30を上回ったら一番古いドキュメントを削除する
        doc_ids = sorted([i.id for i in self.db.collection('rooms').stream()])
        if len(doc_ids) > 30:
            self.db.collection('rooms').document(doc_ids[0]).delete()
            print(f'* ドキュメント数が30個を上回っていたので削除しました -> {doc_ids[0]}')
