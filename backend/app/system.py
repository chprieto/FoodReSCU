from order import Order, OrderList, Status, OLD_TIME
from user import Student, Staff

class System():
    def __init__(self):
        self.upcoming_list = OrderList(Status.UPCOMING)
        self.active_list = OrderList(Status.ACTIVE)
        self.reserved_list = OrderList(Status.RESERVED)
        self.picked_up_list = OrderList(Status.PICKED_UP)
        self.old_list = OrderList(Status.OLD)

        self.student_list: [Student] = []
        self.staff_list: [Staff] = []

    #potentially consolidate these functions into one, depends on if more distinct features are added to user classes
    def add_student(self, username: str, password: str, student_id: str):
        new_student = Student(username=username, password=password, student_id=student_id)
        self.student_list.append(new_student)
        return new_student

    def add_staff(self, username: str, password: str, staff_id: str):
        new_staff = Staff(username=username, password=password, staff_id=staff_id)
        self.staff_list.append(new_staff)

    def verify_student(self, student: Student):
        return student in self.student_list

    def verify_staff(self, staff: Staff):
        return staff in self.staff_list

    # likely will be updated to be data sent from API
    def incoming_order(self, item: str):
        new_order = Order(item=item)
        self.upcoming_list.add_order(new_order)

    def activate_order(self, order: Order, staff: Staff):
        if not self.verify_staff(staff):
            # staff not authorized
            return False
        
        if not order.activate():
            # order not ready to be activated
            return False

        if self.upcoming_list.remove_order(order) is None:
            # order not found
            return False

        self.active_list.add_order(order)
        return True

    def reserve_order(self, order: Order, student: Student):
        if not self.verify_student(student):
            # student not authorized
            return False
        
        if self.active_list.remove_order(order) is None:
            # order not found
            return False

        if not order.reserve(student.student_id):
            # not able to be reserved, should never happen in normal behavior
            return False

        self.reserved_list.add_order(order)
        student.reserved_orders.append(order.order_id)
        return True

    def pick_up_order(self, order: Order, student: Student):
        if order.reserved_by != student.student_id or order.order_id not in student.reserved_orders:
            # not authorized to pick up
            return False

        if self.reserved_list.remove_order(order) is None:
            # order not found
            return False

        if not order.pick_up():
            # not able to be picked up, should never happen in normal behavior
            return False

        self.picked_up_list.add_order(order)
        student.reserved_orders.remove(order.order_id)
        return True

    # helper function for set_orders_as_old
    def make_old(self, orders: OrderList):
        old_orders = [order for order in orders if order.get_time_active() > OLD_TIME]
        
        for order in old_orders:
            order.set_old()
            orders.remove_order(order)
            self.old_list.add_order(order)

        return old_orders

    def set_orders_as_old(self):
        self.make_old(self.upcoming_list)
        self.make_old(self.active_list)
        
        reserved_orders = self.make_old(self.reserved_list)
        for order in reserved_orders:
            # notify student who reserved order!
            pass