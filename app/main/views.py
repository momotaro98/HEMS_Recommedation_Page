from flask import request, render_template, session, redirect, url_for, current_app, abort, flash
from .. import db
from ..models import User, RecommendationPage
from . import main
from flask.ext.wtf import Form
from wtforms import StringField, SelectField, HiddenField, BooleanField, SubmitField, validators
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
    return render_template('index.html')
