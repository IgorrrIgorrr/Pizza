from datetime import datetime, timedelta
from fastapi import FastAPI, Query, Depends, HTTPException, status, Form, Body
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import JWTError, jwt

from typing_extensions import Annotated
from typing import Union
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, select, insert, delete, ForeignKey

import schemas  # todo why "from . import dont work"
import crud
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES




user_table = Table(
    "users",
    metadata,
    Column("id", Integer, autoincrement=True, primary_key=True),
    Column("username", String),
    Column("full_name", String),
    Column("address", String),
    Column("telephone_number", String),
    Column("email", String),
    Column("hashed_password", String),
)


base_pizzas_table = Table(
    "base_pizzas",
    metadata,
    Column("id", Integer, autoincrement=True, unique=True, primary_key=True),
    Column("name", String),
    Column("price", Integer),
)


ingred_table = Table(
    "ingred",
    metadata,
    Column("id", Integer, autoincrement=True, unique=True, primary_key=True),
    Column("ingredient", String),
    Column("price_gr", Integer),
)


cart_table = Table(
    "cart_for_pizzas",
    metadata,
    Column("id", Integer, autoincrement=True, unique=True, primary_key=True),
    Column("user_id", ForeignKey("users.id")), # TODO MAKE ONE TO MANY
    Column("receipt", ForeignKey("receipt.id")),
    # Column("summa", Integer),
)


receipt_table = Table(
    "receipt",
    metadata,
    Column("id", Integer, autoincrement=True, unique=True, primary_key=True),
    Column("ingredient", String), # todo or list
    Column("price", Integer),
)

orders_table = Table(
    "orders",
    metadata,
    Column("id", Integer, autoincrement=True, unique=True, primary_key=True),
    Column("users_id", Integer, ForeignKey("users.id")),
    Column("state", String),
)

orders_detail_table = Table(
    "orders_detail",
    metadata,
    Column("id", Integer, autoincrement=True, unique=True, primary_key=True),
    Column("orders_id", Integer, ForeignKey("orders.id")),
    Column("receipt_id", Integer, ForeignKey("receipt.id")),
)


metadata.drop_all(engine)           # Чтобы при каждом изменении в моделях таблиц они пересоздавались...
metadata.create_all(engine)

stmt_ingr = insert(ingred_table)
stmt_pizz = insert(base_pizzas_table)
stmt_user = insert(user_table)

with engine.begin() as conn:

    del_stmt1 = delete(ingred_table)        # Чтобы при каждом перезапуске приложения при отладке не заполнялись таблицы по второму разу я их пока что решил чистить...
    del_stmt2 = delete(base_pizzas_table)       # Чтобы при каждом перезапуске приложения при отладке не заполнялись таблицы по второму разу я их пока что решил чистить...
    # del_stmt3 = delete(user_table)
    del_stmt4 = delete(cart_table)
    conn.execute(del_stmt1)
    conn.execute(del_stmt2)
    # conn.execute(del_stmt3)
    conn.execute(del_stmt4)

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
                               {"username": "utest", "full_name": "ftest", "address": "atest", "telephone_number": 1, "email":"etest", "hashed_password": get_password_hash("ptest")}
                           ])

