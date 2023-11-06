from datetime import datetime, timedelta
from fastapi import FastAPI, Query, Depends, HTTPException, status, Form, Body
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import JWTError, jwt

from typing_extensions import Annotated
from typing import Union
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, select, insert, delete, ForeignKey

import schemas  # todo why "from . import dont work"
import crud
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES



SECRET_KEY = "b3ee86aeb59bcaf62a3f9626a5d0c0055a7dc5d29fd25195ff6af6710a51de63"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30