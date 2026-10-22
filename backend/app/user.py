from pydantic import BaseModel
from order import ReservedOrder

class User(BaseModel):
    username: str
    password: str

class Staff(User):
    staff_id: str

class Student(User):
    student_id: str
    reserved_orders: list[ReservedOrder]
