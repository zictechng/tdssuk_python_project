from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone
from mainWebsite.models import PromoCode


def apply_promo_code(code_str, shipping_cost):
    """
    Validate and apply a promo code against a shipping cost.

    Args:
        code_str:      The raw promo code string from the user.
        shipping_cost: The order shipping cost — must be Decimal or
                       int/str-coercible to Decimal.

    Returns:
        (promo_instance, discount_amount, error_message)
        Success: (PromoCode, Decimal, None)
        Failure: (None,      Decimal('0'), 'reason string')
    """
    # Guarantee shipping_cost is Decimal regardless of what the caller passes.
    # This makes the function safe whether called from a form (Decimal),
    # a view (string from POST), or a test (int/float).
    try:
        shipping_cost = Decimal(str(shipping_cost))
    except Exception:
        return None, Decimal("0"), "Invalid shipping cost."

    try:
        promo = PromoCode.objects.get(
            code=code_str.upper().strip(),
            status="active",
        )
    except PromoCode.DoesNotExist:
        return None, Decimal("0"), "Invalid or inactive promo code."

    if promo.is_expired:
        return None, Decimal("0"), "This promo code has expired."

    if promo.is_fully_used:
        return None, Decimal("0"), "This promo code has reached its usage limit."

    # Ensure min_order_value comparison is always Decimal vs Decimal.
    min_order_value = Decimal(str(promo.min_order_value))
    if shipping_cost < min_order_value:
        return None, Decimal("0"), (
            f"Minimum order value for this code is £{min_order_value}."
        )

    discount_value = Decimal(str(promo.discount_value))

    if promo.discount_type == "percentage":
        # THE FIX: divide by Decimal('100'), not the float/int literal 100.
        # Decimal / int is safe in Python, but Decimal / Decimal is explicit
        # and unambiguous — use it everywhere money is involved.
        discount = (discount_value / Decimal("100")) * shipping_cost
    else:
        # Flat discount — never exceed the shipping cost itself.
        discount = min(discount_value, shipping_cost)

    # Round to 2 decimal places using banker's rounding (ROUND_HALF_UP for money).
    discount = discount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return promo, discount, None