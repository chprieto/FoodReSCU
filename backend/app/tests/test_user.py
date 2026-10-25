import unittest
from user import Student, Staff
from order import Order, OrderList, Status
from system import System

class TestStudent(unittest.TestCase):

    # 3 regular tests of created student vars and proper reserved_orders updating
    def test_normal_student(self):
        student1 = Student(username="student1", password="pass1", student_id="STU001", reserved_orders=[])
        order = Order(item="Burger", status=Status.ACTIVE)
        system = System()
        system.add_student("student1", "pass1", "STU001")
        system.active_list.add_order(order)

        # Test 1: Default student vars
        self.assertEqual(student1.username, "student1")
        self.assertEqual(student1.password, "pass1")
        self.assertEqual(student1.student_id, "STU001")
        self.assertEqual(len(student1.reserved_orders), 0)

        # Test 2: reserved_orders length is correct after reserving
        system.reserve_order(order, student1)
        self.assertEqual(len(student1.reserved_orders), 1)

        # Test 3: reserved_orders length is correct after picking up
        system.pick_up_order(order, student1)
        self.assertEqual(len(student1.reserved_orders), 0)

    # 1 test of reserved_orders updating correctly in cases where reserving fails
    def test_invalid_student(self):
        student1 = Student(username="student1", password="pass1", student_id="STU001", reserved_orders=[])
        order = Order(item="Burger", status=Status.RESERVED)
        system = System()
        system.add_student("student1", "pass1", "STU001")
        self.assertEqual(len(student1.reserved_orders), 0)

        # Test 4: reserved_orders length is correct after failing to reserve
        system.reserve_order(order, student1)
        self.assertEqual(len(student1.reserved_orders), 0)

    # 1 test of reserved_orders updating correctly with lots of repeated inputs
        student2 = Student(username="student2", password="pass2", student_id="STU002", reserved_orders=[])
        system.add_student("student2", "pass2", "STU002")
        self.assertEqual(len(student2.reserved_orders), 0)
        for _ in range(30):
            order2 = Order(item="Burger", status=Status.ACTIVE)
            system.active_list.add_order(order2)
            system.reserve_order(order2, student2)
            system.pick_up_order(order2, student2)

        # Test 5: reserved_orders length correct after reserving / picking up 30 orders
        self.assertEqual(len(student2.reserved_orders), 0)


class TestStaff(unittest.TestCase):

    #regular tests of created staff variables
    def test_normal_staff(self):
        staff1 = Staff(username="staff1", password="pass1", staff_id="STAFF001")
        staff2 = Staff(username="staff2", password="pass2", staff_id="STAFF002")

        # Tests 1-3: Default staff vars
        self.assertEqual(staff1.username, "staff1")
        self.assertEqual(staff1.password, "pass1")
        self.assertEqual(staff1.staff_id, "STAFF001")

        # Tests 4-6: Additional default staff vars
        self.assertEqual(staff2.username, "staff2")
        self.assertEqual(staff2.password, "pass2")
        self.assertEqual(staff2.staff_id, "STAFF002")



if __name__ == "__main__":
    unittest.main()