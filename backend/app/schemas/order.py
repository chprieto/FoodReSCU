from pydantic import BaseModel, Field
from datetime import datetime
import uuid
from typing import List, Optional
from order import Status


# -------------------------------------------------------------
# Request Schemas (What the client sends to the backend)
# -------------------------------------------------------------

class ReserveOrderRequest(BaseModel):
    """Payload sent by a student when reserving an active order."""
    student_id: str = Field(..., description="The unique ID of the student making the reservation")


class PickupOrderRequest(BaseModel):
    """Payload sent by a student when marking an order as picked up."""
    student_id: str = Field(..., description="The unique ID of the student picking up the order")


class ActivateOrderRequest(BaseModel):
    """Payload sent by staff when activating an upcoming order."""
    staff_id: str = Field(..., description="The unique ID of the staff member activating the order")


class DeleteOrderRequest(BaseModel):
    """Payload sent by staff when deleting an order."""
    staff_id: str = Field(..., description="The unique ID of the staff member deleting the order")


# Aliases for backward compatibility with previous main.py definitions
ReserveRequest = ReserveOrderRequest
ActivateRequest = ActivateOrderRequest
DeleteRequest = DeleteOrderRequest


# -------------------------------------------------------------
# Response Schemas (What the backend returns to the client)
# -------------------------------------------------------------

class OrderResponse(BaseModel):
    """Representation of an order returned to the frontend."""
    order_id: uuid.UUID
    item: str
    status: Status
    time_made: datetime
    time_reserved: Optional[datetime] = None
    reserved_by: Optional[str] = None

    class Config:
        from_attributes = True


class OrderActionResponse(BaseModel):
    """Standard success confirmation for state-change actions."""
    message: str
    order_id: uuid.UUID


class StaffOrdersResponse(BaseModel):
    """Dashboard view of all orders grouped by status for staff."""
    upcoming: List[OrderResponse]
    active: List[OrderResponse]
    reserved: List[OrderResponse]
    picked_up: List[OrderResponse]
    old: List[OrderResponse]


class StudentOrdersResponse(BaseModel):
    """Dashboard view of orders available and relevant to a specific student."""
    available: List[OrderResponse]
    my_reservations: List[OrderResponse]
    my_picked_up: List[OrderResponse]
