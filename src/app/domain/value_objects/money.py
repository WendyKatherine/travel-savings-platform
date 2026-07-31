"""
money.py — Value object for money with currency.

In Clean Architecture, Money is a domain value object:
immutable, self-validating, and currency-aware.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

# Supported currencies (ISO 4217)
# Adding a new currency is a single-line change. No switch statements.
CURRENCIES: dict[str, int] = {
    "COP": 2,   # Colombian Peso → 2 decimals
    "USD": 2,   # US Dollar      → 2 decimals
}

# Domain exception
class MoneyError(Exception):
    """Raised when an invalid money operation is attempted."""


# The main Money class
@dataclass(frozen=True)
class Money:
    """
    Immutable money value with currency.

    >>> Money("100000", "COP")
    Money('100000.00', 'COP')

    >>> Money("100000.00", "COP") + Money("50000.00", "COP")
    Money('150000.00', 'COP')

    Usage:

        price = Money("29000", "COP")
        tax   = Money("4000", "COP")
        total = price + tax       # Money('34000', 'COP')
    """

    amount: Decimal
    currency: str

    def __init__(self, amount: str | int | Decimal, currency: str) -> None:
        """
        Build a validated Money.

        Raises ``MoneyError`` when the amount is invalid or the currency
        is unknown.
        """
        if currency not in CURRENCIES:
            raise MoneyError(f"Unsupported currency: {currency!r}")

        if isinstance(amount, str):
            amount_str = amount.strip()
            try:
                parsed = Decimal(amount_str)
            except InvalidOperation as err:
                raise MoneyError(f"Cannot parse amount: {amount!r}") from err
        elif isinstance(amount, (bool, float)):
            raise MoneyError(f"Float and bool are not allowed: {amount!r}")
        elif isinstance(amount, int):
            parsed = Decimal(str(amount))
        elif isinstance(amount, Decimal):
            parsed = amount
        else:
            raise MoneyError(f"Unsupported amount type: {type(amount).__name__}")

        decimals = CURRENCIES[currency]
        rounded = parsed.quantize(
            Decimal("0." + "0" * decimals) 
            if decimals 
            else Decimal("1"), 
            rounding=ROUND_HALF_UP)

        # Store via object.__setattr__ because the dataclass is frozen
        object.__setattr__(self, "amount", rounded)
        object.__setattr__(self, "currency", currency)

    # Arithmetic

    def __add__(self, other: Money) -> Money:
        if not isinstance(other, Money):
            return NotImplemented
        if self.currency != other.currency:
            raise MoneyError(f"Cannot add {self.currency} + {other.currency}") from None
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: Money) -> Money:
        if not isinstance(other, Money):
            return NotImplemented
        if self.currency != other.currency:
            raise MoneyError(f"Cannot subtract {self.currency} - {other.currency}") from None
        return Money(self.amount - other.amount, self.currency)

    # Comparison

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount == other.amount and self.currency == other.currency

    def __lt__(self, other: Money) -> bool:
        if not isinstance(other, Money) or self.currency != other.currency:
            return NotImplemented
        return self.amount < other.amount

    def __le__(self, other: Money) -> bool:
        if not isinstance(other, Money) or self.currency != other.currency:
            return NotImplemented
        return self.amount <= other.amount

    def __gt__(self, other: Money) -> bool:
        if not isinstance(other, Money) or self.currency != other.currency:
            return NotImplemented
        return self.amount > other.amount

    def __ge__(self, other: Money) -> bool:
        if not isinstance(other, Money) or self.currency != other.currency:
            return NotImplemented
        return self.amount >= other.amount

    # Display

    def __repr__(self) -> str:
        return f"Money('{self.amount}', {self.currency!r})"

    def __str__(self) -> str:
        return f"{self.currency} {self.amount:,.{CURRENCIES[self.currency]}f}"

    # Conversion helper

    def to_decimal(self) -> Decimal:
        """Return the raw numeric amount as a ``Decimal``."""
        return self.amount