import pytest
from main_files.crud import get_password_hash, verify_password


def test_verify_password():
    x = "a"
    res = get_password_hash(x)
    assert True == verify_password(x, res)






