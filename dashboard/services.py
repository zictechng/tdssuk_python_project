
from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from mainWebsite.models import Shipment, ShipmentTrackingEvent
# from mainWebsite.models import Vehicle, FleetAssignment   <- when Fleet is built


# ============================================================
# SHIPMENT MANAGEMENT
# ============================================================

class ShipmentTransitionError(Exception):
    """Raised when a requested shipment status change isn't allowed."""
    pass


@transaction.atomic
def transition_shipment_status(
    *, shipment: Shipment, new_status: str, user=None,
    location: str = '', description: str = '',
) -> Shipment:
    """Move a shipment to a new status, log it, and sync the parent Order."""
    allowed = Shipment.ALLOWED_TRANSITIONS.get(shipment.status, set())
    if new_status not in allowed:
        raise ShipmentTransitionError(
            f"Cannot move shipment from "
            f"'{shipment.get_status_display()}' to '{new_status}'."
        )

    shipment.status = new_status
    now = timezone.now()
    if new_status == Shipment.STATUS_IN_TRANSIT:
        shipment.shipped_at = now
    elif new_status == Shipment.STATUS_DELIVERED:
        shipment.delivered_at = now
    elif new_status == Shipment.STATUS_CANCELLED:
        shipment.cancelled_at = now
    shipment.save()

    ShipmentTrackingEvent.objects.create(
        shipment=shipment, status=new_status,
        location=location, description=description, recorded_by=user,
    )

    order = shipment.order
    order.status = Shipment.ORDER_STATUS_MAP[new_status]
    if user is not None:
        order.updated_by = user
    order.save(update_fields=['status', 'updated_by', 'updated_at'])

    return shipment


def cancel_shipment(*, shipment: Shipment, user=None, reason: str = '') -> Shipment:
    return transition_shipment_status(
        shipment=shipment, new_status=Shipment.STATUS_CANCELLED,
        user=user, description=reason or 'Shipment cancelled.',
    )


# ============================================================
# FLEET MANAGEMENT
# ============================================================
# Add Fleet's service functions here when you build that module —
# e.g. assign_driver_to_shipment(), mark_vehicle_unavailable(), etc.
# Same file, new section, same pattern as above.


# ============================================================
# WAREHOUSE MANAGEMENT
# ============================================================
# Same idea — add here when you get to it.