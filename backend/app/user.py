from pydantic import BaseModel

class User(BaseModel):
    def __init__(self, name):
        self.name = name

class Staff(User):
    def __init(self, name, staff_id):
        super.__init(name)
        self.staff_id = staff_id

class Student(User):
    def __init(self, name, student_id):
        super.__init(name)
        self.student_id = student_id