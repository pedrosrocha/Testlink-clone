from typing import TypedDict
from datetime import datetime


class UserDict(TypedDict):
    id: int
    username: str
    email: str
    password_hash: str
    date_created: datetime
    user_level: str
