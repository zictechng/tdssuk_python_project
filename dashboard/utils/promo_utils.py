
from django.utils import timezone

from mainWebsite.models import PromoCode

def apply_promo_code(code_str, shipping_cost):
    """
    Returns (promo_instance, discount_amount, error_message).
    On failure: (None, 0, 'error message')
    On success: (promo, discount_decimal, None)
    """
    try:
        promo = PromoCode.objects.get(code=code_str.upper().strip(), status='active')
    except PromoCode.DoesNotExist:
        return None, 0, 'Invalid or inactive promo code.'

    if promo.is_expired:
        return None, 0, 'This promo code has expired.'

    if promo.is_fully_used:
        return None, 0, 'This promo code has reached its usage limit.'

    if shipping_cost < promo.min_order_value:
        return None, 0, (
            f'Minimum order value for this code is £{promo.min_order_value}.'
        )

    if promo.discount_type == 'percentage':
        discount = (promo.discount_value / 100) * shipping_cost
    else:
        discount = min(promo.discount_value, shipping_cost)

    return promo, round(discount, 2), None