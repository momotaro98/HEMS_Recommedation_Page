from threading import Thread
import sendgrid
from flask import current_app, render_template
from flask.ext.mail import Message
from . import mail


def send_async_email(app, msg, sg=None):
    with app.app_context():
        if sg:
            sg.send(msg)
        else:
            mail.send(msg)


def send_email(to, subject, template, **kwargs):
    app = current_app._get_current_object()
    body = render_template(template + '.txt', **kwargs)
    html = render_template(template + '.html', **kwargs)

    if app.config['SENDGRID_USE']:
        sg = sendgrid.SendGridClient(app.config['SENDGRID_USERNAME'],
                                     app.config['SENDGRID_PASSWORD'])
        msg = sendgrid.Mail()
        msg.add_to(to)
        msg.set_subject(subject)
        msg.set_text(body)
        msg.set_from('Doe John')
        thr = Thread(target=send_async_email, args=[app, msg, sg])
    else:
        msg = Message(app.config['APP_MAIL_SUBJECT_PREFIX'] + ' ' + subject,
                      sender=app.config['APP_MAIL_SENDER'], recipients=[to])
        msg.body = body
        msg.html = html
        thr = Thread(target=send_async_email, args=[app, msg])

    thr.start()
    return thr
