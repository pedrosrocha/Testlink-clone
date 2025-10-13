import os
from dotenv import load_dotenv
from sqlalchemy import create_engine


class Config:

    load_dotenv()
    SECRET_KEY = os.getenv("SECRET_KEY")


class DatabaseConfig:

    load_dotenv()
    DBengine = create_engine(os.getenv("DATABASE_KEY"))
