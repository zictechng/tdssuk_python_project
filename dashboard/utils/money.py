
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation


def to_decimal(value, default: str = "0.00") -> Decimal:
    
    if value is None or value == "":
        return Decimal(default)

    try:
        # str() first — prevents float imprecision (Decimal(75.5) is lossy)
        return Decimal(str(value)).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
    except InvalidOperation:
        return Decimal(default)


def calculate_total(shipping_cost, discount_amount) -> Decimal:
    
    shipping = to_decimal(shipping_cost)
    discount = to_decimal(discount_amount)
    return max(Decimal("0.00"), shipping - discount)