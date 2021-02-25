"""
Here we create the Database object which methods will help us work with a database for things like adding payments,
debts, gathering the info for showing the operations, etc.
"""
import logging
import time

from datetime import datetime
from utils.database_connection import DatabaseConnection, sqlite3
from typing import List, Set, Tuple
from .users import ADMIN

with open('log.txt', 'w'):
    print()

# Set the basic configurations for the logger
logging.basicConfig(format="%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s", level=logging.DEBUG,
                    filename='log.txt')
# Create the logger
logger = logging.getLogger("Project logger")


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
                cursor.execute("INSERT INTO operaciones VALUES(?, ?, ?)", (name.lower().strip(), amount, date))
            logger.debug("Updating the 'saldos' table.")
            self.update()
        except sqlite3.OperationalError:
            logger.critical("For some reason, a 'sqlite3.OperationalError' was raised.")
            raise

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
    
    def get_individual_balance(self, name: str) -> str:
        """
            Gets the individual's balance given a name. If it doesn't appear in 'saldos' (meaning, it's balance is zero), returns a False statement.
            Otherwise, it returns a string formated to show only two decimal places.
        """
        with DatabaseConnection(self.host) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT amount FROM saldos WHERE name=?", (name.lower(), ))
            client_balance = cursor.fetchone()
            if client_balance:
                return client_balance[0]
            return False

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

    def history(self, name: str) -> Tuple:
        """
            Returns a tuple where each element consits of a list of tuples and a balance. This list of tuples has, in this order,
            the following string objects:
                -> 'debt' or 'payment' corresponding to the operation
                -> the amount (formatted as a string to only show two decimal places)
                -> the operation's date
                -> at what time of this date the operation was loaded into the system.
            
            If the list is empty, then, there are no operations for such individual.

            The 'balance' (the second element of the returned tuple) is either a float or a False statement. If it were a string, contains
            the 'total balance'. It is a False statement when the total is zero.
        """
        with DatabaseConnection(self.host) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT amount, date FROM operaciones WHERE name=? ORDER BY date DESC", (name, ))
            results = cursor.fetchall()
            balance = self.get_individual_balance(name)
            operations = []
            if results:
                for (amount, date) in results:
                    if amount != 0:
                        operation = 'debt' if amount < 0 else 'payment'
                        date = float(date)
                        timestamp = datetime.fromtimestamp(date)
                        date_to_show = timestamp.strftime('%d/%m/%Y')
                        time_to_show = timestamp.strftime('%H:%M')
                        amount_string = "%.2f" % abs(amount)
                        operations.append((operation, amount_string, date_to_show, time_to_show))
            return (operations, balance)
            

    def check_login(self, username: str, password: str):
        with DatabaseConnection(self.host) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM usuarios")
            result = cursor.fetchone()
            if str(result[0]).lower() == username and result[1] == password:
                return True
            else:
                return False
    
    def parcial_maintenance(self):
        """
            The parcial maintenance consists of erasing all of the individual's operations where the debt has
            been payed completety.

            Returns True when the maintenance was done and False when it didn't. Altough, this isn't useful
            at the program's current state, it's more of a 'debugging' device for me to teel if it happened.
        """
        logger.debug("Updating the database")
        self.update()
        with DatabaseConnection(self.host) as connection:
            cursor = connection.cursor()
            logger.debug("Getting the non cancelled debts/payments from the 'saldos' table.")
            cursor.execute("SELECT name FROM saldos")
            results = cursor.fetchall()
            non_cancelled = [
                e[0]
                for e in results
            ]
            logger.debug(f"The following people has yet to cancel their debts/payments: {non_cancelled}")
            logger.debug("Getting the name of all clients within the 'operaciones' table.")
            cursor.execute("SELECT name FROM operaciones")
            results = cursor.fetchall()
            operations_name = {
                e[0]
                for e in results
            }
            logger.debug(f"The following people has operations within the 'operaciones' table: {operations_name}")
            logger.debug("Checking for the 'unmatches' between the previous list and set.")
            suitable_for_maintenance = [
                e
                for e in operations_name
                if e not in non_cancelled
            ]
            if any(suitable_for_maintenance):
                logger.debug(f"The following names are suitable for maintenance: {suitable_for_maintenance}. Performing maintenance...")
                for name in suitable_for_maintenance:
                    logger.debug(f"Erasing {name.title()}'s operations.")
                    cursor.execute("DELETE FROM operaciones WHERE name=?", (name, ))
                    logger.debug(f"Loading a 'zero' operation for {name.title()}")
                    cursor.execute("INSERT INTO operaciones VALUES(?, ?, ?)", (name, 0, time.time()))
                return True
            else:
                logger.error("There were no candidates to perform such maintenance.")
                return False

    def total_maintenance(self) -> True:
        """
            The total maintenance constists of erasing all the operations for all individuals, leaving only one, where
            we synthesize the debt/payment for that person at the moment.
        """
        logger.debug("Performing total maintenance. First, we do a parcial one.")
        self.parcial_maintenance()
        with DatabaseConnection(self.host) as connection:
            cursor = connection.cursor()
            logger.debug("Getting the actual account state for each individual from 'saldos'.")
            cursor.execute("SELECT * FROM saldos")
            results = cursor.fetchall()
            for (name, amount) in results:
                logger.debug(f"Erasing all of {name.title()}'s operations.")
                cursor.execute("DELETE FROM operaciones WHERE name=?", (name, ))
                logger.debug(f"Adding a operation to synthesize the state of the account.")
                cursor.execute("INSERT INTO operaciones VALUES(?, ?, ?)", (name, amount, time.time()))
        logger.debug("Total maintenance performed correctly.")
        return True

