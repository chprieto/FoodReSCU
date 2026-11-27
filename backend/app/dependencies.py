from datetime import datetime, timedelta
from system import System
from order import Order, Status

# Global in-memory singleton instance of the System
system = System()

# Seed test data for development and testing
student = system.add_student("student1", "password123", "STU001")
system.add_student("student2", "password456", "STU002")
staff = system.add_staff("staff1", "staff123", "STAFF001")

system.incoming_order("Burger")
system.incoming_order("Pizza")

# Already-claimable orders (made 70 min ago) so students have something to reserve while testing
for item in ("Pasta", "Salad", "Sandwich"):
    system.active_list.add_order(
        Order(item=item, status=Status.ACTIVE, time_made=datetime.now() - timedelta(minutes=70))
    )
for item in ("Soup", "Rice"):
    system.upcoming_list.add_order(
        Order(item=item, status=Status.UPCOMING, time_made=datetime.now() - timedelta(minutes=30))
    )

order = Order(item="Burger", status=Status.ACTIVE)
system.active_list.add_order(order)
system.reserve_order(order, student)


def get_system() -> System:
    """FastAPI dependency to retrieve the shared System instance."""
    return system
