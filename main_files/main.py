from datetime import timedelta
from fastapi import FastAPI, Depends, HTTPException, status, Form, Request
from fastapi.security import OAuth2PasswordRequestForm
from typing_extensions import Annotated
from sqlalchemy import select, insert, delete, update, and_, func

from config import ACCESS_TOKEN_EXPIRE_MINUTES, engine
from models import cart_table, user_table, receipt_table, orders_table, orders_detail_table
from crud import get_password_hash, check_for_username_existence, authenticate_user, create_access_token, get_current_user, suum
from schemas import Token, User, UserInDB

# todo to implement new column in user table for pizzeria employees and additional fild for accepting rmployee with director, to preven registrstion customer as employee...


app = FastAPI(title="Pizza APP", description="App service for pizzerias")


@app.get("/", tags=["Starting page"])
def greeting():
    return {"greeting": "Hello our dear customer!!!"}


@app.post("/token", response_model= Token, tags=["Service handlers"])
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


@app.get("/users/me/", response_model=User, tags=["Service handlers"]) # todo maby get rid of it??
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user)]
):
    return current_user


@app.post("/registration", tags=["Customer handlers"]) # todo  add error if such user exists
def registration(username: Annotated[str, Form()], full_name: Annotated[str, Form()], address: Annotated[str, Form()], telephone_number: Annotated[int, Form()], email:Annotated[str, Form()], plain_password:Annotated[str, Form()]):
    # print("iiiiiiiiiiiiiiiiiiiiiiiiiii", check_for_username_existence(username))
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
    else:
        return {"response": "such username already exists"}


@app.post("/cart/pizza", tags=["Customer handlers"])
def pizza_choosing(pizza_info: Annotated[dict, Depends(suum)], user: Annotated[UserInDB, Depends(read_users_me)]):
    with engine.begin() as conn:
        rec_ins = conn.execute(insert(receipt_table).values(ingredient = str(pizza_info["ingred"]), price = pizza_info["price"]))
        rec_p_key = rec_ins.inserted_primary_key[0]
        us_id_sel = conn.execute(select(user_table.c.id).where(user_table.c.username == user.username))
        us_id_sel_scal = us_id_sel.scalar()
        cart_ins = conn.execute(insert(cart_table).values(user_id = us_id_sel_scal, receipt = rec_p_key))
        cart_ins_p_key = cart_ins.inserted_primary_key[0]
        user_orders = conn.execute(select(orders_table).where(and_(orders_table.c.users_id == us_id_sel_scal), (orders_table.c.state == "in process of choosing, not ordered yet")))
        a = user_orders.all()
        if not a:
            ord_ins = conn.execute(insert(orders_table).values(users_id=us_id_sel_scal, state = "in process of choosing, not ordered yet"))
            ord_p_key = ord_ins.inserted_primary_key[0]
        user_orders = conn.execute(select(orders_table.c.id).where(and_(orders_table.c.users_id == us_id_sel_scal), (orders_table.c.state == "in process of choosing, not ordered yet")))
        b = user_orders.scalar()
        ord_det_ins = conn.execute(insert(orders_detail_table).values(receipt_id = rec_p_key, orders_id = b))
    return {"response": "Pizza successfully chosen", "pizzas id": cart_ins_p_key}


@app.delete("/cart/{id}", tags=["Customer handlers"]) # todo make error, while trying to delete pizza twice
def delete_pizza_from_cart(id: int, user: Annotated[UserInDB, Depends(read_users_me)]):
    with engine.begin() as conn:
        receipt_id = conn.execute(select(cart_table.c.receipt).where(cart_table.c.id == id)).scalar()
        orders_detail_id = conn.execute(select(orders_detail_table.c.id).where(orders_detail_table.c.receipt_id == int(receipt_id))).scalar()
        cart_del = conn.execute(delete(cart_table).where(cart_table.c.id == id))
        rec_del = conn.execute(delete(receipt_table).where(receipt_table.c.id == int(receipt_id)))
        ord_det_del = conn.execute(delete(orders_detail_table).where(orders_detail_table.c.id ==int(receipt_id)))
        abc = conn.execute(select(func.count()).select_from(cart_table)).scalar()
        if abc == 0:
            aaa = conn.execute(delete(orders_table).where(and_(orders_table.c.users_id==user.id),(orders_table.c.state == "in process of choosing, not ordered yet")))
        return {"answer": "This pizza was successfully deleted"}


@app.post("/cart/ready", dependencies=[Depends(get_current_user)], tags=["Customer handlers"])  # todo make pizzas add to order only after confirminig, or not
def finished_choosing(request: Request):
    username = request.state.user.username
    id = request.state.user.id
    with engine.begin() as conn:
        a = conn.execute(update(orders_table).where(and_(orders_table.c.users_id == id, orders_table.c.state == "in process of choosing, not ordered yet")).values(state = "ordered"))
        order_id = conn.execute(select(orders_table.c.id).where(and_(orders_table.c.users_id == id), (orders_table.c.state == "ordered"))).scalar()
        making_cart_empty = conn.execute(delete(cart_table).where(cart_table.c.user_id == int(id)))
    return {"response": "We have received your order", "your_orders_id": order_id}


@app.get("/orders/{id}", tags=["Customer handlers"])
def check_orders_status_for_user_id(id: int):
    with engine.begin() as conn:
        a = conn.execute(select(orders_table.c.state).where(orders_table.c.users_id == int(id))) # todo maby change id of customer on id of order???
        return {"status_of_order":a.scalar()}


@app.get("/pizzamaster/receipt", tags=["Pizza-master actions"])
def look_at_receipt(id:int):
    with engine.begin() as conn:
        a = conn.execute(select(receipt_table.c.ingredient).where(receipt_table.c.id == int(id))).scalar()
        return {"receipt": a}


@app.post("/pizzamaster/baking/{id}", tags=["Pizza-master actions"])  # todo change status only of first position in orders and make couple statuses, not only ready(begin baking for ec)
def change_order_status_on_baking(id: int):

    with engine.begin() as conn:
        a = conn.execute(update(orders_table).where(orders_table.c.id == int(id)).values(state = "Your order is baking"))
    return{"status": "status changed"}


@app.post("/pizzamaster/ready/{id}", tags=["Pizza-master actions"])  # todo change status only of first position in orders and make couple statuses, not only ready(begin baking for ec)
def change_order_status_on_ready(id: int):

    with engine.begin() as conn:
        a = conn.execute(update(orders_table).where(orders_table.c.id == int(id)).values(state = "Your order is ready! Come take it!"))
    return{"status": "status changed"}


@app.post("/pizzamaster/taken/{id}", tags=["Pizza-master actions"])
def customer_have_taken_order(id:int):
    with engine.begin() as conn:
        a = conn.execute(update(orders_table).where(orders_table.c.id == int(id)).values(state = "order was taken"))
    return {"response":"order was taken"}

