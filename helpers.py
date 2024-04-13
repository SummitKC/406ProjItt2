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

def send_mail_self(email: str, name: str, message: str):
    load_dotenv(PATH)
    sender = "theimprovspot@gmail.com"

    msg = MIMEText(f'From: {name}\n Email: {email}\n Messege: {message}')
    msg['Subject'] = "Messege from"
    msg['From'] = sender
    msg['To'] = sender

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
        smtp_server.login(sender, os.getenv('PASSWORD'))
        smtp_server.sendmail(sender, sender, msg.as_string())

def send_warning_mail(email, name, weeks):
    load_dotenv(PATH)
    week_nums = ', '.join(c.rstrip(',') for c in weeks)
    msg = MIMEText(f'Hello {name}, You have outstanding balances for weeks {week_nums}. \nPlease pay your fees as soon as possible or else you may be subject to late penalties.')
    msg['Subject'] = "Fee Reminders"
    msg['From'] = "theimprovspot@gmail.com"
    msg['To'] = email

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('admin_id'):
            return redirect('/admin')
        elif session.get('user_id') is None:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('admin_id') is None:
            return redirect('/adminlogin')
        return f(*args, **kwargs)
    return decorated_function

def get_key():
    load_dotenv(PATH)
    return os.getenv('SECRET_KEY')


def calculate_total_income(finance_info):
    total_income = 0
    for month in finance_info:
        total_income += month.income_users + month.income_other
    return total_income

def calculate_total_expenses(finance_info):
    total_expenses = 0
    for month in finance_info:
        total_expenses += month.expenses_coach + month.expenses_other + month.expenses_hall
    return total_expenses

def calculate_total_profit(finance_info):
    # return finance_inst.calculate_total_income() - finance_inst.calculate_total_expenses() --> later
    total_profit =  calculate_total_income(finance_info) - calculate_total_expenses(finance_info)
    if total_profit < 0:
        return f"({-1 * total_profit})"
    return total_profit

def zero_padding(day: str):
    if len(day) == 1:
        return "0" + day
    else:
        return day
    
def is_same_week(date1, date2):
    # Get the ISO week numbers for the dates
    # Check if the ISO week numbers are the same
    return date1.isocalendar()[1] == date2.isocalendar()[1]