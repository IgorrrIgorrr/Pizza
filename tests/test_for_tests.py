from main_files.for_tests import summ
import pytest
from contextlib import nullcontext as does_not_raise


class TestCalculator:
    @pytest.mark.parametrize("x,y,res, expectation",
                             [
                                 (1, 2, 3, does_not_raise()),
                                 (3, 4, 7, does_not_raise()),
                                 (4, "5", 9, pytest.raises(TypeError)),
                             ])
    def test_summ(self, x, y, res, expectation):
        with expectation:
            assert summ(x, y) == res























# from crud import suum
#
# def test_suum():
#     # подготовка данных
#
#
#     # вызоов функции
#     #result = suum()
#
#     # проверка результата
#     # assert result == ?
#     pass