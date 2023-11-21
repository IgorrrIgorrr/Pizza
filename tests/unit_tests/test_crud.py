import pytest
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, select, ForeignKey, insert, delete
from main_files.crud import get_password_hash, verify_password, get_user
from main_files.config import engine
from main_files.models import user_table, base_pizzas_table, ingred_table, cart_table, receipt_table, orders_table, orders_detail_table
from dotenv import load_dotenv


load_dotenv('.test.env')

metadata_test = MetaData()

for i in [user_table, base_pizzas_table, ingred_table, cart_table, receipt_table, orders_table, orders_detail_table]:
    i.metadata = metadata_test

for i in [user_table, base_pizzas_table, ingred_table, cart_table, receipt_table, orders_table, orders_detail_table]:
    print(i.metadata)



# metadata_test.drop_all(engine)           # Чтобы при каждом изменении в моделях таблиц они пересоздавались...
# metadata_test.create_all(engine)

stmt_ingr = insert(ingred_table)
stmt_pizz = insert(base_pizzas_table)
stmt_user = insert(user_table)

with engine.begin() as conn:

    a = conn.execute(select(ingred_table))
    if not a.all():
        ing = conn.execute(stmt_ingr,
                           [
                               {"ingredient": "cheese", "price_gr": 25},
                               {"ingredient": "tomato", "price_gr": 6},
                               {"ingredient": "olives", "price_gr": 15},
                               {"ingredient": "onion", "price_gr": 8},
                               {"ingredient": "green", "price_gr": 9},
                               {"ingredient": "sausage", "price_gr": 20},
                               {"ingredient": "small", "price_gr": 1000}, # todo remove sizes from ingredient table (it's just a workaround)
                               {"ingredient": "normal", "price_gr": 1500},
                               {"ingredient": "big", "price_gr": 2000},
                           ])

    b = conn.execute(select(base_pizzas_table))
    if not b.all():
        pizz = conn.execute(stmt_pizz,
                            [
                                {"name": "Neapolitan", "price": 1500},
                                {"name": "Pepperoni", "price": 1700},
                                {"name": "Armenian Classic", "price": 1300},
                                {"name": "Margarita", "price": 1600},
                                {"name": "For seasons", "price": 1650},
                            ])

    c = conn.execute(select(user_table))
    if not c.all():
        use = conn.execute(stmt_user,
                           [
                               {"username": "utest", "full_name": "ftest", "address": "atest", "telephone_number": 1, "email":"etest", "hashed_password": "$2b$12$ifvFi0DIKrhWggaRLizWZ.yaEjvbyq3eZeuMU8lgs.dqSuu.m5NUW"}
                           ])


def test_verify_password():
    x = "a"
    res = get_password_hash(x)
    assert verify_password(x, res) is True


def check_for_username_existence(username: str):
    with engine.begin() as conn:
        a = conn.execute(select(user_table).where(user_table.c.username == username))
        return a.scalar()







