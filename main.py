from datetime import datetime, timedelta
from fastapi import FastAPI, Query, Depends, HTTPException, status, Form, Body
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import JWTError, jwt

from typing_extensions import Annotated
from typing import Union
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, select, insert, delete, ForeignKey

import schemas  #todo why "from . import dont work"



# todo put every theme to different files schemas, models...
SECRET_KEY = "b3ee86aeb59bcaf62a3f9626a5d0c0055a7dc5d29fd25195ff6af6710a51de63"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI(title="Pizza APP", description="App service for pizzerias")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
engine = create_engine("sqlite:///./pizzeria_DB.db") #todo можно вставить echo=True
metadata = MetaData()



def get_password_hash(password):
    return pwd_context.hash(password)


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


def suum(ingredients: Annotated[schemas.PizzaConstr, Depends(schemas.PizzaConstr)],
         type: Annotated[str, Body()] ="Armenian Classic", size: Annotated[str, Body()] = "normal"):
    with engine.begin() as conn:
        a = 0
        res = conn.execute(select(base_pizzas_table.c.price).where(base_pizzas_table.c.name == type))
        a = a + int(res.scalar())
        for k, v in ingredients.ingredients.model_dump(exclude_defaults=True).items():
            res = conn.execute(select(ingred_table.c.price_gr).where(ingred_table.c.ingredient == str(k)))
            a = (a + int(res.scalar())*v)
        if size == "small":
            a += 1000
        elif size == "normal":
            a += 1500
        elif size == "big":
            a += 2000
        b = {"a": a, "ing": list(ingredients.ingredients.model_dump(exclude_defaults=True).items())}
        # print("--------------------", b["ing"])
        return b





def verify_password(plain_password, hashed_password):           #ГОТОВО
    return pwd_context.verify(plain_password, hashed_password)





def get_user(username: str): #добавлю как-нибудь ошибку при непавльном вводе...         #ГОТОВО
    with engine.begin() as conn:
        a = conn.execute(select(user_table).where(user_table.c.username == username))
        b = a.one() # todo correct mapping
        return schemas.UserInDB(username = b[1], full_name= b[2], address= b[3], telephone_number= b[4], email=b[5], hashed_password=b[6])


def check_for_username_existence(username: str):
    with engine.begin() as conn:
        a = conn.execute(select(user_table).where(user_table.c.username == username))
        if a.one():
            return True
        else:
            return False



def authenticate_user(username: str, password: str):            #ГОТОВО
    user = get_user(username)
    print(user.hashed_password)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Union[timedelta, None]):         #ГОТОВО
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):          #ГОТОВО
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


# async def get_current_active_user(
#     current_user: Annotated[User, Depends(get_current_user)]
# ):
#     if current_user.disabled:
#         raise HTTPException(status_code=400, detail="Inactive user")
#     return current_user



@app.get("/test")
def a(fullname: str, b = Depends(authenticate_user)):
    return b


@app.post("/token", response_model= schemas.Token)           #ГОТОВО
async def login_for_access_token(
            form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me/", response_model=schemas.User)         #ГОТОВО
async def read_users_me(
    current_user: Annotated[schemas.User, Depends(get_current_user)]
):
    return current_user


@app.post("/cart/pizza", tags=["Choose pizza"])
def pizza_making(number: Annotated[dict, Depends(suum)], user: Annotated[schemas.UserInDB, Depends(read_users_me)]):
    with engine.begin() as conn:
        res = conn.execute(insert(receipt_table).values(ingredient = str(number["ing"]), price = number["a"]))
        res_p_key = res.inserted_primary_key[0]
        us_id = conn.execute(select(user_table.c.id).where(user_table.c.username == user.username))
        us_id_scal = us_id.scalar()
        res2 = conn.execute(insert(cart_table).values(user_id = us_id_scal, receipt = res_p_key))
        res4 = conn.execute(insert(orders_table).values(users_id=us_id_scal, state = "haven't started cooking yet"))
        res4_p_key = res4.inserted_primary_key[0]
        res3 = conn.execute(insert(orders_detail_table).values(receipt_id = res_p_key, orders_id = res4_p_key))

    return {"response": "pizza successfully chosen"}


@app.get("/", tags=["Starting page"])
def greeting():
    return {"greeting": "Hello our dear customer!!!"}



@app.post("/registration") #    ДОБАВИТЬ ОШИБКУ, ЕСЛИ ЕСТЬ УЖЕ ТАКОЙ ПОЛЬЗОВАТЕЛЬ!!!!
def registration(username: Annotated[str, Form()], full_name: Annotated[str, Form()], address: Annotated[str, Form()], telephone_number: Annotated[int, Form()], email:Annotated[str, Form()], plain_password:Annotated[str, Form()]):
    if not check_for_username_existence(username):
        hashed_password = get_password_hash(plain_password)
        stmt_user = insert(user_table)
        with engine.begin() as conn:
            use = conn.execute(stmt_user,
                               [
                                   {"username": username, "full_name": full_name, "address": address,
                                    "telephone_number": telephone_number, "email": email, "hashed_password": hashed_password},
                               ])
            return{"response": "new user successfully created"}



