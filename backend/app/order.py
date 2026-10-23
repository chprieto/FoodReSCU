import uuid
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from enum import Enum

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from user import Student



class Status(str, Enum):
    UPCOMING = "UPCOMING"
    ACTIVE = "ACTIVE"
    RESERVED = "RESERVED"
    PICKED_UP = "PICKED_UP"
    OLD = "OLD"

ACTIVE_TIME = timedelta(hours = 1)
OLD_TIME = timedelta(hours = 3)

class Order(BaseModel):
    item: str
    time_made: datetime = Field(default_factory=datetime.now)
    order_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    time_reserved: datetime | None = None
    reserved_by: Student | None  = None
    status: Status = Status.UPCOMING

    def get_time_active(self):
        return datetime.now() - self.time_made

    def activate(self):
        if self.status == Status.UPCOMING and self.get_time_active() >= ACTIVE_TIME:
            self.status = Status.ACTIVE

    def reserve(self, reserved_by: Student):
        #return ReservedOrder(item=self.item, time_made=self.time_made, reserved_by=reserved_by)
        if self.status == Status.ACTIVE:
            self.status = Status.RESERVED
            self.reserved_by = reserved_by
            self.time_reserved = datetime.now()

    def pick_up(self):
        if self.status == Status.RESERVED:
            self.status = Status.PICKED_UP

    def set_old(self):
        if self.status != Status.PICKED_UP and self.get_time_active() >= OLD_TIME:
            self.status = Status.OLD


class OrderList():
    def __init__(self, expected_status: Status):
        self.order_list: list[Order] = []
        self.expected_status = expected_status

    def add_order(self, order: Order):
        if self.expected_status == order.status:
            self.order_list.append(order)
    
    def remove_order(self, order: Order):
        if order in self.order_list:
            self.order_list.remove(order)
            return order
        
        # will need more error checking code here in the future, for notifying frontend removal has failed
        return None

    def get_length(self):
        return len(self.order_list)

    


"""class ReservedOrder(Order):
    reserved_by: str

    def unreserve(self):
        return Order(item=self.item, time_made=self.time_made)"""