from datetime import datetime, timedelta
from fastapi import FastAPI, Query, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import JWTError, jwt
from typing import List
from pydantic import BaseModel, Field
from typing_extensions import Annotated
from typing import Union
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, select, insert, delete


SECRET_KEY = "b3ee86aeb59bcaf62a3f9626a5d0c0055a7dc5d29fd25195ff6af6710a51de63"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI(title="Pizza APP", description="App service for pizzerias")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
engine = create_engine("sqlite:///./pizzeria_DB.db")
metadata = MetaData()


user_table = Table(
    "users",
    metadata,
    Column("id", Integer, autoincrement=True, unique=True),
    Column("name", String),
    Column("full_name", String),
    Column("address", String),
    Column("telephone_number", String),
    Column("email", String),
    Column("hashed_password", String),
)

ingred_table = Table(
    "ingred",
    metadata,
    Column("id", Integer, autoincrement=True, unique=True),
    Column("ingredient", String),
    Column("price_gr", Integer),
)

base_pizzas_table = Table(
    "base_pizzas",
    metadata,
    Column("id", Integer, autoincrement=True, unique=True),
    Column("name", String),
    Column("price", Integer),
)

metadata.drop_all(engine)           # Чтобы при каждом изменении в моделях таблиц они пересоздавались...
metadata.create_all(engine)

stmt_ingr = insert(ingred_table)
stmt_pizz = insert(base_pizzas_table)
stmt_user = insert(user_table)

with engine.begin() as conn:

    del_stmt1 = delete(ingred_table)        # Чтобы при каждом перезапуске приложения при отладке не заполнялись таблицы по второму разу я их пока что решил чистить...
    del_stmt2 = delete(base_pizzas_table)       # Чтобы при каждом перезапуске приложения при отладке не заполнялись таблицы по второму разу я их пока что решил чистить...
    del_stmt3 = delete(user_table)
    conn.execute(del_stmt1)
    conn.execute(del_stmt2)
    conn.execute(del_stmt3)

    a = conn.execute(select(ingred_table))
    if not a.all():
        ing = conn.execute(stmt_ingr,
                           [
                               {"ingredient": "cheese", "price_gr": 250},
                               {"ingredient": "tomato", "price_gr": 60},
                               {"ingredient": "olives", "price_gr": 115},
                               {"ingredient": "onion", "price_gr": 80},
                               {"ingredient": "green", "price_gr": 90},
                               {"ingredient": "sausage", "price_gr": 200},
                               {"ingredient": "small", "price_gr": 1000},
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
                               {"id": 123, "name": "TestName", "full_name": "TestFullName", "address": "Test address", "telephone_number": 8984984984, "email":"TestEmail", "hashed_password":"TestHashedPassw"}
                           ])


class PizzaConstr(BaseModel):
    cheese: Union[int, None] = None
    tomato: Union[int, None] = None
    olives: Union[int, None] = None
    onion: Union[int, None] = None
    green: Union[int, None] = None
    sausage: Union[int, None] = None
    size: Union[str, None] = Field(default=None, description="type 'small', 'normal' or 'big'",
                                   examples=["big", "normal", "small"])


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str


class User(BaseModel):
    id: Union[int, None] = None
    name: str
    full_name: str
    address: str
    telephone_number: str
    email: Union[str, None] = None


class UserInDB(User):
    hashed_password: str



def suum(ingredients: Annotated[PizzaConstr, Depends(PizzaConstr)]):
    with engine.begin() as conn:
        a = 0
        for k, v in ingredients.model_dump(exclude_defaults=True).items():
            print(k, v)
            res = conn.execute(select(ingred_table.c.price_gr).where(ingred_table.c.ingredient == str(k)))
            if v == "small":
                a += 1000
            elif v == "normal":
                a += 1500
            elif v == "big":
                a += 2000
            else:
                a = (a + int(res.scalar())*v)
        return a


@app.post("/construct", tags=["Choose pizza"])
def get_suum(number: Annotated[int, Depends(suum)]):
    return {"price of cunstructed pizza": number}


@app.get("/ready", tags=["Choose pizza"])
def get_base_pizza(choice: str):
    with engine.begin() as conn:
        res = conn.execute(select(base_pizzas_table.c.price).where(base_pizzas_table.c.name == choice))
        a =  res.scalar()
    return {"price of base pizza": a}


@app.get("/", tags=["Starting page"])
def greeting():
    return {"greeting": "Hello our dear customer!!!"}


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(fullname: str):
    with engine.connect() as conn:
        a = conn.execute(select(user_table).where(user_table.c.full_name == fullname))
        print(fullname)
        if a.all():
            print(a.mappings().all())
            print("----------------------------------------------------")
            print("a", a.fetchmany())
            print()
            print("KEYS!!!!", a.keys())
            print()
            print("MAPPINGS!!!", a.mappings().all())
            print()
            print("SCALAR!!!", a.scalar())
            print("----------------------------------------------------")
            return a.all()
        else:
            return {"answer": "no such user"}

@app.get("/test")
def a(fullname:str, b = Depends(get_user)):
    return b







