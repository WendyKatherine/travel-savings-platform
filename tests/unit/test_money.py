from decimal import Decimal

import pytest

from app.domain.value_objects.money import Money, MoneyError


# Successful cases of creation and formating
def test_money_creation_from_string_int_and_decimal():
    """Verify that it can be correctly instantiated from str, int, or Decimal."""
    m_str = Money("100000", "COP")
    m_int = Money(100000, "COP")
    m_dec = Money(Decimal("100000"), "COP")

    assert m_str.amount == Decimal("100000.00")
    assert m_int.amount == Decimal("100000.00")
    assert m_dec.amount == Decimal("100000.00")
    assert m_str.currency == "COP"

def test_money_rounds_decimals_correctly():
    """Verify that the ROUND_HALF_UP rounding method is applied according to the currency."""
    m1 = Money("100000.556", "COP")
    m2 = Money("100000.554", "COP")

    assert m1.amount == Decimal("100000.56")
    assert m2.amount == Decimal("100000.55")

def test_money_is_frozen_immutable():
    """Verify that the Value Object is immutable (frozen dataclass)."""
    m = Money("50000", "COP")

    with pytest.raises(AttributeError):
        m.amount = Decimal("99999")

def test_money_addition_same_currency():
    """Addition in the same currency"""
    assert Money("10000", "COP") + Money("5000", "COP") == Money("15000", "COP")

def test_money_subtraction_same_currency():
    """Subtraction works when both amounts share the same currency."""
    assert Money("10000", "COP") - Money("5000", "COP") == Money("5000", "COP")

def test_money_comparison_by_value():
    """Two Monies are equal when amount AND currency match."""
    assert Money("1000", "COP") == Money("1000", "COP")
    assert Money("5000", "COP") != Money("1000", "COP")
    assert Money("1000", "COP") != Money("1000", "USD")

def test_money_decimal_precision():
    """Decimal arithmetic is exact: 0.1 + 0.2 == 0.3 (no float drift)."""
    assert Money("0.1", "USD") + Money("0.2", "USD") == Money("0.3", "USD")

# Edge Cases and exceptions

def test_money_unsupported_currency():
    """Raises MoneyError if the currency is not supported in the dictionary."""
    with pytest.raises(MoneyError, match="Unsupported currency"):
        Money("100000", "EUR")

@pytest.mark.parametrize("invalid_amount", [
    "EUR",
    "abc",          # Texto no numérico
    "12.34.56",     # Formato de puntos inválido
    "100000a",      # Letras mezcladas
    "",             # String vacío
])
def test_money_invalid_string_format_raises_error(invalid_amount):
    """Throws MoneyError if the string format does not match the regex."""
    with pytest.raises(MoneyError, match=r"Invalid amount format|Cannot parse amount"):
        Money(invalid_amount, "COP")

def test_money_unsupported_type_raises_error():
    """Raises MoneyError if a disallowed data type is passed (e.g., list or dict)."""
    with pytest.raises(MoneyError, match="Unsupported amount type"):
        Money([100000], "COP")  # type: ignore

@pytest.mark.parametrize("bad_value", [
    100.50,
    True,
    False
])
def test_money_float_and_bool_type_are_not_allowed(bad_value):
    """Raise MoneyError if the type of amount is float or bool"""
    with pytest.raises(MoneyError, match="Float and bool are not allowed"):
        Money(bad_value, "COP")

def test_money_add_different_currency():
    """Adding different currencies raises MoneyError.""" 
    with pytest.raises(MoneyError, match="Cannot add"):
        Money("10000", "COP") + Money("100", "USD")

def test_money_sub_different_currency():
    """Subtracting different currencies raises MoneyError."""
    with pytest.raises(MoneyError, match="Cannot subtract"):
        Money("10000", "COP") - Money("5000", "USD")