from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String
from sqlalchemy.orm import sessionmaker, backref
from flask import session
import os
import datetime
import json


app = Flask(__name__)
app.secret_key = os.urandom(24)

# /// = relative path, //// = absolute path
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


# def create_session():
#     Session = sessionmaker()
#     Session.configure(bind=engine)
#     session = Session()
#     return session

@app.route('/')
def welcome():
    return render_template('welcome.html')


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/register')
def about():
    return render_template('register.html')


@app.route("/home")
def home():
    if "user_id" in session:
        data = Expense.query.filter_by( user_id = session['user_id'])
        return render_template('home.html', data = data)
    else:
        return redirect('/login')


@app.route("/expenses", methods=["GET"])
def expenses():
    """Manage expenses"""
    return render_template("addexpenses.html")


@app.route("/adddataindb", methods=["GET", "POST"])
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
        data = Expense.query.filter_by(user_id = session['user_id'])
        return render_template('home.html', data=data)


@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    name = request.form.get("uname")
    email = request.form.get("uemail")
    password = request.form.get("upassword")
    new_user = Users(name=name, email=email, password=password)
    db.session.add(new_user)
    db.session.commit()
    return render_template('login.html')


@app.route('/login_validation', methods=['GET', 'POST'])
def login_validation():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        users = Users.query.filter_by(email=email, password=password).first()
        if users:
            session['user_id'] = users.id
            return redirect('/home')
        else:
            return redirect('/register')


@app.route("/logout")
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
