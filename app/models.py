from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from flask.ext.login import UserMixin
from . import db, login_manager

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
    recommendation_page = db.relationship('RecommendationPage',
                                          backref='user',
                                          lazy='dynamic')

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

    def make_1week_RecommendationPage_rows(self, top_dt, bottom_dt):
        data_rows_iter = self.recommendation_page.\
            filter(bottom_dt < RecommendationPage.timestamp).\
            filter(RecommendationPage.timestamp < top_dt).\
            order_by(RecommendationPage.timestamp.asc())
        return data_rows_iter


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


# 何かしらの処理の度にセッションにおけるユーザを再ロードするためのコールバック関数
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class SettempGraph:
    # define specification of this graph
    min_temp = 18
    max_temp = 30
    horizontal_axis_range = range(min_temp, max_temp + 1)
    horizontal_axis = [str(_) + "℃" for _ in horizontal_axis_range]

    def __init__(self, rows_iter):
        self.rows_iter = rows_iter

    def make_virtical_axis_values(self):
        """
        各設定温度の使用頻度のリストを返す 単位は%

        # Return Example
        return [0, 0, 0, 0, 0, 0, 0, 30, 60, 10, 0, 0, 0]
        """
        count_list = [0] * len(self.horizontal_axis_range)
        for row in self.rows_iter:
            count_list[row.set_temperature - self.min_temp] += 1
        return [int((_ / sum(count_list) * 100)) for _ in count_list]


class TotaltimeGraph:
    def __init__(self, rows_iter, top_datetime):
        self.rows_iter = rows_iter
        self.top_datetime = top_datetime

    def make_horizontal_axis_values(self):
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

    def make_virtical_axis_values(self):
        """
        # 1週間分の各日におけるエアコン総稼働時間のリストを返す 単位はHour

        # Return Example
        #       日  月  火  水  木  金  土
        return [65, 59, 80, 81, 56, 55, 48]
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
                index = weekday + 1 if 0 <= weekday <= 5 else 0

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


class PerhourGraph:
    # define specification of this graph
    horizontal_axis = [str(_) + ":00" for _ in range(24)]

    def __init__(self, rows_iter):
        self.rows_iter = rows_iter

    def make_virtical_axis_values(self):
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

        return [int(((_ / 7) * 100)) for _ in count_list]
