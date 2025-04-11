from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re

app = Flask(__name__, template_folder='template')
app.secret_key = 'your_secret_key'

# MySQL config
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'your password'      '''change your password and delete this comment'''
app.config['MYSQL_DB'] = 'bank_db'

mysql = MySQL(app)

# -------------------------
# Landing Page
# -------------------------
@app.route('/')
def landing():
    if 'user_id' in session:
        return redirect(url_for('home'))
    return render_template('landing.html')


# -------------------------
# Signup
# -------------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()
        if user:
            flash("Email already registered.")
            return redirect(url_for('signup'))

        cursor.execute('INSERT INTO users (name, email, password) VALUES (%s, %s, %s)', (name, email, password))
        mysql.connection.commit()
        flash("Account created successfully. Please login.")
        return redirect(url_for('login'))

    return render_template('signup.html')


# -------------------------
# Login
# -------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM users WHERE email = %s AND password = %s', (email, password))
        user = cursor.fetchone()

        if user:
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            return redirect(url_for('home'))
        else:
            flash("Incorrect email or password.")
            return redirect(url_for('login'))

    return render_template('login.html')


# -------------------------
# Logout
# -------------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('landing'))


# -------------------------
# Home Dashboard
# -------------------------
@app.route('/home', methods=['GET', 'POST'])
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT SUM(CASE WHEN type="deposit" THEN amount ELSE -amount END) FROM transactions WHERE user_id = %s', (user_id,))
    balance = cursor.fetchone()[0] or 0.00

    if request.method == 'POST':
        amount = float(request.form['amount'])
        txn_type = request.form['type']
        cursor.execute('INSERT INTO transactions (user_id, type, amount) VALUES (%s, %s, %s)', (user_id, txn_type, amount))
        mysql.connection.commit()
        flash("Transaction successful.")
        return redirect(url_for('home'))

    return render_template('index.html', balance=balance)


# -------------------------
# Transactions
# -------------------------
@app.route('/transactions')
def display():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT type, amount, timestamp FROM transactions WHERE user_id = %s ORDER BY timestamp DESC', (user_id,))
    transactions = cursor.fetchall()

    cursor.execute('SELECT SUM(CASE WHEN type="deposit" THEN amount ELSE -amount END) FROM transactions WHERE user_id = %s', (user_id,))
    balance = cursor.fetchone()[0] or 0.00

    return render_template('transactions.html', transactions=transactions, balance=balance)


# -------------------------
# EMI Calculator
# -------------------------
@app.route('/emi', methods=['GET', 'POST'])
def emi():
    emi = None
    if request.method == 'POST':
        principal = float(request.form['principal'])
        rate = float(request.form['rate']) / 12 / 100
        time = int(request.form['time']) * 12

        emi = (principal * rate * ((1 + rate) ** time)) / (((1 + rate) ** time) - 1)

    return render_template('emi.html', emi=emi)


# -------------------------
# Interest Rate Viewer
# -------------------------
@app.route('/interest', methods=['GET', 'POST'])
def interest():
    bank_rates = {
        'SBI': 6.8,
        'HDFC': 7.2,
        'ICICI': 7.0,
        'AXIS': 6.9,
        'PNB': 6.7
    }
    selected_bank = None
    interest_rate = None

    if request.method == 'POST':
        selected_bank = request.form['bank']
        interest_rate = bank_rates.get(selected_bank)

    return render_template('interest.html', bank_rates=bank_rates, selected_bank=selected_bank, interest_rate=interest_rate)


# -------------------------
# Run the Flask App
# -------------------------
if __name__ == '__main__':
    app.run(debug=True)
