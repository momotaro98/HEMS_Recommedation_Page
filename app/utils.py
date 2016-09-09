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


def make_weekday_in_Japanese_from_num(num):
    """
    >>> make_weekday_in_Japanese_from_num(0)
    '月'
    >>> make_weekday_in_Japanese_from_num(6)
    '日'
    """
    convert_list = ["月", "火", "水", "木", "金", "土", "日"]
    return convert_list[num]


def make_weekday_in_Japanese(the_time=datetime.now()):
    """
    >>> make_weekday_in_Japanese(datetime(2016, 4, 1))
    '金'
    """
    return make_weekday_in_Japanese_from_num(the_time.date().weekday())


def back_1day_ago(the_time=datetime.now()):
    """
    >>> back_1day_ago(datetime(2016, 4, 1))
    datetime.datetime(2016, 3, 31, 0, 0)
    """
    return the_time - timedelta(days=1)


def make_days_last_timestamp(the_time=datetime.now()):
    return datetime(the_time.year, the_time.month, the_time.day,
                    23, 59, 59)


def make_delta_hour(start_dt, end_dt=datetime.now()):
    """
    >>> start_dt = datetime(2016, 4, 1, 10, 40, 0)
    >>> end_dt = datetime(2016, 4, 1, 15, 40, 0)
    >>> make_delta_hour(start_dt, end_dt)
    5.0
    """
    delta_seconds = (end_dt - start_dt).seconds
    return round((delta_seconds // 60) / 60, 1)
