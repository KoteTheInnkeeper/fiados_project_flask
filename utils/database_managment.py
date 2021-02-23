"""
Here we create the Database object which methods will help us work with a database for things like adding payments,
debts, gathering the info for showing the operations, etc.
"""
import logging
import time

from datetime import datetime
from utils.database_connection import DatabaseConnection, sqlite3
from typing import List, Set
from .users import ADMIN

with open('log.txt', 'w'):
    print()

# Set the basic configurations for the logger
logging.basicConfig(format="%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s", level=logging.DEBUG,
                    filename='log.txt')
# Create the logger
logger = logging.getLogger("Fiados_logger.Database")


class Database:
    def __init__(self, host: str):
        self.host = host
        logger.debug(f"New log file created and 'Database' object referred to {self.host}.")
        try:
            logger.debug(f"Checking if {self.host} exists")
            with open(self.host, 'r'):
                logger.debug(f"{self.host} exists")            
        except FileNotFoundError:
            with open(self.host, 'w'):
                logger.error(f"{self.host} created, since it did't exist.")
        finally:
            with DatabaseConnection(self.host) as connection:
                cursor = connection.cursor()
                cursor.execute("CREATE TABLE IF NOT EXISTS operaciones(name TEXT, amount FLOAT, date FLOAT)")
                cursor.execute("CREATE TABLE IF NOT EXISTS saldos(name TEXT UNIQUE primary key, amount FLOAT)")
                cursor.execute("CREATE TABLE IF NOT EXISTS usuarios(name TEXT UNIQUE primary key, password TEXT)")
                cursor.execute("INSERT OR IGNORE INTO usuarios VALUES(?, ?)", (ADMIN[0], ADMIN[1]))

    def initialize(self):
        """
            This function deals with checking if the 'database' file exists, creating one if it doesn't, and initialize
            it from the tables perspective; we need two tables: 'operaciones' and 'saldos'.
        :return:
        """
        try:
            logger.debug(f"Checking if {self.host} exists")
            with open(self.host, 'r'):
                logger.debug(f"{self.host} exists. If 'operaciones' and 'saldos' tables don't exist, they will be "
                             f"created.")
                # Query for creating tables if they don't exist.
        except FileNotFoundError:
            logger.error(f"{self.host} wasn't found. Creating a new one...")
            with open(self.host, 'w'):
                logger.debug(f"{self.host} successfully created.")
            logger.debug(f"Creating the 'operaciones' and 'saldos' tables in {self.host}")
            self.create_tables()

    def add_operation(self, name: str, amount: float, operation: str) -> None:
        """
            This method deals with adding an operation to the database.

        :param name: client's name
        :param amount: amount the client contracted debt for
        :param operation: 'debt' or 'payment'. 
        """
        logger.debug("Try to get today's date and add the operation.")
        try:
            date = time.time()
            amount = abs(amount)
            with DatabaseConnection(self.host) as connection:
                cursor = connection.cursor()
                amount = (-1 * amount) if operation == 'debt' else amount
                cursor.execute("INSERT INTO operaciones VALUES(?, ?, ?)", (name.lower(), amount, date))
            logger.debug("Updating the 'saldos' table.")
            self.update()
        except sqlite3.OperationalError:
            logger.critical("For some reason, a 'sqlite3.OperationalError' was raised.")
            raise

    def update(self):
        # Let's get the names in the operaciones table.
        with DatabaseConnection(self.host) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT name FROM operaciones")
            names = {e[0] for e in cursor.fetchall()}  # {'NON', 'REPEATED', 'NAMES'}
            cursor.execute("DELETE FROM saldos")
            # Search for the total for each person and add it to the database.
            for name in names:
                try:
                    cursor.execute("SELECT amount FROM operaciones WHERE name=?", (name, ))
                    amounts = [e[0] for e in cursor.fetchall()]
                    total = sum(amounts)
                    cursor.execute("INSERT INTO saldos VALUES(?, ?)", (name, total))
                except sqlite3.OperationalError:
                    logger.critical("For some reason, a 'sqlite3.OperationalError' was raised.")
        # Update and erase totals equal to zero
        with DatabaseConnection(self.host) as connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM saldos WHERE amount=0")

    def add_payment(self, name: str, amount: float) -> None:
        """
            This method deals with adding a debt to the database.
        :param name: client's name
        :param amount: amount the client payed.
        :return:
        """
        logger.debug("Try to get today's date and add the payment.")
        try:
            date = time.time()
            amount = abs(amount)
            with DatabaseConnection(self.host) as connection:
                cursor = connection.cursor()
                cursor.execute("INSERT INTO operaciones VALUES(?, ?, ?)", (name.lower(), amount, date))
            logger.debug("Updating database.")
            self.update()
        except sqlite3.OperationalError:
            logger.critical("For some reason, a 'sqlite3.OperationalError' was raised.")
            raise
        else:
            logger.debug(f"{name.title()}'s payment for $.2f added succesfully." % amount)

    def show_balances(self) -> List:
        """
            Returns a list where each element it's a tuple with two elements: name and amount of
            the balance.
        """
        self.update()
        with DatabaseConnection(self.host) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM saldos ORDER BY name")
            results = cursor.fetchall()
            logger.debug("Gathering balances")
            if any(results):
                balances = (
                    (name, amount)
                    for name, amount in results
                )
                logger.debug("Balances found were put into a list and returned.")
                return balances

    def get_clients(self) -> List:
        """
            Returns a list where each element is a client's name. These names are gathered
            from the 'operaciones' table. This means that any client who payed or contracted
            a debt before is going to figure here. 

            I pictured this would be useful when the prompt for 'adding a debt' (or payment)
            was raised, since I want the user to be able to 'select' a client's name or 'insert
            a new one' if it's needed.
        """
        with DatabaseConnection(self.host) as connection:
            cursor = connection.cursor()
            logger.debug("Geting the names in the 'operaciones' table.")
            cursor.execute("SELECT name FROM operaciones ORDER BY name")
            results = cursor.fetchall()
            if results:
                logger.debug("Clients found. Saving them into a set")
                clients = []
                for e in results:
                    if e[0] not in clients:
                        clients.append(e[0])
                logger.debug("Returning these clients as a list")
                return clients
            logger.debug("There are no clients yet!")
            return []



    def show_history(self, name: str) -> None:
        with DatabaseConnection(self.host) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT amount, date FROM operaciones WHERE name=? ORDER BY date", (name, ))
            results = cursor.fetchall()
            if any(results):
                print(f"Las operaciones efectuadas por {name.title()} se muestran a continuación.")
                for i, (amount, date) in enumerate(results, start=1):
                    string_status = 'PAGÓ' if amount > 0 else 'SE FIÓ'
                    date = float(date)
                    timestamp = datetime.fromtimestamp(date)
                    date_to_show = timestamp.strftime('%d/%m/%Y')
                    time_to_show = timestamp.strftime('%H:%M')
                    print(f"\t->{string_status} $%.2f el día {date_to_show} a las {time_to_show}" % abs(amount))
            else:
                print(f"No se han encontrado operaciones para {name.title()}. Compruebe que lo ha escrito correctamente.")

    def check_login(self, username: str, password: str):
        with DatabaseConnection(self.host) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM usuarios")
            result = cursor.fetchone()
            if str(result[0]).lower() == username and result[1] == password:
                return True
            else:
                return False

