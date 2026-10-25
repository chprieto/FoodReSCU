# Unit Test Report

Framework: `unittest` (PyUnit)

Command (from `backend/app`):

```bash
python3 -m unittest tests.test_user tests.test_order tests.test_system -v
```

Result: **70 tests, 0 failures, 0 errors**.

## Counts

| Class | Test class | Tests |
| --- | --- | --- |
| User | `TestUser` | 10 |
| Student | `TestStudent` | 10 |
| Staff | `TestStaff` | 8 |
| Order | `TestOrder` | 15 |
| OrderList | `TestOrderList` | 11 |
| System | `TestSystem` | 16 |
| **Total** | **6 classes** | **70** |

Each class has at least 5 tests. The suite covers normal cases, edge cases (empty values, a single item, boundary times, large lists), and invalid cases (`None`, wrong types, unauthorized users).

## User actions covered

- Student signup and login (`add_student`, `verify_student`)
- Staff signup and login (`add_staff`, `verify_staff`)
- Student reserves an active order
- Student picks up their own reserved order
- Staff makes an order available (`activate_order`)
- Expired orders are moved to old

## Added tests

These five tests are in `tests/test_user.py` and check the user record, in the same way as the other user tests:

1. `TestUser.test_not_equal_when_credentials_differ` — a different username or password is a different user.
2. `TestUser.test_invalid_none_password` — invalid. `None` is rejected for password.
3. `TestUser.test_invalid_wrong_username_type` — invalid. A number is rejected for username.
4. `TestStudent.test_other_student_pickup_keeps_reservation` — another student cannot take this student's reserved order off their list.
5. `TestStaff.test_equal_only_when_staff_fields_match` — staff match only when username, password, and staff id all match.
