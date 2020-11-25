from src import get_seat_availability


def run(Request):
    gsa = get_seat_availability.GetSeatAvailability()

    # 座席状況の取得
    gsa.get_seat_data()

    # 座席状況の保存
    if gsa.do_save:
        gsa.save_room_data_to_firestore()

    # 古い座席情報の削除
    gsa.delete_room_data_from_firestore()

    return 'ok'