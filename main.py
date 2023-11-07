from datetime import timedelta
from fastapi import FastAPI, Depends, HTTPException, status, Form, Request
from fastapi.security import OAuth2PasswordRequestForm
from typing_extensions import Annotated
from sqlalchemy import select, insert, delete, update

from config import ACCESS_TOKEN_EXPIRE_MINUTES, engine
from models import cart_table, user_table, receipt_table, orders_table, orders_detail_table
from crud import get_password_hash, check_for_username_existence, authenticate_user, create_access_token, get_current_user, suum
from schemas import Token, User, UserInDB
# todo put every theme to different files schemas, models...

app = FastAPI(title="Pizza APP", description="App service for pizzerias")

@app.post("/token", response_model= Token)
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


@app.get("/users/me/", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user)]
):
    return current_user


@app.post("/cart/pizza", tags=["Choose pizza"])
def pizza_making(number: Annotated[dict, Depends(suum)], user: Annotated[UserInDB, Depends(read_users_me)]):
    with engine.begin() as conn:
        rec_ins = conn.execute(insert(receipt_table).values(ingredient = str(number["ing"]), price = number["a"]))
        rec_p_key = rec_ins.inserted_primary_key[0]
        us_id_sel = conn.execute(select(user_table.c.id).where(user_table.c.username == user.username))
        us_id_sel_scal = us_id_sel.scalar()
        cart_ins = conn.execute(insert(cart_table).values(user_id = us_id_sel_scal, receipt = rec_p_key))
        cart_ins_p_key = cart_ins.inserted_primary_key[0]
        ord_ins = conn.execute(insert(orders_table).values(users_id=us_id_sel_scal, state = "haven't started cooking yet"))
        ord_p_key = ord_ins.inserted_primary_key[0]
        ord_det_ins = conn.execute(insert(orders_detail_table).values(receipt_id = rec_p_key, orders_id = ord_p_key))

    return {"response": "pizza successfully chosen", "pizzas_id": cart_ins_p_key }


@app.get("/", tags=["Starting page"])
def greeting():
    return {"greeting": "Hello our dear customer!!!"}



@app.post("/registration") #todo    ДОБАВИТЬ ОШИБКУ, ЕСЛИ ЕСТЬ УЖЕ ТАКОЙ ПОЛЬЗОВАТЕЛЬ!!!!
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


@app.delete("/cart/{id}") #todo make error, while trying to delete pizza twice
def delete_pizza_from_cart(id:int):
    with engine.begin() as conn:
        res = conn.execute(delete(cart_table).where(cart_table.c.id == id))
        return {"answer": "This pizza was successfully deleted"}


@app.post("/cart/ready", dependencies=[Depends(get_current_user)])
def finished_choosing(request: Request):
    username = request.state.user.username
    with engine.begin() as conn:
        find_user_id=conn.execute(select(user_table.c.id).where(user_table.c.username == str(username)))
        a = find_user_id.scalar()
        baking = conn.execute(update(orders_table).where(orders_table.c.users_id == int(a)).values(state = "started baking"))
        b = conn.execute(select(orders_table.c.id).where(orders_table.c.users_id == int(a)))
        making_cart_empty = conn.execute(delete(cart_table).where(cart_table.c.user_id == int(a)))
    return {"response": "We started baking your pizzas", "your_orders_id": b.scalar()}


@app.get("/orders/{id}")
def check_orders_status(id: int):
    with engine.begin() as conn:
        a = conn.execute(select(orders_table.c.state).where(orders_table.c.users_id == int(id)))
        return {"status_of_order":a.scalar()}