from random import randint
import time
from helpers import calculate_total_expenses, calculate_total_income, calculate_total_profit, login_required, get_key, send_mail
from datetime import datetime, date
from functools import wraps
from flask import Flask, flash, render_template, request, redirect, session, url_for
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.attributes import flag_modified
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = get_key()
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///database.db'
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    hash = db.Column(db.String, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    phone_number = db.Column(db.String)
    address = db.Column(db.String)
    total_payments = db.Column(db.Integer)
    current_payment = db.Column(db.Integer) # how much the user currently pays for a class
    weekly_status = db.Column(db.JSON)  # Storing a dictionary as JSON

    def userDiscount(self):
        weekDict = self.weekly_status
        revWeekDict = list(weekDict.keys())
        if len(revWeekDict) > 11:
            for i in range(12):
                if revWeekDict[-i] == False: 
                    self.current_payment = 10 
            self.current_payment = self.current_payment * .9

            db.session.commit()

    def add_total_payments(self):
        self.total_payments += self.current_payment
        db.session.commit()

    def update_weekly_status(self, week_number, attendance):
        if not self.weekly_status:
            self.weekly_status = {}
        self.weekly_status[week_number] = (attendance, self.current_payment)
        flag_modified(self, "weekly_status")
        db.session.add(self)
        db.session.commit()

    # TODO remove the hash 
    def __repr__(self) -> str:
        return f'UID: {self.id}, User {self.username}, Hash: {self.hash}| Name: {self.name} | Phone Number: {self.phone_number} | Address: {self.address} | Status: {self.weekly_status}'

class Admins(db.Model):

    # if u want admin login, register thing -> 
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    hash = db.Column(db.String, nullable=False)

class Finances(db.Model):
    month_year = db.Column(db.Date, primary_key=True)
    income_users = db.Column(db.Integer, default=0) #-> users is class participants (feel free to change the name)
    income_other = db.Column(db.Integer, default=0)
    expenses_coach = db.Column(db.Integer, default=0)
    expenses_hall  = db.Column(db.Integer, default=0)
    expenses_other = db.Column(db.Integer, default=0)

    
    def addUserIncome(self, amount: int, type: str):
        if type == 'u':
            self.income_users += amount
        elif type == 'o':
            self.income_other += amount
        db.session.commit()

    def add_expenses(self, amount: int, type: str):
        if type == 'c':
            self.expenses_coach += amount
        elif type == 'h':
            self.expenses_hall += amount
        elif type == 'o':
            self.expenses_other += amount

    def calculate_total_income(self): 
        return self.income_users + self.income_other
    
    def calculate_total_expenses(self): 
        return self.expenses_coach + self.expenses_hall + self.expenses_other 

    def __repr__(self) -> str:
        return f'| YYYY/MM/DD: {self.month_year} | Income: {self.calculate_total_income()} | Expenses: {self.calculate_total_expenses()} | Profit: {self.calculate_profit()}'

    def calculate_profit(self):
        month_profit = self.calculate_total_income()  - self.calculate_total_expenses()
        if month_profit < 0:
            return f"({-1 * month_profit})"
        return month_profit

@app.route('/')
# @login_required <-- TODO uncomment this when everything is done
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/payment', methods=['GET', 'POST'])
def payment():
    if request.method == 'POST':
        cardNumber = request.form['card_number']
        cardNumber = cardNumber.replace('\t', '')[::-1]
        sumOddDigit = 0
        sumEvenDigit = 0
        for number in cardNumber[::2]:
            sumOddDigit += int(number)

        for number in cardNumber[1::2]:
            number = int(number) * 2
            if number > 9: 
                quotient = number // 10 
                remainder = number % 10  
                sumEvenDigit += (quotient + remainder)
            
            else: 
                sumEvenDigit += number

        total = sumEvenDigit + sumOddDigit 

        if total % 10 == 0: 
            week = request.form['week']
            currUserPay = db.session.query(User).filter_by(username=session['username']).first()
            currUserPay.update_weekly_status(week, "attended")
            return redirect('/account')
        else: 
            flash("Declined")
            week = request.form['week']
            return redirect(f'/payment?week={week}')
    
    week = request.args.get('week')
    return render_template('payment.html', week=week)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm-password']
        name = request.form['name']
        address = request.form['address']
        phone_number = request.form['phone-number']

        print(password, confirm_password, name, address, phone_number)

        if confirm_password == password:
            new_user = User(username=username, hash=generate_password_hash(password), 
                            name = name, phone_number = phone_number, address = address,
                            total_payments=0, current_payment=10, weekly_status={}
                            )

            try:
                db.session.add(new_user)
                db.session.commit()
                print("made it", new_user)
            except:
                return render_template('error.html', err_msg="There was an unexpected error registering the account") 
        elif confirm_password != password:
            print("password wrong")
            flash("Passwords do not match")
            return redirect('/register')
        return redirect('/login') 
    return render_template('register.html')


@app.route('/adminlogin',methods=['GET', 'POST'])
def adminlogin(): 
    session.clear()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        admin = db.session.query(Admins).filter_by(username=username).first()
        if admin and check_password_hash(admin.hash, password):
            session['user_id'] = admin.id
            session['username'] = admin.username
            return redirect('/') 
        else:
            #TODO: change this to give a popup notifying the user instead of redirecting them
            return render_template('error.html', err_msg="Incorrect Username or Password")
    else:
        return render_template('adminlogin.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    session.clear()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = db.session.query(User).filter_by(username=username).first()
        if user and check_password_hash(user.hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['payment'] = user.current_payment
            user.userDiscount()
            return redirect('/') 
        else:
            #TODO: change this to give a popup notifying the user instead of redirecting them
            return render_template('error.html', err_msg="Incorrect Username or Password")
    else:
        return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')
    
@app.route('/admin') # TODO add admin login later  
def yearToDate():
    ytd = db.session.query(Finances).all()
    ytdTotal = 0
    for yt in ytd:
        ytdTotal += yt.calculate_profit()

    return render_template('adminSide.html', ytdTotal = ytdTotal)

@app.route('/dashboard')
@login_required
def dashboard():
    username = session['username']
    return f"Welcome, {username}! This is your dashboard."

@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    #weeks = range(10)
    if request.method == 'POST':
        # payments; week_to_pay = week number, not the amount paid
        week_to_pay = list(request.form.keys())[0]
        d = datetime.today()
        # query both finance and user side
        finance = db.session.query(Finances).filter_by(month_year=date(d.year, d.month, 1)).first()
        user = db.session.query(User).filter_by(username=session['username']).first()
        # finance side
        finance.addUserIncome(user.current_payment, 'u')
        # user side
        user.total_payments += user.current_payment
        user.update_weekly_status(week_to_pay, 'attended')

        return render_template('account.html', weeks=["1","2","3","4"], payment=user.current_payment, status=user.weekly_status)
    else:
        # TODO: update to use render_template(account.html) when ready
        user = db.session.query(User).filter_by(username=session['username']).first()
        return render_template('account.html', weeks=["1","2","3","4"], payment=user.current_payment, status=user.weekly_status)

@app.route('/finance')
def finance():
    db.session.add(Finances(month_year = datetime(randint(1900, 2024), randint(1, 12), randint(1, 28)),income_users = randint(1000, 10000), income_other = randint(1000, 10000), expenses_coach=randint(1000, 2000), expenses_hall=randint(1000, 2000), expenses_other=randint(1000, 2000))),db.session.add(Finances(month_year = datetime(randint(1900, 2024), randint(1, 12), randint(1, 28)),income_users = randint(1000, 10000), income_other = randint(1000, 10000), expenses_coach=randint(1000, 2000), expenses_hall=randint(1000, 2000), expenses_other=randint(1000, 2000)))
    db.session.add(Finances(month_year = datetime(randint(1900, 2024), randint(1, 12), randint(1, 28)),income_users = randint(1000, 10000), income_other = randint(1000, 10000), expenses_coach=randint(1000, 2000), expenses_hall=randint(1000, 2000), expenses_other=randint(1000, 2000)))
    db.session.add(Finances(month_year = datetime(randint(1900, 2024), randint(1, 12), randint(1, 28)),income_users = randint(1000, 10000), income_other = randint(1000, 10000), expenses_coach=randint(1000, 2000), expenses_hall=randint(1000, 2000), expenses_other=randint(1000, 2000)))
    db.session.add(Finances(month_year = datetime(randint(1900, 2024), randint(1, 12), randint(1, 28)),income_users = randint(1000, 10000), income_other = randint(1000, 10000), expenses_coach=randint(1000, 2000), expenses_hall=randint(1000, 2000), expenses_other=randint(1000, 2000)))
    db.session.commit()


    finance_info = db.session.query(Finances).all()
    return render_template('finance.html', lt_profit=calculate_total_profit(finance_info), lt_income=calculate_total_income(finance_info),
                            lt_expenses=calculate_total_expenses(finance_info), finance_info=finance_info)

@app.route('/test')
def test():

    # d = datetime.today()
    # new_finance = Finances(month_year=date(d.year, d.month, 1), 
    #                        income_users=1000, expenses_hall=500)
    # db.session.add(new_finance)
    # db.session.commit()

    # ytd = db.session.query(Finances).first()
    # print(ytd.month_year.year == mmyy.year and ytd.month_year.month == mmyy.month)
    # print(ytd.month_year, type(ytd.month_year))
    # print(ytd.month_year, date(d.year, d.month, 1), ytd.month_year == date(d.year, d.month, 1))
    # byMonthYear = db.session.query(Finances).filter_by(month_year=date(d.year, 5, 1)).first()
    # print(byMonthYear)

    users = db.session.query(User).all()
    for user in users:
        print(user.name)
        print(user.weekly_status, type(user.weekly_status))
    return render_template('test.html', users=users)

@app.route('/test2')
def test2():
    users = db.session.query(User).all()
    for user in users:
        print(user.name)
        print(user.weekly_status, type(user.weekly_status))
    return render_template('test.html', users=users)

@app.route('/test3')
def test3():
    users = db.session.query(User).all()
    for user in users:
        print(user.name)
        print(user.weekly_status, type(user.weekly_status))
    return render_template('test.html', users=users)
