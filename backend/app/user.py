from pydantic import BaseModel

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from order import Order



class User(BaseModel):
    username: str
    password: str

class Staff(User):
    staff_id: str

class Student(User):
    student_id: str
    reserved_orders: list[Order]
