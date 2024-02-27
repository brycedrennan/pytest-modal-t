import time

import pytest


def sample_function_to_test(x):
    return x * 2


# Define a sample class with methods to test
class SampleClass:
    def __init__(self, value):
        self.value = value

    def increment(self):
        self.value += 1
        return self.value

    def decrement(self):
        self.value -= 1
        return self.value


# Test for a basic function
def test_sample_function():
    assert sample_function_to_test(2) == 4
    assert sample_function_to_test(-1) == -2


# Test for a class method
class TestSampleClass:
    def test_increment(self):
        obj = SampleClass(0)
        assert obj.increment() == 1

    def test_decrement(self):
        obj = SampleClass(2)
        assert obj.decrement() == 1


def test_with_exception():
    with pytest.raises(TypeError):
        sample_function_to_test(None)


@pytest.mark.parametrize("duration", list(range(50)))
def test_slow_stuff(duration):
    time.sleep(2)


def test_gone_wrong():
    assert "a" == "b"


@pytest.mark.parametrize(("a", "expected"), [(1, 2), (2, 4), (3, 6)])
def test_sample_function_parameterized(a, expected):
    assert sample_function_to_test(a) == expected
