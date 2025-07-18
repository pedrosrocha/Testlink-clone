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

with engine.connect() as connection:
    connection.execute(text("""

    CREATE TABLE projects (
        id INT AUTO_INCREMENT PRIMARY KEY,
        
        name VARCHAR(100) NOT NULL UNIQUE,              -- Name of the project
        description TEXT,                               -- Optional longer description
        status ENUM('active', 'inactive', 'archived') DEFAULT 'active',  -- Status of project

        owner_name VARCHAR(100),                        -- Optional link to user who owns the project
        start_date DATE,                                -- When the project started
        end_date DATE,                                  -- Optional planned end date

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,             -- Timestamp for creation
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP  -- Auto update on modification
    );
        """))
    connection.commit()
