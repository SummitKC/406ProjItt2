from helpers import login_required, get_key, send_mail
import datetime
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

class Finance(db.Model):
    month_year = db.Column(db.DateTime, primary_key=True)
    profit = db.Column(db.Integer)
    expenses = db.Column(db.Integer)

    def __repr__(self) -> str:
        return f'| MM/YYYY: {self.month_year} | Profit: {self.profit} | Expenses: {self.expenses} |'


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

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')

@app.route('/test')
def test():
    users = db.session.query(User).all()
    for user in users:
        print(user.name)
        print(user.hash)
    return render_template('test.html', users=users)
