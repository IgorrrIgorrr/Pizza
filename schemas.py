from pydantic import BaseModel, Field
from typing import Union


class PizzaConstr(BaseModel):
    cheese: Union[int, None] = None
    tomato: Union[int, None] = None
    olives: Union[int, None] = None
    onion: Union[int, None] = None
    green: Union[int, None] = None
    sausage: Union[int, None] = None
    size: Union[str, None] = Field(default=None, description="type 'small', 'normal' or 'big'",
                                   examples=["big", "normal", "small"]) # todo make default (medium)


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