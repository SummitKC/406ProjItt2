from random import randint
from helpers import *
from datetime import datetime, date
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
        self.total_payments += 1
        db.session.commit()

    def update_weekly_status(self, week_number, attendance, paid):
        if not self.weekly_status:
            self.weekly_status = {}
        # user has not paid but has registered for a class
        if paid == False:
            self.weekly_status[week_number] = [attendance, 0]
        # user has both registered and paid for a class
        else:
            # idk why i have to return in this else but it wont work otherwise
            self.weekly_status[week_number] = [attendance, self.current_payment]
            flag_modified(self, "weekly_status")
            self.add_total_payments()
            db.session.commit()
            return 
        
        flag_modified(self, "weekly_status")
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
        return month_profit
    
class Classes(db.Model):
    week = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.Date, nullable=False)

@app.route('/')
@login_required 
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        Email = request.form['email']
        name = request.form['name']
        message = request.form['message']
        send_mail_self(Email, name, message )
        flash('Email Sent')
        return render_template('contact.html')
    return render_template('contact.html')

@app.route('/reqadmin', methods=['GET', 'POST'])
def request_admin():
    if request.method == 'POST':
        email = request.form['email']
        usernames = sorted(db.session.query(Admins), key=lambda x: x.username)
        if usernames:
            admin_num = str(int(usernames[-1].username[-1]) + 1)
            new_admin_name = f'admin{admin_num}'
        else:
            new_admin_name = 'admin1'
        password = ""
        for _ in range(10):
            password += str(randint(0,9))
        new_admin = Admins(username=new_admin_name, hash=generate_password_hash(password))
        db.session.add(new_admin)
        db.session.commit()
        send_mail(email, (new_admin_name, password))
        return render_template('reqadmin.html', req_sent=True)
    else:
        return render_template('reqadmin.html', req_sent=False)
    
@app.route('/adminlogin',methods=['GET', 'POST'])
def adminlogin(): 
    session.clear()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        admin = db.session.query(Admins).filter_by(username=username).first()
        if admin and check_password_hash(admin.hash, password):
            session['admin_id'] = admin.id
            return redirect('/admin') 
        else:
            #TODO: change this to give a popup notifying the user instead of redirecting them

            return render_template('error.html', err_msg="Incorrect Username or Password")
    else:
        return render_template('adminlogin.html')

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
            flash ('Incorrect Username or Password')
            return render_template('/login.html')
    else:
        return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/admin') # TODO add admin login later 
@admin_required 
def admin():
    return render_template('adminhome.html')

@app.route('/adminhome', methods=['GET', 'POST'])
@admin_required
def adminhome():
    if request.method == 'POST':
        class_date = request.form['class']
        # string index is safe as date format is always yyyy-mm-dd
        new_class = Classes(date=datetime(int(class_date[0:4]), int(class_date[5:7]), int(class_date[8:])))
        db.session.add(new_class)
        db.session.commit()
        newClasses = db.session.query(Classes).all()
        weeks = [(str(week.week), str(week.date))for week in newClasses]
        weeksDate = [str(week.date) for week in newClasses]
        return render_template('adminhome.html', weeks = weeks)

    date = datetime.today()
    year = str(date.year)
    month = zero_padding(str(date.month))
    day = zero_padding(str(date.day))
    return render_template('adminhome.html', year=year, month=month, day=day)

@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    if request.method == 'POST':
        # a post request on this function means the user registered, but did not paid for a class
        week_number = list(request.form.keys())[0]
        user = db.session.query(User).filter_by(username=session['username']).first()
        session['payment'] = user.current_payment
        user.update_weekly_status(week_number, 'attended', False)
        print(week_number)
        newClasses = db.session.query(Classes).all()
        weeks = [(str(week.week), str(week.date)) for week in newClasses]
        return render_template('account.html', weeks = weeks, payment=user.current_payment, status=user.weekly_status)
    else:
        newClasses = db.session.query(Classes).all()
        weeks = [(str(week.week), str(week.date)) for week in newClasses]
        user = db.session.query(User).filter_by(username=session['username']).first()
        return render_template('account.html', weeks = weeks, payment=user.current_payment, status=user.weekly_status)

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

            # query finance to get correct month/year to update
            d = datetime.today()
            finance = db.session.query(Finances).filter_by(month_year=date(d.year, d.month, 1)).first()
            # if mm/yy not in db (could be because new month) create the row and add it to db
            if not finance:
                finance = Finances(month_year=date(d.year, d.month, 1), income_users=0, income_other=0,
                                expenses_coach=0, expenses_hall=0, expenses_other=0)
                db.session.add(finance)
                db.session.commit()

            currUserPay = db.session.query(User).filter_by(username=session['username']).first()
            print(currUserPay)
            currUserPay.update_weekly_status(week, "attended", True)
            finance.addUserIncome(currUserPay.current_payment, 'u')
            return redirect('/account')
        else: 
            flash("Declined")
            return redirect('/payment')
    
    week = request.args.get('week')
    return render_template('payment.html', week=week)

@app.route('/finance', methods=['GET', 'POST'])
@admin_required
def finance():
    finance_info = db.session.query(Finances).all()
    if request.method == 'POST':
        today = datetime.today()
        year_month_only = date(today.year, today.month, 1)
        expenseType = request.form['expenseType']
        expenseAmount = int(request.form['expenseAmount'])
        entered = False
        for month in finance_info:
            print(type(month.month_year), type(year_month_only))
            if month.month_year == year_month_only:
                if (expenseType == "coach"):
                    month.expenses_coach += expenseAmount
                    db.session.commit()
                    entered = True
                elif (expenseType == "hall"):
                    month.expenses_hall += expenseAmount
                    db.session.commit()
                    entered = True
                elif (expenseType == "other"):
                    month.expenses_other += expenseAmount
                    db.session.commit()
                    entered = True

        if (not entered):
            if (expenseType == "coach"):
                db.session.add(Finances(month_year = year_month_only, income_users = 0, income_other = 0, expenses_coach=expenseAmount, expenses_hall=0, expenses_other=0))
                db.session.commit()
                print("coach add")
                entered = True
            elif (expenseType == "hall"):
                db.session.add(Finances(month_year = year_month_only, income_users = 0, income_other = 0, expenses_coach=0, expenses_hall=expenseAmount, expenses_other=0))
                month.expenses_hall += expenseAmount
                db.session.commit()
                print("hall add")
                entered = True
            elif (expenseType == "other"):
                db.session.add(Finances(month_year = year_month_only, income_users = 0, income_other = 0, expenses_coach=0, expenses_hall=0, expenses_other=expenseAmount))
                db.session.commit()
                print("other add")
                entered = True
    #db.session.add(Finances(month_year = datetime(randint(1900, 2024), randint(1, 12), randint(1, 28)),income_users = randint(1000, 10000), income_other = randint(1000, 10000), expenses_coach=randint(1000, 2000), expenses_hall=randint(1000, 2000), expenses_other=randint(1000, 2000)))
    #db.session.add(Finances(month_year = datetime(randint(1900, 2024), randint(1, 12), randint(1, 28)),income_users = randint(1000, 10000), income_other = randint(1000, 10000), expenses_coach=randint(1000, 2000), expenses_hall=randint(1000, 2000), expenses_other=randint(1000, 2000)))

    return render_template('finance.html', lt_profit=calculate_total_profit(finance_info), lt_income=calculate_total_income(finance_info),
                            lt_expenses=calculate_total_expenses(finance_info), finance_info=finance_info)

@app.route('/test', methods=['GET', 'POST'])
@admin_required
def pickSortFunction():

    if request.method == 'POST':
        
        if request.form['sort'] == "completedPayment":
            return test2()
        elif request.form['sort'] == "classAttendence":
            return test()
        else: 
            return test3()
    
    return test3()

def test3():
    users = db.session.query(User).all()
    usersAsList = []
    for user in users:
        usersAsList.append([user.name, user.username, user.phone_number, user.address])
    return render_template('test.html', users=usersAsList, sortCriteria="")

def test():
    # sort by number of classes attended
    users = db.session.query(User).all()
    usersAsList = []
    usersSorted = []
    maxClassesAttended = 0
    for user in users:
        usersAsList.append([user.name, user.username, user.phone_number, user.address, len(user.weekly_status)])
        maxClassesAttended = max(len(user.weekly_status), maxClassesAttended)
    
    # add based on classes attended
    for i in range(maxClassesAttended + 1):
        for user in usersAsList:
            if (user[-1] == i):
                usersSorted.append(user)
    usersSorted.reverse()
    return render_template('test.html', users=usersSorted, sortCriteria="Number of Classes Attended")

def test2():
    # sort by classes paid for
    users = db.session.query(User).all()
    usersAsList = []
    usersSorted = []
    maxTotalPayments = 0
    for user in users:
        usersAsList.append([user.name, user.username, user.phone_number, user.address, user.total_payments])
        maxTotalPayments = max(user.total_payments, maxTotalPayments)
    
    # add based on classes attended
    for i in range(maxTotalPayments + 1):
        for user in usersAsList:
            if (user[-1] == i):
                usersSorted.append(user)
    usersSorted.reverse()
    return render_template('test.html', users=usersSorted, sortCriteria="Total Payments")