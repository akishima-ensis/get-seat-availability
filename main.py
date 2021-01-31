from datetime import datetime

from src import jst, DEBUG
from src.script import get_rooms_data, save_rooms_data, delete_rooms_data


def run(Request) -> None:
    now = datetime.now(jst)

    print('run...')
    print(now)

    # 座席情報の取得
    rooms_data = get_rooms_data()
    print(rooms_data)

    # 座席情報の保存
    if rooms_data:
        save_rooms_data(rooms_data, now)

    # 古い座席情報の削除
    if now.hour == 10 and now.minute == 0:
        delete_rooms_data()

    return 'ok'


if DEBUG:
    run('')