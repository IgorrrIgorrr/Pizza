from pydantic import BaseModel
from typing import Union


class Ingredients(BaseModel):
    cheese: Union[int, None] = None
    tomato: Union[int, None] = None
    olives: Union[int, None] = None
    onion: Union[int, None] = None
    green: Union[int, None] = None
    sausage: Union[int, None] = None


class PizzaConstr(BaseModel):
    # # type: str = Field(default="Armenian Classic",)# todo how to sent type, size in a body of one BM class???
    # # size: str = Field(default="normal", description="type 'small', 'normal' or 'big'", # todo delete workaround
    #                                examples=["big", "normal", "small"]) # todo make default (medium)
    ingredients: Union[Ingredients, None] = None


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
