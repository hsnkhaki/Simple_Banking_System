import os
from random import random, randrange
import sqlite3

menu_home = """
1. Create an account
2. Log into account
0. Exit
"""

menu_login_user = """
Enter your card number:
"""

menu_login_pin = """
Enter your PIN:
"""

menu_wrong_login = "Wrong card number or PIN!"

menu_home_user = """
1. Balance
2. Add income
3. Do transfer
4. Close account
5. Log out
0. Exit
"""


class ConnectionMySQL:
    def __init__(self, db_name):
        self.connection = sqlite3.connect(db_name)

    def execute_query(self, query):
        cursor = self.connection.cursor()
        try:
            cursor.execute(query)
            self.connection.commit()
            # print("Query executed successfully")
        except sqlite3.Error as e:
            print(f"The error '{e}' occurred")

    def execute_read_query(self, query):
        cursor = self.connection.cursor()
        result = None
        try:
            cursor.execute(query)
            result = cursor.fetchall()
            return result
        except sqlite3.Error as e:
            print(f"The error '{e}' occurred")
            return result


def luhn_algorithm(card15):
    card15 = list(card15)
    card15 = [int(c) * 2 if i % 2 == 0 else int(c) for i, c in enumerate(card15)]
    cs = sum([c if c <= 9 else c - 9 for c in card15]) % 10
    if cs == 0:
        return '0'
    else:
        return str(10 - cs)


def generate_visa_card(conn):
    card_number = f'4000004{randrange(00000000, 99999999):08d}'
    card_number += luhn_algorithm(card_number)
    card_pin = f'{randrange(0000, 9999):04d}'
    print(f"""
Your card has been created
Your card number:
{card_number}
Your card PIN:
{card_pin}
    """)
    insert_query = f"""
            INSERT INTO 
                card(number, pin) 
            VALUES 
                ('{card_number}', '{card_pin}');
            """
    conn.execute_query(insert_query)
    return 1


def get_visa_card(conn, card_number, pin):
    get_card_query = f"""
    SELECT
        number,
        pin,
        balance
    FROM
        card
    WHERE
        number = '{card_number}' AND pin = '{pin}';
                    """

    result = conn.execute_read_query(get_card_query)
    if result:
        number, pin_number, balance = result[0]
    else:
        number, pin_number, balance = None, None, 0
    return number == card_number and pin_number == pin, balance


def main():
    sql_data = 'card.s3db'
    conn = ConnectionMySQL(sql_data)
    query_create_table = """
        CREATE TABLE IF NOT EXISTS card(
            id      INTEGER,
            number  TEXT,
            pin     TEXT,
            balance INTEGER DEFAULT 0
        );
        """
    conn.execute_query(query_create_table)

    menu = menu_home
    cards = {}
    while True:
        selection = input(menu)
        if selection == '0':
            print('Bye!')
            break
        if menu == menu_home:
            if selection == '1':  # creat an account
                card = generate_visa_card(conn)
                continue
            elif selection == '2':  # log into account
                card_number = input(menu_login_user)
                card_pin = input(menu_login_pin)
                login_success, balance = get_visa_card(conn, card_number, card_pin)
                if login_success:
                    print('You have successfully logged in!')
                    menu = menu_home_user
                    continue
                else:
                    print(menu_wrong_login)
                    menu = menu_home
                    continue
        elif menu == menu_home_user:
            if selection == '1':
                print(f'Balance: {balance}')
            elif selection == '2':  # Add income
                income = int(input('Enter income:'))
                update_income_query = f"""
                UPDATE
                    card
                SET
                    balance = '{balance + income}'
                WHERE
                    number = '{card_number}'
                """
                conn.execute_query(update_income_query)
                balance += income
                print('Income was added!')
            elif selection == '3':  # Do transfer
                print("Transfer")
                to_card_number = input("Enter card number:")
                if to_card_number[-1] != luhn_algorithm(to_card_number[:-1]):
                    print('Probably you made a mistake in the card number. Please try again!')
                    continue
                if to_card_number == card_number:
                    print("You can't transfer money to the same account!")
                    continue
                to_card_query = f"""
                SELECT
                    balance
                FROM
                    card
                WHERE
                    number = '{to_card_number}'
                """
                result = conn.execute_read_query(to_card_query)
                if result:
                    send_amount = int(input('Enter how much money you want to transfer:'))
                    if send_amount > balance:
                        print('Not enough money!')
                        continue
                    else:
                        sender_balance = balance - send_amount
                        receiver_balance = result[0][0] + send_amount
                        update_sender_balance_query = f"""
                            UPDATE
                                card
                            SET
                                balance = '{sender_balance}'
                            WHERE
                                number = '{card_number}'
                            """
                        update_receiver_balance_query = f"""
                            UPDATE
                                card
                            SET
                                balance = '{receiver_balance}'
                            WHERE
                                number = '{to_card_number}'
                            """
                        conn.execute_query(update_sender_balance_query)
                        conn.execute_query(update_receiver_balance_query)
                        print('Success!')
                else:
                    print("Such a card does not exist.")
                    continue
            elif selection == '4':  # Close account
                delete_account_query = f"""
                DELETE FROM
                    card
                WHERE
                    number = '{card_number}'
                """
                conn.execute_query(delete_account_query)

            elif selection == '5':  # log into account
                print("You have successfully logged out!")
                menu = menu_home
                continue


if __name__ == '__main__':
    main()
