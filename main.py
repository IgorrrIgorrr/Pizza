from datetime import datetime, timedelta
from fastapi import FastAPI, Query, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import JWTError, jwt
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
engine = create_engine("sqlite:///./pizzeria_DB.db", echo=True)
metadata = MetaData()


user_table = Table(
    "users",
    metadata,
    Column("id", Integer, autoincrement=True, unique=True, primary_key=True),
    Column("username", String),
    Column("full_name", String),
    Column("address", String),
    Column("telephone_number", String),
    Column("email", String),
    Column("hashed_password", String),
)

ingred_table = Table(
    "ingred",
    metadata,
    Column("id", Integer, autoincrement=True, unique=True, primary_key=True),
    Column("ingredient", String),
    Column("price_gr", Integer),
)

base_pizzas_table = Table(
    "base_pizzas",
    metadata,
    Column("id", Integer, autoincrement=True, unique=True, primary_key=True),
    Column("name", String),
    Column("price", Integer),
)

# metadata.drop_all(engine)           # Чтобы при каждом изменении в моделях таблиц они пересоздавались...
metadata.create_all(engine)

stmt_ingr = insert(ingred_table)
stmt_pizz = insert(base_pizzas_table)
stmt_user = insert(user_table)

with engine.begin() as conn:

    del_stmt1 = delete(ingred_table)        # Чтобы при каждом перезапуске приложения при отладке не заполнялись таблицы по второму разу я их пока что решил чистить...
    del_stmt2 = delete(base_pizzas_table)       # Чтобы при каждом перезапуске приложения при отладке не заполнялись таблицы по второму разу я их пока что решил чистить...
    # del_stmt3 = delete(user_table)
    conn.execute(del_stmt1)
    conn.execute(del_stmt2)
    # conn.execute(del_stmt3)

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

    # c = conn.execute(select(user_table))
    # if not c.all():
    #     use = conn.execute(stmt_user,
    #                        [
    #                            {"username": "utest", "full_name": "ftest", "address": "atest", "telephone_number": 1, "email":"etest", "hashed_password":"TestHashedPassw"}
    #                        ])


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
    username: str
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





def verify_password(plain_password, hashed_password):           #ГОТОВО
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(username: str): #добавлю как-нибудь ошибку при непавльном вводе...         #ГОТОВО
    with engine.begin() as conn:
        a = conn.execute(select(user_table).where(user_table.c.username == username))
        b = a.one()
        return UserInDB(username = b[1], full_name= b[2], address= b[3], telephone_number= b[4], email=b[5], hashed_password=b[6])



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
        token_data = TokenData(username=username)
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


@app.post("/token", response_model= Token)           #ГОТОВО
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


@app.get("/users/me/", response_model=User)         #ГОТОВО
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user)]
):
    return current_user


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



@app.post("/registration")
def registration(username: Annotated[str, Form()], full_name: Annotated[str, Form()], address: Annotated[str, Form()], telephone_number: Annotated[int, Form()], email:Annotated[str, Form()], plain_password:Annotated[str, Form()]):
    hashed_password = get_password_hash(plain_password)
    stmt_user = insert(user_table)
    with engine.begin() as conn:
        use = conn.execute(stmt_user,
                           [
                               {"username": username, "full_name": full_name, "address": address,
                                "telephone_number": telephone_number, "email": email, "hashed_password": hashed_password},
                           ])
        return{"response": "new user successfully created"}



