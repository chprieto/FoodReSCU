from __future__ import annotations
from pydantic import BaseModel
import uuid



class User(BaseModel):
    username: str
    password: str

class Staff(User):
    staff_id: str

class Student(User):
    student_id: str
    reserved_orders: list[uuid.UUID] = []
