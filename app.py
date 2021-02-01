"""
This program is meant to take debts and payments given a name. It should also store dates for this operations.
"""
from utils.database_managment import Database
from menu import Operations, MainMenu

HOST = 'utils/database_file.db'

# Create the Database object for HOST
database = Database(HOST)
# Initialize and update the database.
database.initialize()
database.update()

# First print
print("Bienvenido a la versión 2.0 del programa de deudas. Este le ayudará a llevar las deudas y pagos de"
    " las distintas personas que interactúen con su negocio. Además, le permitirá ver el historial de"
    " operaciones para algún cliente particular, así como revisar los saldos actuales.")

# Print the first 'help' message and then run the main menu.
print(MainMenu.HELP_STRING)
MainMenu.loop(database)