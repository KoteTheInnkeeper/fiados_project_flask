"""
Here we create the Database object which methods will help us work with a database for things like adding payments,
debts, gathering the info for showing the operations, etc.
"""
import logging
import time
from datetime import datetime

from utils.database_connection import DatabaseConnection, sqlite3

# Set the basic configurations for the logger
logging.basicConfig(format="%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s", level=logging.DEBUG,
                    filename='log.txt')
# Create the logger
logger = logging.getLogger("Project logger")


class Database:
    def __init__(self, host: str):
        self.host = host
        logger.debug(f"'Database' object referred to {self.host}")

    def create_tables(self):
        try:
            with DatabaseConnection(self.host) as connection:
                cursor = connection.cursor()
                cursor.execute("CREATE TABLE IF NOT EXISTS operaciones(name TEXT, amount FLOAT, date FLOAT)")
                cursor.execute("CREATE TABLE IF NOT EXISTS saldos(name TEXT UNIQUE primary key, amount FLOAT)")
        except sqlite3.OperationalError:
            logger.error(f"sqlite3.OperationalError encountered. Check the traceback.")
            raise

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
                self.create_tables()
        except FileNotFoundError:
            logger.error(f"{self.host} wasn't found. Creating a new one...")
            with open(self.host, 'w'):
                logger.debug(f"{self.host} successfully created.")
            logger.debug(f"Creating the 'operaciones' and 'saldos' tables in {self.host}")
            self.create_tables()

    def add_debt(self, name: str, amount: float) -> None:
        """
            This method deals with adding a debt to the database.

        :param name: client's name
        :param amount: amount the client contracted debt for
        """
        logger.debug("Try to get today's date and add the debt.")
        try:
            date = time.time()
            amount = abs(amount)
            with DatabaseConnection(self.host) as connection:
                cursor = connection.cursor()
                cursor.execute("INSERT INTO operaciones VALUES(?, ?, ?)", (name.lower(), -amount, date))
            logger.debug("Updating the 'saldos' table.")
            self.update()
        except sqlite3.OperationalError:
            logger.critical("For some reason, a 'sqlite3.OperationalError' was raised.")
            raise
        else:
            print(f"La deuda de {name.title()} por $%.2f fue cargada correctamente." % amount)

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
            print(f"El pago de {name.title()} por $%.2f fue agregado correctamente." % amount)

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

    def show_balances(self) -> None:
        self.update()
        with DatabaseConnection(self.host) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM saldos ORDER BY name")
            results = cursor.fetchall()
            if any(results):
                print("Los saldos al día de la fecha se muestran a continuación.")
                for i, (name, amount) in enumerate(results, start=1):
                    status_string = 'debe' if amount < 0 else 'tiene a favor'
                    print(f"{i}) {name.title()} {status_string} $%.2f." % abs(amount))
            else:
                print("¡No hay saldos pendientes!")

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

