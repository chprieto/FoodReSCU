import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from user import Student
from enum import Enum


class Status(Enum):
    UPCOMING = 1
    ACTIVE = 2
    RESERVED = 3
    PICKED_UP = 4
    OLD = 5

ACTIVE_TIME = datetime.timedelta(hours = 1)
OLD_TIME = datetime.timedelta(hours = 3)

class Order(BaseModel):
    item: str
    time_made: datetime = datetime.now()
    order_id: str = uuid.uuid4()
    time_reserved: datetime = None
    reservered_by: Student = None
    status: Status = Status.UPCOMING

    def get_time_active(self):
        return datetime.now() - self.time_made

    def activate(self):
        if self.get_time_active() >= ACTIVE_TIME:
            self.status = Status.ACTIVE

    def reserve(self, reserved_by):
        #return ReservedOrder(item=self.item, time_made=self.time_made, reserved_by=reserved_by)
        if self.status == Status.ACTIVE:
            self.status = Status.RESERVED
            self.reservered_by = reserved_by
            self.time_reserved = datetime.now()

    def pick_up(self):
        if self.status == Status.RESERVED:
            self.status = Status.PICKED_UP

    def set_old(self):
        if self.get_time_active() >= OLD_TIME:
            self.status = Status.OLD

class OrderList():
    def __init__(self, expected_status: Status):
        self.order_list = List[Order]
        self.expected_status = expected_status

    def add_order(self, order: Order):
        if self.expected_status == order.status:
            self.order_list.append(order)
    
    def remove_order(self, order: Order):
        self.order_list.remove(order)

    def get_length(self):
        return len(self.order_list)

    


"""class ReservedOrder(Order):
    reserved_by: str

    def unreserve(self):
        return Order(item=self.item, time_made=self.time_made)"""