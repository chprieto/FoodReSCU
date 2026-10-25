import os
import sys
import unittest
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pydantic import ValidationError

from user import Student, Staff, User
from order import Order, Status
from system import System


class TestUser(unittest.TestCase):

    def test_normal_credentials(self):
        user = User(username="ada", password="secret")
        self.assertEqual(user.username, "ada")
        self.assertEqual(user.password, "secret")

    def test_normal_equal_when_fields_match(self):
        first = User(username="ada", password="secret")
        second = User(username="ada", password="secret")
        self.assertEqual(first, second)

    def test_edge_empty_credentials(self):
        user = User(username="", password="")
        self.assertEqual(user.username, "")
        self.assertEqual(user.password, "")

    def test_edge_very_long_credentials(self):
        username = "u" * 10000
        password = "p" * 10000
        user = User(username=username, password=password)
        self.assertEqual(len(user.username), 10000)
        self.assertEqual(user.password, password)

    def test_invalid_none_username(self):
        with self.assertRaises(ValidationError):
            User(username=None, password="secret")

    def test_invalid_wrong_password_type(self):
        with self.assertRaises(ValidationError):
            User(username="ada", password=12345)

    def test_invalid_missing_password(self):
        with self.assertRaises(ValidationError):
            User(username="ada")

    def test_not_equal_when_credentials_differ(self):
        user = User(username="ada", password="secret")
        self.assertNotEqual(user, User(username="ada", password="other"))
        self.assertNotEqual(user, User(username="grace", password="secret"))

    def test_invalid_none_password(self):
        with self.assertRaises(ValidationError):
            User(username="ada", password=None)

    def test_invalid_wrong_username_type(self):
        with self.assertRaises(ValidationError):
            User(username=12345, password="secret")


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

    def test_edge_reserved_orders_not_shared(self):
        first = Student(username="student1", password="pass1", student_id="STU001")
        second = Student(username="student2", password="pass2", student_id="STU002")
        first.reserved_orders.append(uuid.uuid4())
        self.assertEqual(len(first.reserved_orders), 1)
        self.assertEqual(len(second.reserved_orders), 0)

    def test_edge_single_reserved_order(self):
        order_id = uuid.uuid4()
        student = Student(
            username="student1",
            password="pass1",
            student_id="STU001",
            reserved_orders=[order_id],
        )
        self.assertEqual(len(student.reserved_orders), 1)
        self.assertEqual(student.reserved_orders[0], order_id)

    def test_edge_large_reserved_order_list(self):
        order_ids = [uuid.uuid4() for _ in range(500)]
        student = Student(
            username="student1",
            password="pass1",
            student_id="STU001",
            reserved_orders=order_ids,
        )
        self.assertEqual(len(student.reserved_orders), 500)
        self.assertEqual(student.reserved_orders[0], order_ids[0])
        self.assertEqual(student.reserved_orders[-1], order_ids[-1])

    def test_student_is_user(self):
        student = Student(username="student1", password="pass1", student_id="STU001")
        self.assertIsInstance(student, User)

    def test_invalid_none_student_id(self):
        with self.assertRaises(ValidationError):
            Student(username="student1", password="pass1", student_id=None)

    def test_invalid_reserved_orders_wrong_type(self):
        with self.assertRaises(ValidationError):
            Student(
                username="student1",
                password="pass1",
                student_id="STU001",
                reserved_orders="not-a-list",
            )

    def test_invalid_none_reserved_orders(self):
        with self.assertRaises(ValidationError):
            Student(
                username="student1",
                password="pass1",
                student_id="STU001",
                reserved_orders=None,
            )

    # Another student picking up does not change this student's reserved orders.
    def test_other_student_pickup_keeps_reservation(self):
        owner = Student(username="student1", password="pass1", student_id="STU001", reserved_orders=[])
        other = Student(username="student2", password="pass2", student_id="STU002", reserved_orders=[])
        order = Order(item="Burger", status=Status.ACTIVE)
        system = System()
        system.add_student("student1", "pass1", "STU001")
        system.add_student("student2", "pass2", "STU002")
        system.active_list.add_order(order)

        system.reserve_order(order, owner)
        system.pick_up_order(order, other)

        self.assertEqual(len(owner.reserved_orders), 1)
        self.assertEqual(owner.reserved_orders[0], order.order_id)
        self.assertEqual(len(other.reserved_orders), 0)


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

    def test_staff_is_user(self):
        staff = Staff(username="staff1", password="pass1", staff_id="STAFF001")
        self.assertIsInstance(staff, User)
        self.assertNotEqual(staff, User(username="staff1", password="pass1"))

    def test_edge_empty_staff_id(self):
        staff = Staff(username="staff1", password="pass1", staff_id="")
        self.assertEqual(staff.staff_id, "")

    def test_edge_single_character_staff_id(self):
        staff = Staff(username="s", password="p", staff_id="1")
        self.assertEqual(staff.username, "s")
        self.assertEqual(staff.staff_id, "1")

    def test_invalid_none_staff_id(self):
        with self.assertRaises(ValidationError):
            Staff(username="staff1", password="pass1", staff_id=None)

    def test_invalid_integer_staff_id(self):
        with self.assertRaises(ValidationError):
            Staff(username="staff1", password="pass1", staff_id=42)

    def test_invalid_missing_staff_id(self):
        with self.assertRaises(ValidationError):
            Staff(username="staff1", password="pass1")

    def test_equal_only_when_staff_fields_match(self):
        staff = Staff(username="staff1", password="pass1", staff_id="STAFF001")
        same = Staff(username="staff1", password="pass1", staff_id="STAFF001")
        different_id = Staff(username="staff1", password="pass1", staff_id="STAFF002")

        self.assertEqual(staff, same)
        self.assertEqual(staff.username, same.username)
        self.assertEqual(staff.password, same.password)
        self.assertEqual(staff.staff_id, same.staff_id)
        self.assertNotEqual(staff, different_id)


if __name__ == "__main__":
    unittest.main()