from flask import (request, render_template, session,
                   redirect, url_for, current_app, abort, flash)
from .. import db
from ..models import (User, RecommendationPage,
                      SettempGraph, TotaltimeGraph, PerhourGraph)
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

    top_datetime, bottom_datetime = utils.make_week_top_and_bottom_day()

    user = User.query.filter_by(username=current_user.username).\
        first_or_404()
    user_1week_rows_iter = user.\
        make_1week_RecommendationPage_rows(top_datetime, bottom_datetime)

    # イテレータは一度使われると再利用できないのでリストにする
    user_1week_rows_iter = list(user_1week_rows_iter)
    # ↑これ合ってる?

    settemp_graph = SettempGraph(user_1week_rows_iter)
    totaltime_graph = TotaltimeGraph(user_1week_rows_iter, top_datetime)
    perhour_graph = PerhourGraph()

    return render_template('index.html',
                           settemp_graph=settemp_graph,
                           totaltime_graph=totaltime_graph,
                           perhour_graph=perhour_graph)
