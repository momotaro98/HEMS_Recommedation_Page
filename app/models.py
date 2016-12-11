from datetime import datetime
from datetime import timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from flask.ext.login import UserMixin
from . import db, login_manager

from decision_tree_for_hems_recommendations import (
    SettingTempDT, TotalUsageDT, ChangeUsageDT,
)

from . import utils


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role', lazy='dynamic')
    # backrefを記述することで、Userモデルにdb.relationship('role')が記述されたことと同じになる
    # TODO lazyはRoleに関係するアイテムがロードされるタイミングを指定するものらしい
    # が、よく理解できていない


    def __repr__(self):
        return '<Role {0}>'.format(self.name)


# class User(db.Model):
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    recommendation_page = db.relationship(
        'RecommendationPage', backref='user', lazy='dynamic')

    # propertyでself.passwordを管理する
    @property
    def password(self):
        # passwordにはアクセスできないよとうエラーを発生させる
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):  # パスワードが設定されるとき(代入されるとき)に実行する
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    # SerializerはトークンとIDを紐付けるために必要なオブジェクトという認識である
    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)  # 与えられたトークンでシリアライザ-からロードができるか
            # トークンとIDは一対一のハッシュ関係
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True  # rowインスタンスのconfirmedカラムをTrueにする
        db.session.add(self)  # confirmedされたことをデータベースへ更新する
        return True

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def __repr__(self):
        return '<User {0}>'.format(self.username)

    def query_between_topdt_and_bottomdt(self, top_dt, bottom_dt):
        data_rows_iter = self.recommendation_page.\
            filter(bottom_dt < RecommendationPage.timestamp).\
            filter(RecommendationPage.timestamp < top_dt).\
            order_by(RecommendationPage.timestamp.asc())
        return data_rows_iter


# 何かしらの処理の度にセッションにおけるユーザを再ロードするためのコールバック関数
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class RecommendationPage(db.Model):
    __tablename__ = 'recommendationpage'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    timestamp = db.Column(db.DateTime, index=True)
    on_off = db.Column(db.String(64))
    operating = db.Column(db.String(64))
    set_temperature = db.Column(db.Integer)
    wind = db.Column(db.String(64))
    indoor_temperature = db.Column(db.Float)
    indoor_pressure = db.Column(db.Float)
    indoor_humidity = db.Column(db.Float)
    operate_ipaddress = db.Column(db.String(64))


class SettempGraph:
    # define specification of this graph
    min_temp = 18
    max_temp = 30
    horizontal_axis_range = range(min_temp, max_temp + 1)
    horizontal_axis = [str(t) + "℃" for t in horizontal_axis_range]

    def __init__(self, rows_iter):
        self.rows_iter = rows_iter
        self.virtical_axis = self._make_virtical_axis_values()

    def _make_virtical_axis_values(self):
        """
        各設定温度の使用頻度のリストを返す 単位は%

        # Return Example
        return [0, 0, 0, 0, 0, 0, 0, 30, 60, 10, 0, 0, 0]
        """
        count_list = [0] * len(self.horizontal_axis_range)
        for row in self.rows_iter:
            count_list[row.set_temperature - self.min_temp] += 1
        return [int((c / sum(count_list) * 100)) for c in count_list]

    def make_frequent_temperature(self):
        """
        self.virtical_axisのリストを利用して最も利用している設定温度を求める
        """
        return self.virtical_axis.index(max(self.virtical_axis)) + 18

    def make_recommend_temperature_summer(self):
        '''
        夏場におけるレコメンドレポートにおける推奨設定温度を求める
        '''
        return min(self.make_frequent_temperature() + 2, 28)

    def make_recommend_temperature_winter(self):
        '''
        冬場におけるレコメンドレポートにおける推奨設定温度を求める
        '''
        return max(self.make_frequent_temperature() - 2, 20)


class TotaltimeGraph:
    def __init__(self, rows_iter, top_datetime):
        self.rows_iter = rows_iter
        self.top_datetime = top_datetime
        self._weekday_to_index_list = self._make_weekday_to_index_list()
        self.horizontal_axis = self._make_horizontal_axis_values()
        self.virtical_axis = self._make_virtical_axis_values()
        self.ave_hour, self.ave_min = self._make_ave_HourAndMin()

    def _make_horizontal_axis_values(self):
        """
        # 日付の横軸ラベルを返す

        # Return Example
        # ["8月14日(日)", "8月15日(月)", "8月16日(火)",
           "8月17日(水)", "8月18日(木)", "8月19日(金)",
           "8月20日(土)"]
        """
        ret_list = []
        dt = self.top_datetime
        for _ in range(7):
            weekday = utils.make_weekday_in_Japanese(dt)
            insert_text = "{month}月{day}日({weekday})".\
                format(month=dt.month, day=dt.day, weekday=weekday)
            ret_list.insert(0, insert_text)
            dt = utils.back_1day_ago(dt)
        return ret_list

    def _make_weekday_to_index_list(self):
        """
        self.top_datetimeのweekdayが
        ret_listの6番目のインデックスになるようにする
        例
        self.top_datetimeが水曜日(2)のとき
         木 金 土 日 月 火 水
        [X, X, X, X, X, X, X]
        を'最終的に'返すのが目的なので
         月 火 水 木 金 土 日
        [4, 5, 6, 0, 1, 2, 3]
        を作る

        Usage:
        weekdayが水曜日(2)のとき
        index = self._weekday_to_index_list[weekday]
        でindex == 6 となる

        # >>> # self.top_datetime.date().weekday() == 2 のとき
        # >>> self._make_weekday_to_index_list()
        # [4, 5, 6, 0, 1, 2, 3]
        """
        ret_list = [7, 7, 7, 7, 7, 7, 7]
        weekday = self.top_datetime.date().weekday()
        for u_index in range(6, -1, -1):
            ret_list[weekday] = u_index
            weekday = weekday - 1 if weekday > 0 else 6
        return ret_list

    def _make_virtical_axis_values(self):
        """
        # 1週間分の各日におけるエアコン総稼働時間のリストを返す 単位はHour

        # Return Example
        return [0.0, 2.3, 4.4, 2.9, 6.1, 4.2, 2.5]
        """

        # 1番始めのonから次に来るoffまでの時間の合計時間を求める
        # onの時の日にちをon->off間の日にちとする

        ret_list = [0] * 7
        on_operationg_flag = False
        index = 0
        for row in self.rows_iter:
            if row.on_off == "on" and not on_operationg_flag:
                on_operationg_flag = True

                on_timestamp = row.timestamp
                # examine on_timestamp's weekday
                weekday = on_timestamp.date().weekday()
                # convert weekday to ret_list index
                index = self._weekday_to_index_list[weekday]

            elif row.on_off == "off" and on_operationg_flag:
                on_operationg_flag = False

                off_timestamp = row.timestamp
                ret_list[index] += utils.make_delta_hour(on_timestamp,
                                                         off_timestamp)

        # 1番最後の日にちにおいて23:59まで分を合計に追加する
        if on_operationg_flag:
            days_last_timestamp = utils.make_days_last_timestamp(on_timestamp)
            ret_list[index] += utils.make_delta_hour(on_timestamp,
                                                     days_last_timestamp)

        return ret_list

    def make_top1_weekday(self):
        top1_index = self.make_top_index_list(self.virtical_axis)[0]
        return self.convert_num_to_weekday(top1_index)

    def make_top2_weekday(self):
        top2_index = self.make_top_index_list(self.virtical_axis)[1]
        return self.convert_num_to_weekday(top2_index)

    @staticmethod
    def make_top_index_list(vlist):
        copy_list = vlist[:]
        top1_index = copy_list.index(max(copy_list))
        copy_list[top1_index] = 0
        top2_index = copy_list.index(max(copy_list))
        return [top1_index, top2_index]

    @staticmethod
    def convert_num_to_weekday(num):
        convert_list = ["日", "月", "火", "水", "木", "金", "土"]
        return convert_list[num]

    def _make_ave_HourAndMin(self):
        '''
        self.virtical_axisのリストの平均をHourとMinで返す

        # self.virtical_axis == [2.75, 2.75, 2.75, 2.75, 2.75, 2.75, 2.75]
        # >>> self.make_ave_HourAndMin()
        # (2, 45)
        '''
        # get ave of Hour.
        ave_hour = sum(self.virtical_axis) / len(self.virtical_axis)
        h, m = utils.convert_HourPoint_to_HourAndMin(ave_hour)
        return h, m


class PerhourGraph:
    # define specification of this graph
    horizontal_axis = [str(hour) + ":00" for hour in range(24)]

    def __init__(self, rows_iter):
        self.rows_iter = rows_iter
        self.virtical_axis = self._make_virtical_axis_values()

    def _make_virtical_axis_values(self):
        count_list = self._make_count_list()
        return [int((c / 7) * 100) for c in count_list]

    def _make_count_list(self):
        """
        1週間分における時間当たりの使用率のリストを返す 単位は%
        # Return Example
        return [90, 19, 13, 32, 2, 12, 50, 90, 19, 13, 32, 2, 12, 50,
                90, 19, 13, 32, 2, 12, 50, 90, 19, 13, 32, 2, 12, 50]
        """
        count_list = [0] * len(self.horizontal_axis)
        on_operationg_flag = False
        for row in self.rows_iter:
            if row.on_off == "on" and not on_operationg_flag:
                on_operationg_flag = True
                on_timestamp = row.timestamp
            elif row.on_off == "off" and on_operationg_flag:
                on_operationg_flag = False
                off_timestamp = row.timestamp

                # on->off 期間のHourをカウントする
                over_days = off_timestamp.day - on_timestamp.day
                # 日をまたがないとき
                if over_days == 0:
                    for i in range(on_timestamp.hour, off_timestamp.hour + 1):
                        count_list[i] += 1
                # 日をまたぐとき
                else:
                    for i in range(on_timestamp.hour, 24):
                        count_list[i] += 1
                    for i in range(0, off_timestamp.hour + 1):
                        count_list[i] += 1

        if on_operationg_flag:
            for i in range(on_timestamp.hour, 24):
                count_list[i] += 1

        return count_list

    def find_a_certain_hour_value(self, hour_index):
        return self.virtical_axis[hour_index]


class OneDayhourGraph(PerhourGraph):
    def _make_virtical_axis_values(self):
        count_list = self._make_count_list()
        return count_list


class OneDayTotaltimeGraph:
    def __init__(self, rows_iter):
        self.rows_iter = rows_iter
        self.use_hour, self.use_min = self._make_total_time()

    def _make_total_time(self):
        total_time_min = 0
        on_operationg_flag = False
        for row in self.rows_iter:
            if row.on_off == "on" and not on_operationg_flag:
                on_operationg_flag = True
                on_timestamp = row.timestamp
            elif row.on_off == "off" and on_operationg_flag:
                on_operationg_flag = False
                off_timestamp = row.timestamp
                total_time_min += utils.make_delta_min(
                    on_timestamp, off_timestamp)
        # 1番最後の日にちにおいて23:59まで分を合計に追加する
        if on_operationg_flag:
            days_last_timestamp = utils.make_days_last_timestamp(on_timestamp)
            total_time_min += utils.make_delta_min(
                on_timestamp, days_last_timestamp)
        h, m = utils.convert_MinToHourAndMin(total_time_min)
        return h, m


class DateTimeForRecommend:
    def __init__(self, target_datetime, top_datetime, bottom_datetime):
        # target_datetime
        self.target_datetime_month = target_datetime.month
        self.target_datetime_day = target_datetime.day
        self.target_datetime_yobi = \
            utils.convert_num_to_weekday(target_datetime.date().weekday())

        # top_datetime
        self.top_datetime_month = top_datetime.month
        self.top_datetime_day = top_datetime.day
        self.top_datetime_yobi = \
            utils.convert_num_to_weekday(top_datetime.date().weekday())

        # bottom_datetime
        self.bottom_datetime_month = bottom_datetime.month
        self.bottom_datetime_day = bottom_datetime.day
        self.bottom_datetime_yobi = \
            utils.convert_num_to_weekday(bottom_datetime.date().weekday())


class IsRecommendation:
    def __init__(self, user):
        self.user = user
        # startはコンテンツごとに異なる

    def ret_pred_Y(self):
        '''
        # IsSettingTempの場合
        ac_logs_list = self.ret_ac_logs_list()
        target_season = self.ret_target_season()
        target_hour = self.ret_target_hour()
        self.rDT = SettingTempDT(
                start_train_dt=self.start_train_dt,
                end_train_dt=self.end_train_dt,
                ac_logs_list=ac_logs_list,
                target_season=target_season,
                target_hour=target_hour,
        )
        y_pred = self.rDT.ret_predicted_Y_int()
        return y_pred
        '''
        pass

    def ret_start_train_dt(self):
        start_train_dt = datetime(2016, 11, 16, 0, 0, 0)
        return start_train_dt

    def ret_end_train_dt(self):
        # end_train_dt = datetime.now() - timedelta(days=1)
        '''
        # 今のtenkishochoでは当月のデータを得られないので
        # 得られるようにするまでは前月分までのデータ
        '''
        end_train_dt = datetime(2016, 11, 30, 23, 59, 59)
        return end_train_dt

    def ret_ac_logs_list(self):
        top_datetime = utils.the_dt_last_dt(self.ret_end_train_dt())
        bottom_datetime = self.ret_start_train_dt()
        rows_iter = self.user.query_between_topdt_and_bottomdt(
            top_datetime, bottom_datetime)
        # to be list
        ac_logs_list = list(rows_iter)
        return ac_logs_list

    def ret_target_season(self):
        # target_season = 'spr'
        # target_season = 'sum'
        # target_season = 'fal'
        target_season = 'win'
        return target_season

    def ret_target_hour(self):
        target_hour = 10
        return target_hour


class IsSettingTemp(IsRecommendation):
    def ret_pred_Y(self):
        start_train_dt = self.ret_start_train_dt()
        end_train_dt = self.ret_end_train_dt()
        ac_logs_list = self.ret_ac_logs_list()
        target_season = self.ret_target_season()
        target_hour = self.ret_target_hour()
        self.rDT = SettingTempDT(
                start_train_dt=start_train_dt,
                end_train_dt=end_train_dt,
                ac_logs_list=ac_logs_list,
                target_season=target_season,
                target_hour=target_hour,
        )
        y_pred = self.rDT.ret_predicted_Y_int()
        return y_pred

    def ret_start_train_dt(self):
        start_train_dt = datetime(2016, 11, 16, 0, 0, 0)
        return start_train_dt


class IsTotalUsage(IsRecommendation):
    def ret_pred_Y(self):
        start_train_dt = self.ret_start_train_dt()
        end_train_dt = self.ret_end_train_dt()
        ac_logs_list = self.ret_ac_logs_list()
        target_season = self.ret_target_season()
        target_hour = self.ret_target_hour()
        self.rDT = TotalUsageDT(
                start_train_dt=start_train_dt,
                end_train_dt=end_train_dt,
                ac_logs_list=ac_logs_list,
                target_season=target_season,
                target_hour=target_hour,
        )
        y_pred = self.rDT.ret_predicted_Y_int()
        return y_pred

    def ret_start_train_dt(self):
        start_train_dt = datetime(2016, 8, 16, 0, 0, 0)
        return start_train_dt


class IsChangeUsage(IsRecommendation):
    def ret_pred_Y(self):
        start_train_dt = self.ret_start_train_dt()
        end_train_dt = self.ret_end_train_dt()
        ac_logs_list = self.ret_ac_logs_list()
        target_season = self.ret_target_season()
        target_hour = self.ret_target_hour()
        self.st_DT = ChangeUsageDT(
                start_train_dt=start_train_dt,
                end_train_dt=end_train_dt,
                ac_logs_list=ac_logs_list,
                target_season=target_season,
                target_hour=target_hour,
        )
        y_pred = self.st_DT.ret_predicted_Y_int()
        return y_pred

    def ret_start_train_dt(self):
        start_train_dt = datetime(2016, 8, 16, 0, 0, 0)
        return start_train_dt
