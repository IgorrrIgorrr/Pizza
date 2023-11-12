from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status, Body, Request
from jose import JWTError, jwt
from typing_extensions import Annotated
from typing import Union
from sqlalchemy import select, exists

from schemas import PizzaConstr, UserInDB, TokenData
from models import user_table, base_pizzas_table, ingred_table
from config import SECRET_KEY, ALGORITHM, pwd_context, engine, oauth2_scheme


def get_password_hash(password):
    return pwd_context.hash(password)


def suum(ingredients: Annotated[PizzaConstr, Depends(PizzaConstr)],
         type: Annotated[str, Body()] = "Armenian Classic", size: Annotated[str, Body()] = "normal"):
    with engine.begin() as conn:
        acum = 0
        res = conn.execute(select(base_pizzas_table.c.price).where(base_pizzas_table.c.name == type))
        acum = acum + int(res.scalar())
        for k, v in ingredients.ingredients.model_dump(exclude_defaults=True).items():
            res = conn.execute(select(ingred_table.c.price_gr).where(ingred_table.c.ingredient == str(k)))
            acum = (acum + int(res.scalar()) * v)
        if size == "small":
            acum += 1000
        elif size == "normal":
            acum += 1500
        elif size == "big":
            acum += 2000
        b = {"price": acum, "ingred": list(ingredients.ingredients.model_dump(exclude_defaults=True).items())}
        return b


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_user(username: str):  # todo add exception while wrong credentials ...
    with engine.begin() as conn:
        a = conn.execute(select(user_table).where(user_table.c.username == username))
        b = a.one()  # todo correct mapping
        return UserInDB(id = b[0], username=b[1], full_name=b[2], address=b[3], telephone_number=b[4], email=b[5],
                        hashed_password=b[6])


def check_for_username_existence(username: str):
    with engine.begin() as conn:
        a = conn.execute(select(user_table).where(user_table.c.username == username))
        return a.scalar()


def authenticate_user(username: str, password: str):
    user = get_user(username)
    print(user.hashed_password)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Union[timedelta, None]):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], request: Request):
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
    request.state.user = user
    return user
