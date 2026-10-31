# Unit Test Report

Framework: `unittest` (PyUnit)

Command (from `backend/app`):

```bash
python3 -m unittest tests.test_user tests.test_order tests.test_system -v
```

Result: **78 tests, 0 failures, 0 errors**.

## Counts

| Class | Test class | Tests |
| --- | --- | --- |
| User | `TestUser` | 10 |
| Student | `TestStudent` | 10 |
| Staff | `TestStaff` | 8 |
| Order | `TestOrder` | 15 |
| OrderList | `TestOrderList` | 11 |
| System | `TestSystem` | 24 |
| **Total** | **6 classes** | **78** |

Each class has at least 5 tests. The suite covers normal cases, edge cases (empty values, a single item, boundary times, large lists, UUID auto-generation), and invalid/known incorrect cases (`None`, wrong types, unauthorized users, duplicate user IDs).

## User actions covered

- Student signup and registration (`add_student`, `verify_student`)
- Staff signup and registration (`add_staff`, `verify_staff`)
- Automatic ID generation when ID is omitted or `None`
- Duplicate student and staff ID rejection
- Student reserves an active order
- Student picks up their own reserved order
- Staff makes an order available (`activate_order`)
- Expired orders are moved to old

## Added tests for `add_student` and `add_staff`

These eight tests are in `tests/test_system.py` to test the new registration features:

1. `TestSystem.test_add_student_success_returns_student` — **Normal**: `add_student` successfully returns the created `Student` instance and appends it to `student_list`.
2. `TestSystem.test_add_staff_success_returns_staff` — **Normal**: `add_staff` successfully returns the created `Staff` instance and appends it to `staff_list`.
3. `TestSystem.test_add_student_duplicate_id_rejected` — **Known Incorrect**: attempting to add a student with an existing `student_id` returns `None` and does not add a duplicate.
4. `TestSystem.test_add_staff_duplicate_id_rejected` — **Known Incorrect**: attempting to add a staff with an existing `staff_id` returns `None` and does not add a duplicate.
5. `TestSystem.test_add_student_auto_generates_id_when_none` — **Edge / Feature**: passing `student_id=None` generates a valid 32-character hex UUID and successfully registers the student.
6. `TestSystem.test_add_staff_auto_generates_id_when_none` — **Edge / Feature**: passing `staff_id=None` generates a valid 32-character hex UUID and successfully registers the staff.
7. `TestSystem.test_add_user_with_omitted_id_parameter` — **Edge / Feature**: omitting the ID parameter entirely defaults to `None` and auto-generates a valid UUID.
8. `TestSystem.test_add_multiple_auto_id_users_generate_unique_ids` — **Edge**: multiple users added with `None` IDs receive distinct, non-colliding UUIDs.
