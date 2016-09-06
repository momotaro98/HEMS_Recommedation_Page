from threading import Thread
from flask import current_app, render_template
from flask.ext.mail import Message
import sendgrid
from sendgrid.helpers.mail import *

from . import mail


def send_async_email(app, msg, sg=None):
    with app.app_context():
        mail.send(msg)


def send_async_email_with_sendgrid(app, sg):
    with app.app_context():
        response = sg.client.mail.send.post(request_body=mail.get())


def send_email(to, subject, template, **kwargs):
    app = current_app._get_current_object()
    body = render_template(template + '.txt', **kwargs)
    html = render_template(template + '.html', **kwargs)

    if app.config['SENDGRID_USE']:
        '''
        sg = sendgrid.SendGridClient(app.config['SENDGRID_USERNAME'],
                                     app.config['SENDGRID_PASSWORD'])
        msg = sendgrid.Mail()
        msg.add_to(to)
        msg.set_subject(subject)
        msg.set_text(body)
        msg.set_from('Doe John')
        '''

        sg = sendgrid.SendGridAPIClient(apikey=app.config['SENDGRID_API_KEY'])
        from_email = Email("test@example.com")
        subject = "Hello World from the SendGrid Python Library!"
        to_email = Email(to)
        content = Content("text/plain", body)
        mail = Mail(from_email, subject, to_email, content)
        thr = Thread(target=send_async_email_with_sendgrid, args=[app, sg])

    else:
        msg = Message(app.config['APP_MAIL_SUBJECT_PREFIX'] + ' ' + subject,
                      sender=app.config['APP_MAIL_SENDER'], recipients=[to])
        msg.body = body
        msg.html = html
        thr = Thread(target=send_async_email, args=[app, msg])

    thr.start()
    return thr
