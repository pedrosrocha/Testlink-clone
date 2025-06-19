from sqlalchemy import create_engine, text


# Format: mysql+pymysql://<username>:<password>@<host>/
# ( becomes %28
# ) becomes %29
engine = create_engine(
    "mysql+pymysql://UserPython:root%2812345%29@localhost/testlinkclone")

with engine.connect() as connection:
    connection.execute(text("""
        CREATE TABLE users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            email VARCHAR(100) NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            date_created DATETIME DEFAULT CURRENT_TIMESTAMP,
            user_level ENUM('admin', 'editor', 'viewer') DEFAULT 'viewer',
            is_active BOOLEAN DEFAULT TRUE,
            last_login DATETIME DEFAULT NULL
        );
        """))
    connection.commit()
