"""
This program is meant to take debts and payments given a name. It should also store dates for this operations.

Aside from that, I want to build a Flask app to manage this, instead of using the console.
"""
from utils.database_managment import Database
from flask import Flask, redirect, render_template, url_for, session, request
from datetime import timedelta

WELCOME_STRING = """Bienvenido a la versión 2.0 del programa de deudas. Este le ayudará a llevar las deudas y pagos de
las distintas personas que interactúen con su negocio. Además, le permitirá ver el historial de
operaciones para algún cliente particular, así como revisar los saldos actuales."""

HOST = 'utils/database_file.db'

# Create the Database object for HOST
database = Database(HOST)
# Initialize and update the database.
database.initialize()
database.update()


### FLASK APP ###
app = Flask(__name__)
app.secret_key = "J@tAYGpzdCRL6C2jKBuW&8"
app.permanent_session_lifetime = timedelta(hours=8)


@app.route('/')
def home():
    try:
        if session['user']:
            return render_template('index.html', WELCOME_STRING=WELCOME_STRING)
    except KeyError:
        return redirect(url_for('login'))
        

@app.route('/totals')
def display_totals():
    try:
        if session['user']:
            balances = database.show_balances()
            return render_template('saldos.html', balances=balances)
    except KeyError:
        return redirect(url_for('login'))


@app.route('/add', methods=['POST', 'GET'])
def add_operation():
    try:
        if session['user']:
            try:
                if request.method == 'POST':
                    # Get te form's data.
                    old_name = '' if request.form['old_client'] == 'No está en la lista' else request.form['old_client']
                    new_name = request.form['new_client']
                    try:
                        amount = float(str(request.form['amount']).strip().strip('-'))
                    except ValueError:
                        return redirect(url_for('add_operation'))                    
                    operation = request.form['op_radio']                    
                    if (old_name or new_name) and amount:
                        if not old_name:
                            name = new_name
                        else:
                            name = old_name
                        database.add_operation(name, amount, operation)
                    else:
                        return redirect(url_for('add_operation'))

                    return redirect(url_for('display_totals'))
                else:
                    clients = database.get_clients()
                    return render_template('add_operation.html', clients=clients)
            except:
                raise
    except KeyError:
        return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session.permament = True
        user = request.form['user']
        password = request.form['pass']
        if database.check_login(user, password):
            session['user'] = user
            return redirect(url_for('home'))
        else:
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

### FLASK RUN ONLY IF THIS IS THE MAIN SCRIPT ###
if __name__ == '__main__':
    app.run(debug=True)
    

