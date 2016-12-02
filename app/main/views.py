from flask import (request, render_template, session,
                   redirect, url_for, current_app, abort, flash)
from .. import db
from ..models import (User, RecommendationPage,
                      SettempGraph, TotaltimeGraph, PerhourGraph,
                      OneDayhourGraph, OneDayTotaltimeGraph,
                      DateTimeForRecommend)
from .. import utils
from . import main
from flask.ext.wtf import Form
from wtforms import (StringField, SelectField, HiddenField,
                     BooleanField, SubmitField, validators)
from flask.ext.login import current_user, login_required
import datetime

from . import main
from ..email import send_email


@main.app_errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@main.app_errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


@main.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))

    # 対象のユーザインスタンスを取得
    user = User.query.filter_by(
        username=current_user.username).first_or_404()

    # $$$$$ 1週間分データの処理 Start $$$$$
    # @@@ クエリ用のtop_datetime, bottom_datetimeを取得する @@@
    # ### top=土曜日 パターン ###
    # 指定日(デフォルトが本日)において
    # 1番最近の土曜日のdatetime(top)と
    # そこから1週間前のdatetime(bottom)
    # *** 本日 ***
    # top_datetime, bottom_datetime = \
    #     utils.make_week_topSaturday_and_bottom_day()
    # *** 指定日 ***
    # top_datetime, bottom_datetime = \
    #     utils.make_week_topSaturday_and_bottom_day(
    #         datetime.datetime(2016, 9, 1))

    # ### top=昨日 パターン###
    # 指定日において昨日(top)と
    # そこから1週間前のdatetime(bottom)の2つを返す関数
    # *** 本日 ***
    # top_datetime, bottom_datetime = \
    #     utils.make_week_topPreviousDay_and_bottom_day()
    # *** 指定日 ***
    top_datetime, bottom_datetime = \
        utils.make_week_topPreviousDay_and_bottom_day(
            datetime.datetime(2016, 11, 16))

    # クエリ発行、1週間分のデータを取得
    user_1week_rows_iter = user.query_between_topdt_and_bottomdt(
        top_datetime, bottom_datetime)
    # イテレータをリストにする
    user_1week_rows_list = list(user_1week_rows_iter)
    # データが無いユーザに対してはデータが無いことを伝えるページに移す
    if len(user_1week_rows_list) <= 0:
        return redirect(url_for('main.data_not_prepaired'))

    # $$$$$ 1週間分データの処理 End $$$$$

    # $$$$$ 1日分データの処理 Start $$$$$
    # top_dt, bottom_dtを取得
    # oneday_top_datetime, oneday_bottom_datetime = \
    #     utils.make_dayPreviousDay_start_dt()
    oneday_top_datetime, oneday_bottom_datetime = \
        utils.make_dayPreviousDay_start_dt(datetime.datetime(2016, 11, 16))

    print('top_datetime', top_datetime)
    print('oneday_top_datetime', oneday_top_datetime)

    # クエリ発行、指定日の前日分のデータを取得
    user_1day_rows_iter = user.query_between_topdt_and_bottomdt(
        oneday_top_datetime, oneday_bottom_datetime)
    # イテレータをリストにする
    user_1day_rows_list = list(user_1day_rows_iter)
    # データの有無の確認
    is_preday_existed = False if len(user_1day_rows_list) <= 0 else True
    # $$$$$ 1日分データの処理 End $$$$$

    # 各レコメンドコンテンツのインスタンスを取得
    # instances for 1 week
    settemp_graph = SettempGraph(user_1week_rows_list)
    totaltime_graph = TotaltimeGraph(user_1week_rows_list, top_datetime)
    perhour_graph = PerhourGraph(user_1week_rows_list)

    # instances for 1 day
    oneday_settemp_graph = \
        SettempGraph(user_1day_rows_list) if is_preday_existed else None
    oneday_totaltime_graph = \
        OneDayTotaltimeGraph(user_1day_rows_list) if is_preday_existed else None
    oneday_perhour_graph = \
        OneDayhourGraph(user_1day_rows_list) if is_preday_existed else None

    print('oneday_settemp_graph.make_frequent_temperature()',
          oneday_settemp_graph.make_frequent_temperature())
    print('oneday_totaltime_graph.use_hour',
          oneday_totaltime_graph.use_hour)
    print('oneday_totaltime_graph.use_min',
          oneday_totaltime_graph.use_min)
    print('oneday_perhour_graph.find_a_certain_hour_value(10)',
          oneday_perhour_graph.find_a_certain_hour_value(10))

    # 日付におけるオリジナルオブジェクトのインスタンスを呼ぶ
    dt_reco = DateTimeForRecommend(
        top_datetime=top_datetime,
        bottom_datetime=bottom_datetime
    )

    return render_template(
        'index.html',
        dt_reco=dt_reco,
        settemp_graph=settemp_graph,
        totaltime_graph=totaltime_graph,
        perhour_graph=perhour_graph,
        is_preday_existed=is_preday_existed,
        oneday_settemp_graph=oneday_settemp_graph,
        oneday_totaltime_graph=oneday_totaltime_graph,
        oneday_perhour_graph=oneday_perhour_graph,
    )


@main.route('/notyet')
def data_not_prepaired():
    return render_template('sorry.html')
