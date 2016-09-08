from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from flask.ext.login import UserMixin
from . import db, login_manager

from .utils import make_week_top_and_bottom_day


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

    def make_1week_RecommendationPage_rows(self):
        top_datetime, bottom_datetime = make_week_top_and_bottom_day()

        data_rows_iter = self.recommendation_page.\
            filter(bottom_datetime < RecommendationPage.timestamp).\
            filter(RecommendationPage.timestamp < top_datetime).\
            order_by(RecommendationPage.timestamp.desc())
        '''
        # For Debugging
        for row in data_rows_iter:
            print("row.timestamp: ", row.timestamp)
        '''
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
    horizontal_axis = [str(_) + "℃" for _ in range(18, 31)]

    def __init__(self):
        pass

    def make_virtical_axis_values(self):
        # ret = RecommendationPage.

        # Return Example
        return [0, 0, 0, 0, 0, 0, 0, 30, 60, 10, 0, 0, 0]


class TotaltimeGraph:
    # define specification of this graph

    def __init__(self):
        pass

    def make_virtical_axis_values(self):

        # Return Example
        return [65, 59, 80, 81, 56, 55, 48]


class PerhourGraph:
    # define specification of this graph
    horizontal_axis = [str(_) + ":00" for _ in range(24)]

    def __init__(self):
        pass

    def make_virtical_axis_values(self):

        # Return Example
        return [90, 19, 13, 32, 2, 12, 50, 90, 19, 13, 32, 2, 12, 50,
                90, 19, 13, 32, 2, 12, 50, 90, 19, 13, 32, 2, 12, 50]
