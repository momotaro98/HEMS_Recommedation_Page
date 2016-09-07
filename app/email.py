from threading import Thread
from flask import current_app, render_template
from flask.ext.mail import Message
import sendgrid
from sendgrid.helpers.mail import *

from . import mail


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_async_email_with_sendgrid(app, sg, sg_mail):
    with app.app_context():
        response = sg.client.mail.send.post(request_body=sg_mail.get())


def send_email(to, subject, template, **kwargs):
    app = current_app._get_current_object()
    body = render_template(template + '.txt', **kwargs)
    html = render_template(template + '.html', **kwargs)

    if app.config['SENDGRID_USE']:

        sg = sendgrid.SendGridAPIClient(apikey=app.config['SENDGRID_API_KEY'])
        from_email = Email("慶應義塾大学池田伸太郎<ikeda@west.sd.keio.ac.jp>")
        subject = "慶應義塾大学レコメンドレポート " + subject
        to_email = Email(to)
        content = Content("text/plain", body)
        sg_mail = Mail(from_email, subject, to_email, content)
        thr = Thread(target=send_async_email_with_sendgrid,
                     args=[app, sg, sg_mail])

    else:
        msg = Message(app.config['APP_MAIL_SUBJECT_PREFIX'] + ' ' + subject,
                      sender=app.config['APP_MAIL_SENDER'], recipients=[to])
        msg.body = body
        msg.html = html
        thr = Thread(target=send_async_email, args=[app, msg])

    thr.start()
    return thr
