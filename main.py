from fastapi import FastAPI, Query, Depends
from typing import List
from pydantic import BaseModel, Field
from typing_extensions import Annotated
from typing import Union

from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, select, insert, delete


app = FastAPI( title="Pizza APP", description="App service for pizzerias")


engine = create_engine("sqlite:///./pizzeria_DB.db")

metadata = MetaData()

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

metadata.drop_all(engine)
metadata.create_all(engine)

stmt_ingr = insert(ingred_table)
stmt_pizz = insert(base_pizzas_table)

with engine.begin() as conn:

    del_stmt1 = delete(ingred_table)
    del_stmt2 = delete(base_pizzas_table)
    conn.execute(del_stmt1)
    conn.execute(del_stmt2)

    a =  conn.execute(select(ingred_table))
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


class PizzaConstr(BaseModel):
    cheese: Union[int, None] = None
    tomato: Union[int, None] = None
    olives: Union[int, None] = None
    onion: Union[int, None] = None
    green: Union[int, None] = None
    sausage: Union[int, None] = None
    size: Union[str, None] = Field(default=None, description="type 'small', 'normal' or 'big'", examples=["big", "normal", "small"])


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


@app.post("/construct")
def get_suum(number: Annotated[int, Depends(suum)]):
    return number

