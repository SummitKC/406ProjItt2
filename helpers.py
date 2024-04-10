import os
import smtplib
from email.mime.text import MIMEText
from typing import Tuple
from dotenv import load_dotenv
from flask import redirect, session
from functools import wraps


PATH = os.path.join(os.path.dirname(__file__), 'instance', '.env')

def send_mail(email: str, credentials: Tuple[str, str]):
    load_dotenv(PATH)
    sender = "theimprovspot@gmail.com"
    recipients = [sender, email]

    msg = MIMEText(f'Your login credentials are:\nUsername: {credentials[0]}\nPassword: {credentials[1]}\n\n Please change your password as soon as you log in.')
    msg['Subject'] = "Login Credentials"
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
        smtp_server.login(sender, os.getenv('PASSWORD'))
        smtp_server.sendmail(sender, recipients, msg.as_string())

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_id') is None:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

def get_key():
    load_dotenv(PATH)
    return os.getenv('SECRET_KEY')