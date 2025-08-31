from pydantic import BaseModel
from typing import List, Dict, Union, Optional


class DatabaseReturnValueModel(BaseModel):
    executed: bool
    message: str
    error: str
    data: Optional[Union[List[Dict], bool]]


"""
def get_data() -> DatabaseReturnValueModel:
    return DatabaseReturnValueModel(
        executed=True,
        message="Data updated successfully",
        error="",
        data=[{"id": 1}, {"id": 2}, {"id": 3}]
    )

"""
