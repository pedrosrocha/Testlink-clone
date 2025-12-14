import os
from dotenv import load_dotenv
from sqlalchemy import create_engine


class Config:

    load_dotenv()
    SECRET_KEY = os.getenv("SECRET_KEY")


class DatabaseConfig:

    load_dotenv()
    host = os.getenv("DATABASE_HOST")
    password = os.getenv("DATABASE_PASSWORD")
    user = os.getenv("DATABASE_USER")
    port = os.getenv("DATABASE_PORT")
    tag = os.getenv("DATABASE_KEY")
    database_name = os.getenv("DATABASE_NAME")

    database_connection_path = f"{tag}{user}:{password}@{host}:{port}/{database_name}"
    DBengine = create_engine(database_connection_path)
