from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine


def create_database(database_connection_path):

    DBengine = create_engine(database_connection_path)

    try:
        with DBengine.begin() as connection:
            connection.execute(
                text("CREATE DATABASE IF NOT EXISTS testclone;"))
            connection.commit()
    except SQLAlchemyError as e:
        print(f"Error: {e}")


def create_tables(database_connection_path):

    DBengine = create_engine(database_connection_path)

    with open('create_tables.sql', 'r') as f:
        sql_commands = f.read()

    try:
        with DBengine.begin() as connection:
            for command in sql_commands.split(';'):
                if command.strip():
                    connection.execute(text(command))
            connection.commit()
    except SQLAlchemyError as e:
        print(f"Error: {e}")


if __name__ == '__main__':
    load_dotenv()
    host = os.getenv("DATABASE_HOST")
    password = os.getenv("DATABASE_PASSWORD")
    user = os.getenv("DATABASE_USER")
    port = os.getenv("DATABASE_PORT")
    tag = os.getenv("DATABASE_KEY")
    database_name = os.getenv("DATABASE_NAME")

    create_database(f"{tag}{user}:{password}@{host}:{port}")
    create_tables(f"{tag}{user}:{password}@{host}:{port}/{database_name}")
    print("All the tables and indexes were created sucessfully!")
