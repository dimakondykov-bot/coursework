import pytest

from src.utils import parse_amount


def test_parse_amount_basic_numbers():
    assert parse_amount('1234') == 1234.0
    assert parse_amount('1 234') == 1234.0
    assert parse_amount('1\xa0234') == 1234.0


def test_parse_amount_decimal_and_comma():
    assert parse_amount('1234,56') == 1234.56
    assert parse_amount('1 234,56') == 1234.56
    assert parse_amount('-160,89') == -160.89


def test_parse_amount_parentheses_negative():
    assert parse_amount('(1 234,56)') == -1234.56


def test_parse_amount_invalid():
    assert parse_amount(None) is None
    assert parse_amount('') is None
    assert parse_amount('abc') is None
