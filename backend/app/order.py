from datetime import datetime
from pydantic import BaseModel, Field

class Order(BaseModel):
    item: str
    time_made: datetime = Field(default_factory=datetime.now)

    def reserve(self, reserved_by):
        return ReservedOrder(item=self.item, time_made=self.time_made, reserved_by=reserved_by)

class ReservedOrder(Order):
    reserved_by: str

    def unreserve(self):
        return Order(item=self.item, time_made=self.time_made)

