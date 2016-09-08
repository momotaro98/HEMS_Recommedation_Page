from datetime import datetime, timedelta


def make_week_top_and_bottom_day(the_time=datetime.now()):
    """
    '本日'において1番最近の土曜日のdatetime(top)とそこから1週間前のdatetime(bottom)の2つを返す関数
    """
    weekday = the_time.date().weekday()  # 本日の曜日ナンバー取得
    '''
    0なら2日前
    1なら3日前
    2なら4日前
    3なら5日前
    4なら6日前
    5なら7日前
    6なら1日前
    '''
    ago_day = weekday + 2 if 0 <= weekday <= 5 else 1
    date_recent_Satureday = the_time - timedelta(days=ago_day)
    date_7day_from_rSd = date_recent_Satureday - timedelta(days=7)
    top_datetime = datetime(date_recent_Satureday.year,
                            date_recent_Satureday.month,
                            date_recent_Satureday.day,
                            23, 59, 59)
    bottom_datetime = datetime(date_7day_from_rSd.year,
                               date_7day_from_rSd.month,
                               date_7day_from_rSd.day,
                               23, 59, 59)
    return top_datetime, bottom_datetime
