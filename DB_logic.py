from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, select, insert, delete

engine = create_engine("sqlite:///./pizzeria_DB.db")

metadata = MetaData()

ingred_table = Table(
    "ingred",
    metadata,
    Column("id", Integer, autoincrement=True, unique=True),
    Column("ingredient", String),
    Column("price/gr", Integer),
)

base_pizzas_table = Table(
    "base_pizzas",
    metadata,
    Column("id", Integer, autoincrement=True, unique=True),
    Column("name", String),
    Column("price", Integer),
)


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
                               {"ingredient": "cheese", "price/gr": 250},
                               {"ingredient": "tomato", "price/gr": 60},
                               {"ingredient": "olives", "price/gr": 115},
                               {"ingredient": "onion", "price/gr": 80},
                               {"ingredient": "green", "price/gr": 90},
                               {"ingredient": "sausage", "price/gr": 200},
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

    # a = conn.execute(select(ingred_table))
    # for i in a:
    #     print(i)

def sum(ingredients):
    with engine.begin() as conn:
        for i in ingredients:
            if ingredients[i] is not None:
                res = conn.execute(select(ingred_table).where(ingred_table.c.ingredient == i))

