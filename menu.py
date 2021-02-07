"""
    In this .py file we manage the 'menu' things, like the available operations, how do we call them, the main menu
    loop, and so on.
"""

from utils.database_managment import Database, logger
from time import sleep

# A few functions for help and quiting the program
def exit_from_program(_):
    print("Gracias por usar este programa!")
    sleep(2)
    exit()



def show_help(_):
    print(MainMenu.HELP_STRING)


class Operations:
    @classmethod
    def gather_debt(cls, database: Database) -> None:
        logger.debug("Getting the debt's info...")
        name = input("¿Quién se fió?\nNombre: ").lower().strip()
        amount = input(f"¿Por cuánto se fió {name.title()}?\n$")
        logger.debug("Making sure the amount entered is a number.")
        while not isinstance(amount, float):
            try:
                amount = abs(float(amount))
            except ValueError:
                print("Al momento de ingresar el monto, utilice el punto (.) como separador decimal.")
                amount = input(f"¿Por cuánto se fió {name.title()}?\n$")
            pass
        logger.debug("Call for the 'add_debt' method within the Database object.")
        database.add_debt(name, amount)

    @classmethod
    def gather_payment(cls, database: Database):
        logger.debug("Getting the payment's info...")
        name = input("¿Quién pagó?\nNombre: ").lower().strip()
        amount = input(f"¿Cuánto pagó {name.title()}?\nCantidad: $")
        logger.debug("Making sure the amount entered is a number.")
        while not isinstance(amount, float):
            try:
                amount = abs(float(amount))
            except ValueError:
                print("Al momento de ingresar el monto, utilice el punto (.) como separador decimal.")
                amount = input(f"¿Cuánto pagó {name.title()}?\nCantidad: $")
            pass
        logger.debug("Call for the 'add_payment' method within the Database object.")
        database.add_payment(name, amount)

    @classmethod
    def history(cls, database: Database) -> None:
        name = input("¿De quién desea conocer las operaciones?\nNombre: ").lower().strip()
        database.show_history(name)
        pass

    @classmethod
    def list_totals(cls, database: Database) -> None:
        database.show_balances()


class MainMenu:
    HELP_STRING = """Los siguientes comandos son válidos. Debe ingresar uno de ellos sin los apóstrofes y luego
presionar la tecla ENTER.

    'd' - para agregar una deuda
    'p' - para agregar un pago
        (Los pagos y deudas se agregan con la fecha actual)
    'l' - para ver la lista de saldos
    'ln' - para ver el historial de operaciones de alguna persona en particular
    'h' - para obtener ayuda
    'q' - para salir del programa."""

    OPERATIONS = {
        'd': Operations.gather_debt,
        'p': Operations.gather_payment,
        'l': Operations.list_totals,
        'ln': Operations.history,
        'h': show_help,
        'q': exit_from_program
    }

    @classmethod
    def loop(cls, database: Database) -> None:
        _ = True
        while _:
            try:
                user_input = input("Ingrese un comando: ").strip().lower()
                to_perform = cls.OPERATIONS[user_input]
            except KeyError:
                print("Ese no es un comando válido, recuerde que los comandos válidos son los que se mostraron al"
                      " inicio del programa. Si desea verlos nuevamente, ingrese el comando 'h', sin apóstrofes. ")
            else:
                to_perform(database)
