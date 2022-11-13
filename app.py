from flask import Flask, render_template, request, redirect, url_for, Response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String
from sqlalchemy.orm import sessionmaker, backref
from flask import session
import os
import io
import datetime
from functools import wraps
# from werkzeug.security import generate_password_hash, check_password_hash
import json
import xlwt

app = Flask(__name__)
app.secret_key = os.urandom(24)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    password = db.Column(db.String(100))
    income = db.Column(db.Float(10), default=60000.0)

    def __repr__(self):
        return f"Register('{self.id}','{self.name}','{self.email}','{self.password}')"


class Expense(db.Model):
    __tablename__ = 'expense'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.Text, nullable=False)
    expense_date = db.Column(db.Text, nullable=False)
    amount = db.Column(db.Float(100), nullable=False)
    payer = db.Column(db.Text, nullable=False)
    submit_time = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    users = db.relationship("Users", backref=backref("users", uselist=False))

    def __repr__(self):
        return f"Expense('{self.id}','{self.description}','{self.category}','{self.user_id}')"



def login_required(test):
    @wraps(test)
    def wrap(*args, **kwargs):
        if 'user_id' in session:
            return test(*args, **kwargs)
        else:
            return redirect(url_for('login'))

    return wrap


@app.route('/')                 #welcome page
def welcome():
    return render_template('welcome.html')


@app.route('/login')                 #login page
def login():
    return render_template('login.html')


@app.route('/register')          #registeration page
def about():
    error = None
    return render_template('register.html', error=error)


@app.route("/reports")
@login_required
def reports():
    if "user_id" in session:
        data = Expense.query.filter_by(user_id=session['user_id']).all()
        output = io.BytesIO()         #output in bytes
        workbook = xlwt.Workbook()      #to create workbook object
        sh = workbook.add_sheet('Expense Report')    #add a a sheet
        sh.write(0, 0, 'ID')                        #add a header
        sh.write(0, 1, 'DESCRIPTION')
        sh.write(0, 2, 'CATEGORY')
        sh.write(0, 3, 'EXPENSE_DATE')
        sh.write(0, 4, 'AMOUNT')
        sh.write(0, 5, 'PAYER')
        idx = 0
        for row in data:
            sh.write(idx+1, 0, str(row.id))
            sh.write(idx+1, 1, row.description)
            sh.write(idx+1, 2, row.category)
            sh.write(idx+1, 3, row.expense_date)
            sh.write(idx+1, 4, str(row.amount))
            sh.write(idx+1, 5, row.payer)
            idx+= 1
        workbook.save(output)
        output.seek(0)

        return Response(output, mimetype="application/ms-excel", headers={"Content-Disposition": "attachment;filename=expense_report.xls"})







@app.route('/account')
@login_required
def account():
    data = Expense.query.filter_by(user_id=session['user_id']).all()
    users = Users.query.filter_by(id=session['user_id']).all()
    ex = sum([i.amount for i in data])
    count = len([i.amount for i in data])
    return render_template('accountpage.html', data=users, ex=ex, count=count)


@app.route('/weekly')
@login_required
def weekly():
    # weekly_graph = Expense.query.filter(
    #     Expense.expense_date.between((datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y-%m-%d"),
    #                                  (datetime.datetime.now()).strftime("%Y-%m-%d"))).group_by(Expense.expense_date)

    var = Expense.query.with_entities(db.func.sum(Expense.amount).label("amount"), Expense.expense_date).group_by(Expense.expense_date).filter(
        Expense.expense_date.between((datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y-%m-%d"),
                                     (datetime.datetime.now()).strftime("%Y-%m-%d")))
    amount = [i.amount for i in var]
    dates = [i.expense_date for i in var]
    return render_template('weeklygraph.html', amount=json.dumps(amount), dates=json.dumps(dates))


@app.route('/monthly')
@login_required
def monthly():
    # monthly_graph = Expense.query.filter(
    #     Expense.expense_date.between((datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d"),
    #                                  (datetime.datetime.now()).strftime("%Y-%m-%d")))
    var = Expense.query.with_entities(db.func.sum(Expense.amount).label("amount"), Expense.expense_date).group_by(
        Expense.expense_date).filter(
        Expense.expense_date.between((datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d"),
                                     (datetime.datetime.now()).strftime("%Y-%m-%d")))
    amount = [i.amount for i in var]
    dates = [i.expense_date for i in var]
    return render_template('monthlygraph.html', amount=json.dumps(amount), dates=json.dumps(dates))


@app.route("/home")
@login_required
def home():
    if "user_id" in session:
        data = Expense.query.filter_by(user_id=session['user_id']).order_by(Expense.id.desc())
        ex = sum([i.amount for i in data])
        weekly = Expense.query.filter(
            Expense.expense_date.between((datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y-%m-%d"),
                                         (datetime.datetime.now()).strftime("%Y-%m-%d")))
        for i in weekly:
            print(i.expense_date)
        ex_weekly = sum([i.amount for i in weekly])
        amount = [i.amount for i in weekly]
        dates = [i.expense_date for i in weekly]
        print(amount)
        monthly = Expense.query.filter(
            Expense.expense_date.between((datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d"),
                                         (datetime.datetime.now()).strftime("%Y-%m-%d")))
        ex_monthly = sum([i.amount for i in monthly])
        print(ex_monthly)
        data = data.limit(3)
        return render_template('home.html', data=data, ex=ex, ex_weekly=ex_weekly, ex_monthly=ex_monthly)
    else:
        return redirect('/login')


@app.route("/expenses", methods=["GET"])
@login_required
def expenses():
    """Manage expenses"""
    return render_template("addexpenses.html")


@app.route("/adddataindb", methods=["GET", "POST"])
@login_required
def adddataindb():
    if request.method == "POST":
        # formData = request.form
        description = request.form.get("description")
        category = request.form.get("category")
        date = request.form.get("date")
        payer = request.form.get("payer")
        amount = request.form.get("amount")
        data = Expense(description=description, category=category, expense_date=date, payer=payer, amount=amount,
                       submit_time=datetime.datetime.now().strftime("%H:%M"), user_id=session['user_id'])
        db.session.add(data)
        db.session.commit()
        data = Expense.query.filter_by(user_id=session['user_id']).order_by(Expense.id.desc())
        ex = sum([i.amount for i in data])
        weekly = Expense.query.filter(
            Expense.expense_date.between((datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y-%m-%d"),
                                         (datetime.datetime.now()).strftime("%Y-%m-%d")))
        ex_weekly = sum([i.amount for i in weekly])
        print(ex_weekly)
        monthly = Expense.query.filter(
            Expense.expense_date.between((datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d"),
                                         (datetime.datetime.now()).strftime("%Y-%m-%d")))
        ex_monthly = sum([i.amount for i in monthly])
        print(ex_monthly)
        data = data.limit(3)
        return render_template('home.html', data=data, ex=ex, ex_weekly=ex_weekly, ex_monthly=ex_monthly)


@app.route("/update/<int:id>", methods=["GET", "POST"])
@login_required
def update(id):
    if request.method == "GET":
        data = Expense.query.filter_by(id=id).first()
        y = [data]
        # for i in y:
        #     print(i.id)
        #     print(i.category)
        return render_template('update.html', data=[data])


@app.route("/addupdatedata/<int:id>", methods=["GET", "POST"])
@login_required
def addupdatedata(id):
    if request.method == "POST":
        description = request.form.get("description")
        category = request.form.get("category")
        date = request.form.get("date")
        payer = request.form.get("payer")
        amount = request.form.get("amount")
        deleted = Expense.query.filter_by(id=id).first()
        db.session.delete(deleted)
        data = Expense(id=id, description=description, category=category, expense_date=date, payer=payer, amount=amount,
                       submit_time=datetime.datetime.now().strftime("%H:%M"), user_id=session['user_id'])
        db.session.add(data)
        db.session.commit()
        return redirect(url_for('fulltable'))
    return render_template("showtable.html", data=None)


@app.route("/delete/<int:id>", methods=["GET", "POST"])
@login_required
def delete_data(id):
    # data = Users.query.filter_by(user_id=session['user_id']).all()
    if request.method == "GET":
        deleted = Expense.query.filter_by(id=id).first()
        db.session.delete(deleted)
        db.session.commit()
        return redirect(url_for('fulltable'))
    return render_template("showtable.html", data=None)


@app.route("/fulltable", methods=['GET', 'POST'])
@login_required
def fulltable():
    if "user_id" in session:
        data = Expense.query.filter_by(user_id=session['user_id']).all()
        return render_template('showtable.html', data=data)


@app.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    name = request.form.get("uname")
    for x in name:
        if x == " ":
            error = "Invalid Username Contain Spaces"
            return render_template("register.html", error=error)
    email = request.form.get("uemail")
    password = request.form.get("upassword")
    users = Users.query.all()
    for i in users:
        if i.name == name:
            error = "User Already Exist"
            return render_template('register.html', error=error)
        elif i.email == email:
            error = "Email Already Exist"
            return render_template('register.html', error=error)
        elif not password.isalpha:
            error = "Plain Password Not Accepted"
            return render_template('register.html', error=error)
    new_user = Users(name=name, email=email, password=password)
    db.session.add(new_user)
    db.session.commit()
    return render_template('login.html')


@app.route('/login_validation', methods=['GET', 'POST'])
def login_validation():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        users = Users.query.filter_by(email=email).first()
        if users!=None:
            for i in [users]:
                if i.password == password:
                    session['user_id'] = i.id
                    return redirect('/home')
                else:
                    error = "Password is Wrong"
                    return render_template('login.html', error=error)
        else:
            error = "User Not Exist.Please Register"
            return render_template('register.html', error=error)


@app.route("/logout")
@login_required
def logout():
    """Log user out"""
    # Forget any user_id
    session.clear()
    # Redirect user to welcome page
    return redirect("/")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)  # if any changes done in the code then we need not to run the code again and again to see the
    # changes



