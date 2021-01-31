import re
from datetime import datetime
from typing import Dict, Optional
import requests
from bs4 import BeautifulSoup

from src import db, url, session, headers


def get_rooms_data() -> Optional[Dict]:
    """
    下記のURLに対してリクエスト、スクレイピングを行い学習室の空席情報を取得する
    https://webreserv.library.akishima.tokyo.jp/webReserv/AreaInfo/Login

    Returns:
        Dict or None: 通常は書く学習室の空席情報、開館時間外はNoneを返す
    """
    print('\n### get_seat_data ###')

    rooms_data = {
        'status': True,
        'update': '0000/00/00 00:00',
        'data': [
            {
                'name': '学習席（有線LAN有）',
                'seats_num': 0,
                'web_seats_num': 0,
                'total_seats_num': 0,
            },
            {
                'name': '学習席',
                'seats_num': 0,
                'web_seats_num': 0,
                'total_seats_num': 0,
            },
            {
                'name': '研究個室',
                'seats_num': 0,
                'web_seats_num': 0,
                'total_seats_num': 0,
            },
            {
                'name': 'インターネット・DB席',
                'seats_num': 0,
                'web_seats_num': 0,
                'total_seats_num': 0,
            },
            {
                'name': 'グループ学習室',
                'seats_num': 0,
                'web_seats_num': 0,
                'total_seats_num': 0,
            },
            {
                'name': 'ティーンズ学習室',
                'seats_num': 0,
                'web_seats_num': 0,
                'total_seats_num': 0,
            }
        ]
    }

    # リクエスト
    try:
        res = session.get(url=url, headers=headers)
        res.raise_for_status()
    except requests.exceptions.RequestException as e:
        rooms_data['status'] = False
        print(e)
        return rooms_data

    soup = BeautifulSoup(res.text, 'lxml')

    # サイト内更新時間の取得
    try:
        update_str = soup.find(class_='check_date text-danger').text
        update_str_re = re.findall('\d', update_str)
        if len(update_str_re) == 11:
            update_str_re.insert(8, '0')
        update_strptime = datetime.strptime(''.join(update_str_re), '%Y%m%d%H%M')
        update = update_strptime.strftime('%Y/%m/%d %H:%M')
        rooms_data['update'] = update

        # 座席情報の取得
        seats = soup.find(class_='seat').find_all('tr')

        for index, room in enumerate(rooms_data['data'], 1):

            # 各部屋の座席情報を取得
            seat = [i.text for i in seats[index].find_all('div')]

            # 空席数
            if seat[0].isdecimal():
                room['seats_num'] = int(seat[0])
            elif seat[0] == '満\u3000席':
                pass
            else:
                print('* 現在は閉館時間です')
                return

            # web空き数
            if seat[1].isdecimal():
                room['web_seats_num'] = int(seat[1])

            # 座席総数
            room['total_seats_num'] = int(seat[2])

    except Exception as e:
        print(e)
        rooms_data['update'] = False
        return rooms_data

    return rooms_data


def save_rooms_data(rooms_data: Dict, now: datetime) -> None:
    """
    firestoreに空席情報を保存する

    Args:
        rooms_data(dict): 学習室の空席情報
        now(datetime): 現在時刻
    """
    print('\n### save_room_data_to_firestore ###')
    date = now.strftime('%Y%m%d')
    time = now.strftime('%H%M')
    rooms_ref = db.collection('rooms').document(date)
    if rooms_ref.get().exists:
        rooms_ref.update({time: rooms_data})
    else:
        rooms_ref.set({time: rooms_data})


def delete_rooms_data() -> None:
    """
    firestoreのroomsコレクションないのドキュメント数が30を超えていたら一番古いドキュメントを削除する
    """
    print('\n### delete_room_data_from_firestore ###')
    doc_ids = sorted([i.id for i in db.collection('rooms').stream()])
    if len(doc_ids) > 30:
        db.collection('rooms').document(doc_ids[0]).delete()
        print(f'* ドキュメントを削除しました document_id: {doc_ids[0]}')
