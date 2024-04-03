from traitlets import default
from helpers import login_required, get_key, send_mail
from datetime import datetime, date
from functools import wraps
from flask import Flask, flash, render_template, request, redirect, session, url_for
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
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
    role = db.Column(db.Integer, nullable=False) # 0=member, 1=admin
    name = db.Column(db.String(50), nullable=False)
    phone_number = db.Column(db.String)
    address = db.Column(db.String)
    total_payments = db.Column(db.Integer)
    current_payment = db.Column(db.Integer)
    weekly_status = db.Column(db.JSON)  # Storing a dictionary as JSON


# TODO remove the hash 
    def __repr__(self) -> str:
        return f'UID: {self.id}, User {self.username}, Hash: {self.hash}| Name: {self.name} | Phone Number: {self.phone_number} | Address: {self.address} |'

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
    
    def calculate_profit(self):
        return self.calculate_total_income()  - self.calculate_total_expenses()

    def monthInformation(self): 
        return

    def __repr__(self) -> str:
        return f'| MM/YYYY: {self.month_year} | Income: {self.calculate_total_income()} | Expenses: {self.calculate_total_expenses()} | Profit: {self.calculate_profit()}'


@app.route('/')
# @login_required <-- TODO uncomment this when everything is done
def home():
    return render_template('home.html')

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
            new_user = User(username=username, hash=generate_password_hash(password), role=0, name = name, phone_number = phone_number, address = address)

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
        return redirect('/') 
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    session.clear()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        users = db.session.query(User).filter_by(username=username)
        # users would only ever have 1 or 0 items. therefore a loop is a quick and easy way to check if user is in db
        for user in users:
            if check_password_hash(user.hash, password):
                session['user_id'] = user.id
                session['username'] = user.username
                return redirect('/dashboard')    
            
        #TODO: change this to give a popup notifying the user instead of redirecting them
        return render_template('error.html', err_msg="Incorrect Username or Password")
    else:
        return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    username = session['username']
    return f"Welcome, {username}! This is your dashboard."

@app.route('/admin') # TODO add admin login later  
def yearToDate():
    ytd = db.session.query(Finances).all()
    ytdTotal = 0
    for yt in ytd:
        ytdTotal += yt.calculate_profit()

    return render_template('adminSide.html', ytdTotal = ytdTotal)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')

@app.route('/test')
def test():

    d = datetime.today()
    # new_finance = Finances(month_year=date(d.year, d.month, 1), 
    #                        income_users=1000, expenses_hall=500)
    # db.session.add(new_finance)
    # db.session.commit()

    ytd = db.session.query(Finances).first()
    # print(ytd.month_year.year == mmyy.year and ytd.month_year.month == mmyy.month)
    # print(ytd.month_year, type(ytd.month_year))
    # print(ytd.month_year, date(d.year, d.month, 1), ytd.month_year == date(d.year, d.month, 1))
    byMonthYear = db.session.query(Finances).filter_by(month_year=date(d.year, d.month, 1)).first()
    print(byMonthYear)

    users = db.session.query(User).all()
    for user in users:
        print(user.name)
        print(user.hash)
    return render_template('test.html', users=users)
