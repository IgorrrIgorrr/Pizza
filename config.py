from fastapi import FastAPI
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy import create_engine, MetaData


SECRET_KEY = "b3ee86aeb59bcaf62a3f9626a5d0c0055a7dc5d29fd25195ff6af6710a51de63"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI(title="Pizza APP", description="App service for pizzerias")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

engine = create_engine("sqlite:///./pizzeria_DB.db") #todo можно вставить echo=True
metadata = MetaData()

