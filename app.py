"""
This program is meant to take debts and payments given a name. It should also store dates for this operations.

Aside from that, I want to build a Flask app to manage this, instead of using the console.
"""
from utils.database_managment import Database
from menu import Operations, MainMenu
from flask import Flask, redirect, render_template, url_for

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


@app.route('/')
def home():
    return render_template('index.html', WELCOME_STRING=WELCOME_STRING)


@app.route('/display_totals')
def display_totals():
    balances = database.show_balances()
    return render_template('saldos.html', balances=balances)


@app.route('/add_operation')
def add_operation():
    return render_template('add_operation.html')


### FLASK RUN ONLY IF THIS IS THE MAIN SCRIPT ###
if __name__ == '__main__':
    clients = database.get_clients()
    print(clients)
    app.run(debug=True)
    

