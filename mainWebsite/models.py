from __future__ import annotations
import os
from django.db import models
from django.conf import settings
import uuid
from django.core.exceptions import ValidationError
from django.utils import timezone
from django_countries.fields import CountryField
from dashboard.helper.status_badges import get_status_badge
from dashboard.utils.file_handler import build_upload_path, document_upload_to

# Create your models here.

class ContactMessage(models.Model):
    sender_name = models.CharField(max_length=100)
    sender_email = models.EmailField()
    sender_phone = models.CharField(max_length=30, blank=True)
    sender_subject = models.CharField(max_length=200)
    sender_message = models.TextField()
    status = models.CharField(max_length=30,
        choices=[
        ('pending', 'Pending'),
        ('read', 'Read'),
        ('replied', 'Replied'),
        ('completed', 'Completed'),
        ('close', 'Closed'),
        ],
    default='pending')
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.subject}"
    
    def status_badge(self):
        return get_status_badge(self.status)
    
    ticket = models.OneToOneField(
        'SupportTicket',
        on_delete  = models.SET_NULL,
        null       = True,
        blank      = True,
        related_name = 'contact_source'
    )

# newsletter class model
class Newsletter(models.Model):
    subscriber_email = models.EmailField()
    status = models.CharField(
        max_length=30,
        choices=[
            ('pending', 'Pending'),
            ('verify', 'Verified'),
            ('deleted', 'Deleted'),
            ('close', 'Closed'),
        ],
        default='pending'
    )
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.subscriber_email

class AllCountries(models.Model):
    country = CountryField()

# Quote request model

class QuoteRequest(models.Model):

    SERVICE_TYPES = [
        ('sea', 'Sea Shipping'),
        ('air', 'Air Freight'),
        ('vehicle', 'Vehicle Shipment'),
        ('other', 'Other Types'),
    ]

    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_TREATED = 'treated'
    STATUS_DELETED = 'deleted'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_TREATED, 'Treated'),
        (STATUS_DELETED, 'Deleted'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    quote_name = models.CharField(max_length=150)
    quote_email = models.EmailField()
    quote_phone = models.CharField(max_length=30)

    quote_serviceType = models.CharField(
        max_length=30,
        choices=SERVICE_TYPES
    )

    quoteFromCountry = models.CharField(max_length=100)
    quoteToCountry = models.CharField(max_length=100)

    quote_message = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='STATUS_PENDING'
    )
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_quote_requests"
    )

    updated_by_username = models.CharField(max_length=150, blank=True, null=True)
    
    updated_at = models.DateTimeField(auto_now=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quote_name} - {self.quote_serviceType}"

# order type model
class OrderType(models.Model):
    name = models.CharField(max_length=100)
    code = models.SlugField(unique=True)

    def __str__(self):
        return self.name
    
# category type model
class Category(models.Model):
    name = models.CharField(max_length=100)
    code = models.SlugField(unique=True)

    def __str__(self):
        return self.name

# Address shipment model
class Address(models.Model):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=50, blank=True, null=True)
    email = models.CharField(max_length=250, blank=True, null=True)

    address_line = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.city}"
    
# order model
class Order(models.Model):

    STATUS_NEW = 'new'
    STATUS_CANCELLED = 'cancelled'
    STATUS_COMPLETED = 'completed'
    STATUS_DELETED = 'deleted'
    STATUS_PROCESSING = 'processing'
    STATUS_IN_TRANSIT = 'in_transit'
    STATUS_RETURNED = 'returned'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = [
        (STATUS_NEW, 'New'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_DELETED, 'Deleted'),
        (STATUS_PROCESSING, 'Processing'),
        (STATUS_IN_TRANSIT, 'In Transit'),
        (STATUS_RETURNED, 'Returned'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    order_number = models.CharField(max_length=50, unique=True)

    customer_name = models.CharField(max_length=255)
    customer_email = models.EmailField(blank=True, null=True)
    customer_phone = models.CharField(max_length=50)

    # sender (pickup)
    sender_name = models.CharField(max_length=255, blank=True, null=True)
    sender_phone = models.CharField(max_length=50, blank=True, null=True)
    sender_email = models.EmailField(blank=True, null=True)
    sender_address = models.TextField(blank=True, null=True)
    sender_city = models.CharField(max_length=100, blank=True, null=True)
    sender_country = models.CharField(max_length=100, blank=True, null=True)

    # receiver (delivery)
    receiver_name = models.CharField(max_length=255)
    receiver_phone = models.CharField(max_length=50)
    receiver_email = models.CharField(max_length=50, blank=True, null=True)
    receiver_address = models.TextField(blank=True, null=True)
    receiver_city = models.CharField(max_length=100, blank=True, null=True)
    receiver_country = models.CharField(max_length=100)

    # ORIGIN / DESTINATION (logistics movement)
    origin = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        null=True,
        related_name='origin_orders'
    )

    destination = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        null=True,
        related_name='destination_orders'
    )

    # Add these two fields to Order model
    order_origin_country = models.CharField(max_length=100, blank=True, null=True)
    order_destination_country = models.CharField(max_length=100, blank=True, null=True)

    order_type = models.ForeignKey(
        OrderType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    quantity = models.PositiveIntegerField(default=1)

    weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    tracking_number = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True
    )

    shipping_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    promo_code = models.ForeignKey(
    'PromoCode',
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='orders',
    )
    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_NEW
    )

    reference_number = models.CharField(
    max_length=100,
    blank=True,
    null=True
    )

    notes = models.TextField(blank=True, null=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='orders_created'
    )

    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders_updated'
    )

    expected_delivery_date = models.DateField(
    blank=True,
    null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new and not self.order_number:
            self.order_number = f"ORD-{self.id:06d}"

        if not self.tracking_number:
            self.tracking_number = f"TRK-{uuid.uuid4().hex[:10].upper()}"

        super().save(update_fields=["order_number", "tracking_number"])

    def __str__(self):
        return self.order_number


# upload product/shipment images

def order_image_upload_path(instance, filename):
    return f'order_images/{instance.order.uuid}/{filename}'

class OrderImage(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='images',
    )
    image = models.ImageField(upload_to=order_image_upload_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f'Image for {self.order.order_number}'


# shipment model goes here
# ============================================================
# SHIPMENT MANAGEMENT
# ============================================================

class Shipment(models.Model):

    STATUS_PENDING = 'pending'
    STATUS_IN_TRANSIT = 'in_transit'
    STATUS_DELIVERED = 'delivered'
    STATUS_CANCELLED = 'cancelled'
    STATUS_RETURNED = 'returned'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_IN_TRANSIT, 'In Transit'),
        (STATUS_DELIVERED, 'Delivered'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_RETURNED, 'Returned'),
    ]

    # Maps each Shipment status straight onto the existing Order.STATUS_*
    # values, so syncing the two is a one-line lookup, not branching logic.
    ORDER_STATUS_MAP = {
        STATUS_PENDING: 'processing',
        STATUS_IN_TRANSIT: 'in_transit',
        STATUS_DELIVERED: 'completed',
        STATUS_CANCELLED: 'cancelled',
        STATUS_RETURNED: 'returned',
    }

    ALLOWED_TRANSITIONS = {
        STATUS_PENDING: {STATUS_IN_TRANSIT, STATUS_CANCELLED},
        STATUS_IN_TRANSIT: {STATUS_DELIVERED, STATUS_RETURNED, STATUS_CANCELLED},
        STATUS_DELIVERED: {STATUS_RETURNED},
        STATUS_CANCELLED: set(),
        STATUS_RETURNED: set(),
    }

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    shipment_number = models.CharField(max_length=50, unique=True, blank=True)

    order = models.ForeignKey(
        Order,
        on_delete=models.PROTECT,
        related_name='shipments',
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
    )

    # Carrier / vehicle. vehicle/driver point at Fleet Management, which
    # doesn't exist yet — left as plain text (carrier_name) for now so
    # this module isn't blocked. Swap to FKs once Fleet is built.
    carrier_name = models.CharField(max_length=150, blank=True, null=True)

    pickup_date = models.DateField(blank=True, null=True)
    expected_delivery_date = models.DateField(blank=True, null=True)
    shipped_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)

    proof_of_delivery = models.FileField(
        upload_to='shipments/pod/', blank=True, null=True,
    )
    signed_by = models.CharField(max_length=150, blank=True, null=True)

    notes = models.TextField(blank=True, null=True)

        # --- Customs & Direction ---
    DIRECTION_OUTBOUND = 'outbound'
    DIRECTION_INBOUND = 'inbound'
    DIRECTION_CHOICES = [
        ('outbound', 'Outbound (UK → West Africa)'),
        ('inbound', 'Inbound (West Africa → UK)'),
    ]

    CUSTOMS_STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('cleared',     'Cleared'),
        ('held',        'Held at Port'),
        ('rejected',    'Rejected'),
    ]

    shipment_direction = models.CharField(
        max_length=20,
        choices=DIRECTION_CHOICES,
        default='outbound',
        db_index=True,
    )
    customs_status = models.CharField(
        max_length=20,
        choices=CUSTOMS_STATUS_CHOICES,
        default='not_started',
        db_index=True,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='shipments_created',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['order', 'status']),
        ]

    def __str__(self):
        return self.shipment_number or str(self.uuid)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and not self.shipment_number:
            self.shipment_number = f"SHP-{self.id:06d}"
            super().save(update_fields=['shipment_number'])


class ShipmentTrackingEvent(models.Model):
    """Timeline entries for a shipment's tracking history."""

    shipment = models.ForeignKey(
        Shipment,
        on_delete=models.CASCADE,
        related_name='tracking_events',
    )
    status = models.CharField(max_length=20, choices=Shipment.STATUS_CHOICES)
    location = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='+',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.shipment.shipment_number} -> {self.status}"


# ============================================================
# FLEET MANAGEMENT
# ============================================================

class Vehicle(models.Model):

    OWNERSHIP_IN_HOUSE = 'in_house'
    OWNERSHIP_THIRD_PARTY = 'third_party'

    OWNERSHIP_CHOICES = [
        (OWNERSHIP_IN_HOUSE, 'In-House'),
        (OWNERSHIP_THIRD_PARTY, 'Third-Party Carrier'),
    ]

    STATUS_AVAILABLE = 'available'
    STATUS_ON_ROUTE = 'on_route'
    STATUS_MAINTENANCE = 'maintenance'
    STATUS_OUT_OF_SERVICE = 'out_of_service'

    STATUS_CHOICES = [
        (STATUS_AVAILABLE, 'Available'),
        (STATUS_ON_ROUTE, 'On Route'),
        (STATUS_MAINTENANCE, 'Under Maintenance'),
        (STATUS_OUT_OF_SERVICE, 'Out of Service'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    ownership_type = models.CharField(max_length=20, choices=OWNERSHIP_CHOICES, default=OWNERSHIP_IN_HOUSE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_AVAILABLE, db_index=True)

    # Always relevant
    name = models.CharField(max_length=150, help_text="e.g. Van 4, DHL Express")
    vehicle_type = models.CharField(max_length=100, blank=True, help_text="e.g. Van, Truck, Motorbike")

    # In-house only — blank/irrelevant for third-party
    license_plate = models.CharField(max_length=50, blank=True, null=True)
    make = models.CharField(max_length=100, blank=True, null=True)
    model = models.CharField(max_length=100, blank=True, null=True)
    year = models.PositiveIntegerField(blank=True, null=True)
    mileage = models.PositiveIntegerField(default=0, help_text="Current odometer reading, in km")
    assigned_driver_name = models.CharField(max_length=150, blank=True, null=True)

    # Third-party only — blank/irrelevant for in-house
    carrier_company_name = models.CharField(max_length=150, blank=True, null=True)
    carrier_contact_phone = models.CharField(max_length=50, blank=True, null=True)
    carrier_contact_email = models.EmailField(blank=True, null=True)

    notes = models.TextField(blank=True, null=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='vehicles_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


def vehicle_document_upload_path(instance, filename):
    return f'vehicle_documents/{instance.vehicle.uuid}/{filename}'


class VehicleMaintenanceRecord(models.Model):
    """Backs the 'Vehicle Maintenance' sidebar link."""

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='maintenance_records')
    service_type = models.CharField(max_length=150, help_text="e.g. Oil change, Tyre replacement, Inspection")
    description = models.TextField(blank=True, null=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    service_date = models.DateField()
    next_service_due = models.DateField(blank=True, null=True)
    performed_by = models.CharField(max_length=150, blank=True, null=True, help_text="Garage / mechanic name")

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-service_date']

    def __str__(self):
        return f"{self.vehicle.name} — {self.service_type} ({self.service_date})"


class FuelRecord(models.Model):
    """Backs the 'Fuel Records' sidebar link."""

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='fuel_records')
    liters = models.DecimalField(max_digits=8, decimal_places=2)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    odometer_reading = models.PositiveIntegerField(blank=True, null=True)
    fuel_date = models.DateField()
    station_name = models.CharField(max_length=150, blank=True, null=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fuel_date']

    def __str__(self):
        return f"{self.vehicle.name} — {self.liters}L on {self.fuel_date}"


class Route(models.Model):
    """Backs the 'Route Planning' sidebar link."""

    STATUS_PLANNED = 'planned'
    STATUS_ACTIVE = 'active'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PLANNED, 'Planned'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name='routes')
    route_name = models.CharField(max_length=150)
    start_location = models.CharField(max_length=255)
    end_location = models.CharField(max_length=255)
    planned_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PLANNED, db_index=True)
    notes = models.TextField(blank=True, null=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-planned_date']

    def __str__(self):
        return self.route_name


# ============================================================
# WAREHOUSE MANAGEMENT
# ============================================================

class Warehouse(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=150)
    address = models.TextField()
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='United Kingdom')
    capacity = models.PositiveIntegerField(help_text="Max storage units")
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='warehouses_created')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='warehouses_updated')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class StorageLocation(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='locations')
    zone = models.CharField(max_length=50, help_text="e.g. Zone A")
    shelf = models.CharField(max_length=50, blank=True, null=True, help_text="e.g. Shelf 3")
    description = models.CharField(max_length=255, blank=True, null=True)
    is_occupied = models.BooleanField(default=False)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='locations_created')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='locations_updated')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['warehouse', 'zone', 'shelf']
        unique_together = ['warehouse', 'zone', 'shelf']

    def __str__(self):
        return f"{self.warehouse.name} — {self.zone} {self.shelf or ''}".strip()


class WarehouseItem(models.Model):

    STATUS_IN_STOCK = 'in_stock'
    STATUS_DISPATCHED = 'dispatched'
    STATUS_HELD = 'held'

    STATUS_CHOICES = [
        (STATUS_IN_STOCK, 'In Stock'),
        (STATUS_DISPATCHED, 'Dispatched'),
        (STATUS_HELD, 'On Hold'),
    ]

    CATEGORY_GENERAL = 'general'
    CATEGORY_VEHICLE = 'vehicle'
    CATEGORY_CONTAINER = 'container'
    CATEGORY_AIR = 'air_freight'

    CATEGORY_CHOICES = [
        (CATEGORY_GENERAL, 'General Cargo'),
        (CATEGORY_VEHICLE, 'Vehicle'),
        (CATEGORY_CONTAINER, 'Container Cargo'),
        (CATEGORY_AIR, 'Air Freight'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='items')
    location = models.ForeignKey(StorageLocation, on_delete=models.SET_NULL, null=True, blank=True, related_name='items')
    customer_name = models.CharField(max_length=150)
    customer_phone = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(help_text="What is the item/cargo?")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default=CATEGORY_GENERAL, db_index=True)
    quantity = models.PositiveIntegerField(default=1)
    weight_kg = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    destination_country = models.CharField(max_length=100, help_text="e.g. Nigeria, Ghana")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_IN_STOCK, db_index=True)
    tracking_number = models.CharField(max_length=100, blank=True, null=True, unique=True)
    received_date = models.DateField()
    dispatched_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='items_created')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='items_updated')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.customer_name} — {self.description[:50]}"


class StockMovement(models.Model):

    MOVEMENT_IN = 'inbound'
    MOVEMENT_OUT = 'outbound'
    MOVEMENT_TRANSFER = 'transfer'

    MOVEMENT_CHOICES = [
        (MOVEMENT_IN, 'Inbound'),
        (MOVEMENT_OUT, 'Outbound'),
        (MOVEMENT_TRANSFER, 'Internal Transfer'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    item = models.ForeignKey(WarehouseItem, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_CHOICES, db_index=True)
    quantity = models.PositiveIntegerField(default=1)
    from_location = models.ForeignKey(StorageLocation, on_delete=models.SET_NULL, null=True, blank=True, related_name='movements_out')
    to_location = models.ForeignKey(StorageLocation, on_delete=models.SET_NULL, null=True, blank=True, related_name='movements_in')
    movement_date = models.DateField()
    reference = models.CharField(max_length=150, blank=True, null=True, help_text="e.g. Container number, AWB number")
    notes = models.TextField(blank=True, null=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='movements_created')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='movements_updated')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-movement_date']

    def __str__(self):
        return f"{self.get_movement_type_display()} — {self.item} ({self.movement_date})"


# ============================================================
# FINANCE MANAGEMENT
# ============================================================

class Invoice(models.Model):

    STATUS_DRAFT = 'draft'
    STATUS_SENT = 'sent'
    STATUS_PARTIALLY_PAID = 'partially_paid'
    STATUS_PAID = 'paid'
    STATUS_OVERDUE = 'overdue'
    STATUS_CANCELLED = 'cancelled'
    STATUS_REJECTED = 'rejected'           # ← separate constant

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_SENT, 'Sent'),
        (STATUS_PARTIALLY_PAID, 'Partially Paid'),
        (STATUS_PAID, 'Paid'),
        (STATUS_OVERDUE, 'Overdue'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_REJECTED, 'Rejected'),     # ← correct value now 'rejected'
    ]

    CURRENCY_GBP = 'GBP'
    CURRENCY_USD = 'USD'
    CURRENCY_NGN = 'NGN'
    CURRENCY_GHS = 'GHS'

    CURRENCY_CHOICES = [
        (CURRENCY_GBP, 'GBP — British Pound'),
        (CURRENCY_USD, 'USD — US Dollar'),
        (CURRENCY_NGN, 'NGN — Nigerian Naira'),
        (CURRENCY_GHS, 'GHS — Ghanaian Cedi'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    invoice_number = models.CharField(max_length=50, unique=True, help_text="e.g. INV-2026-0001")
    customer_name = models.CharField(max_length=150)
    customer_email = models.EmailField(blank=True, null=True)
    customer_phone = models.CharField(max_length=50, blank=True, null=True)
    destination_country = models.CharField(max_length=100)

    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default=CURRENCY_GBP)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT, db_index=True)

    issue_date = models.DateField()
    due_date = models.DateField()

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    notes = models.TextField(blank=True, null=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='invoices_created',
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='invoices_updated',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-issue_date', '-created_at']

    def __str__(self):
        return f"{self.invoice_number} — {self.customer_name}"

    @property
    def balance_due(self):
        return self.total_amount - self.amount_paid
    
    def save(self, *args, **kwargs):
            is_new = self.pk is None
            super().save(*args, **kwargs)
            if is_new and not self.invoice_number:
                now = timezone.localtime()
                self.invoice_number = f"INV-{now.month:02d}-{now.year}-{self.id:04d}"
                super().save(update_fields=['invoice_number'])

    def recalculate_totals(self, commit=True):
        """Recompute subtotal/total from line items. Call after line items change."""
        from django.db.models import Sum
        line_total = self.line_items.aggregate(total=Sum('amount'))['total'] or 0
        self.subtotal = line_total
        self.total_amount = line_total - self.discount
        if commit:
            self.save(update_fields=['subtotal', 'total_amount', 'updated_at'])
        
class InvoiceLineItem(models.Model):

    CHARGE_FREIGHT = 'freight'
    CHARGE_HANDLING = 'handling'
    CHARGE_INSURANCE = 'insurance'
    CHARGE_STORAGE = 'storage'
    CHARGE_DOCUMENTATION = 'documentation'
    CHARGE_CONTAINER = 'container'
    CHARGE_CAR = 'car'
    CHARGE_OTHER = 'other'

    CHARGE_TYPE_CHOICES = [
        (CHARGE_FREIGHT, 'Car Shipping'),
        (CHARGE_FREIGHT, 'Container Shipping'),
        (CHARGE_FREIGHT, 'Freight / Shipping'),
        (CHARGE_HANDLING, 'Handling Fee'),
        (CHARGE_INSURANCE, 'Insurance'),
        (CHARGE_STORAGE, 'Storage Fee'),
        (CHARGE_DOCUMENTATION, 'Documentation Fee'),
        (CHARGE_OTHER, 'Other'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name='line_items',
    )
    item = models.ForeignKey(
        'WarehouseItem', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='invoice_line_items',
    )
    charge_type = models.CharField(
        max_length=20, choices=CHARGE_TYPE_CHOICES,
        default=CHARGE_FREIGHT, db_index=True,
    )
    description = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text="quantity × unit_price, auto-calculated on save",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.get_charge_type_display()} — {self.description}"

    def save(self, *args, **kwargs):
        self.amount = (self.quantity or 0) * (self.unit_price or 0)
        super().save(*args, **kwargs)

class Payment(models.Model):

    METHOD_BANK_TRANSFER = 'bank_transfer'
    METHOD_CARD = 'card'
    METHOD_CASH = 'cash'
    METHOD_MOBILE_MONEY = 'mobile_money'

    METHOD_CHOICES = [
        (METHOD_BANK_TRANSFER, 'Bank Transfer'),
        (METHOD_CARD, 'Card Payment'),
        (METHOD_CASH, 'Cash'),
        (METHOD_MOBILE_MONEY, 'Mobile Money'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name='payments',
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(
        max_length=20, choices=METHOD_CHOICES, default=METHOD_BANK_TRANSFER,
    )
    reference = models.CharField(max_length=150, blank=True, null=True)
    paid_on = models.DateField()
    notes = models.TextField(blank=True, null=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='payments_created',
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='payments_updated',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-paid_on']

    def __str__(self):
        return f"{self.invoice.invoice_number} — {self.amount} ({self.paid_on})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Sync invoice amount_paid after every payment save
        total_paid = self.invoice.payments.aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        self.invoice.amount_paid = total_paid
        # Auto-update invoice status based on payment
        if total_paid >= self.invoice.total_amount:
            self.invoice.status = Invoice.STATUS_PAID
        elif total_paid > 0:
            self.invoice.status = Invoice.STATUS_PARTIALLY_PAID
        self.invoice.save(update_fields=['amount_paid', 'status', 'updated_at'])

class CustomsDutyRecord(models.Model):

    STATUS_PENDING = 'pending'
    STATUS_PROCESSING = 'processing'   # ← separate constant
    STATUS_PAID = 'paid'
    STATUS_REIMBURSED = 'reimbursed'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending Clearance'),
        (STATUS_PROCESSING, 'Processing Payment'),  # ← correct value now 'processing'
        (STATUS_PAID, 'Paid by Company'),
        (STATUS_REIMBURSED, 'Reimbursed by Customer'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    item = models.ForeignKey(
        'WarehouseItem', on_delete=models.CASCADE, related_name='customs_records',
    )
    invoice = models.ForeignKey(
        Invoice, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='customs_records',
    )
    destination_country = models.CharField(max_length=100)
    duty_amount = models.DecimalField(max_digits=10, decimal_places=2)
    duty_currency = models.CharField(
        max_length=3, choices=Invoice.CURRENCY_CHOICES, default=Invoice.CURRENCY_NGN,
    )
    customs_reference = models.CharField(max_length=150, blank=True, null=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True,
    )
    paid_date = models.DateField(blank=True, null=True)
    reimbursed_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

        # --- Extended Duty Fields ---
    hs_code = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Harmonized System commodity code e.g. 8703.23",
    )
    duty_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Applicable duty rate as a percentage e.g. 20.00 for 20%",
    )
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="VAT or levy amount in the same duty_currency",
    )
    clearance_port = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Port of clearance e.g. Lagos (Apapa), Tema, Takoradi",
    )
    customs_agent = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        help_text="Name of the clearing agent at destination",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='customs_records_created',
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='customs_records_updated',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Duty — {self.item.customer_name} ({self.get_status_display()})"

class AgentCommission(models.Model):

    STATUS_PENDING = 'pending'
    STATUS_PROCESSING = 'processing'   # ← separate constant
    STATUS_PAID = 'paid'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PROCESSING, 'Processing'),  # ← correct value now 'processing'
        (STATUS_PAID, 'Paid'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    item = models.ForeignKey(
        'WarehouseItem', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='agent_commissions',
    )
    agent_name = models.CharField(max_length=150)
    agent_country = models.CharField(max_length=100)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(
        max_length=3, choices=Invoice.CURRENCY_CHOICES, default=Invoice.CURRENCY_USD,
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True,
    )
    due_date = models.DateField(blank=True, null=True)
    paid_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='commissions_created',
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='commissions_updated',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.agent_name} — {self.commission_amount} {self.currency}"

class ExchangeRate(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    base_currency = models.CharField(
        max_length=3, choices=Invoice.CURRENCY_CHOICES, default=Invoice.CURRENCY_GBP,
    )
    target_currency = models.CharField(
        max_length=3, choices=Invoice.CURRENCY_CHOICES, default=Invoice.CURRENCY_NGN,
    )
    rate = models.DecimalField(
        max_digits=12, decimal_places=4,
        help_text="1 base_currency = rate target_currency",
    )
    effective_date = models.DateField()

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='exchange_rates_created',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-effective_date']
        unique_together = ['base_currency', 'target_currency', 'effective_date']

    def __str__(self):
        return f"1 {self.base_currency} = {self.rate} {self.target_currency} ({self.effective_date})"

class Expense(models.Model):

    CATEGORY_RENT = 'rent'
    CATEGORY_UTILITIES = 'utilities'
    CATEGORY_FUEL = 'fuel'
    CATEGORY_STAFF = 'staff'
    CATEGORY_MAINTENANCE = 'maintenance'
    CATEGORY_OTHER = 'other'

    CATEGORY_CHOICES = [
        (CATEGORY_RENT, 'Rent'),
        (CATEGORY_UTILITIES, 'Utilities'),
        (CATEGORY_FUEL, 'Fuel'),
        (CATEGORY_STAFF, 'Staff / Payroll'),
        (CATEGORY_MAINTENANCE, 'Maintenance'),
        (CATEGORY_OTHER, 'Other'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    warehouse = models.ForeignKey(
        'Warehouse', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='expenses',
    )
    category = models.CharField(
        max_length=20, choices=CATEGORY_CHOICES,
        default=CATEGORY_OTHER, db_index=True,
    )
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(
        max_length=3, choices=Invoice.CURRENCY_CHOICES, default=Invoice.CURRENCY_GBP,
    )
    expense_date = models.DateField()
    notes = models.TextField(blank=True, null=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='expenses_created',
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='expenses_updated',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-expense_date']

    def __str__(self):
        return f"{self.get_category_display()} — {self.description} ({self.amount} {self.currency})"

# ============================================================
# CUSTOMS DOCUMENT MANAGEMENT
# ============================================================

def customs_document_upload_path(instance, filename):
    return f'customs_documents/{instance.uuid}/{filename}'


class CustomsDocument(models.Model):

    DOC_BILL_OF_LADING      = 'bill_of_lading'
    DOC_AIRWAY_BILL         = 'airway_bill'
    DOC_PACKING_LIST        = 'packing_list'
    DOC_COMMERCIAL_INVOICE  = 'commercial_invoice'
    DOC_CERTIFICATE_ORIGIN  = 'certificate_of_origin'
    DOC_CUSTOMS_DECLARATION = 'customs_declaration'
    DOC_IMPORT_DUTY_RECEIPT = 'import_duty_receipt'
    DOC_DELIVERY_ORDER      = 'delivery_order'
    DOC_OTHER               = 'other'

    DOCUMENT_TYPE_CHOICES = [
        (DOC_BILL_OF_LADING,      'Bill of Lading'),
        (DOC_AIRWAY_BILL,         'Airway Bill (AWB)'),
        (DOC_PACKING_LIST,        'Packing List'),
        (DOC_COMMERCIAL_INVOICE,  'Commercial Invoice'),
        (DOC_CERTIFICATE_ORIGIN,  'Certificate of Origin'),
        (DOC_CUSTOMS_DECLARATION, 'Customs Declaration'),
        (DOC_IMPORT_DUTY_RECEIPT, 'Import Duty Receipt'),
        (DOC_DELIVERY_ORDER,      'Delivery Order'),
        (DOC_OTHER,               'Other'),
    ]

    STATUS_PENDING   = 'pending'
    STATUS_SUBMITTED = 'submitted'
    STATUS_APPROVED  = 'approved'
    STATUS_REJECTED  = 'rejected'

    STATUS_CHOICES = [
        (STATUS_PENDING,   'Pending'),
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_APPROVED,  'Approved'),
        (STATUS_REJECTED,  'Rejected'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    shipment = models.ForeignKey(
        'Shipment',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='customs_documents',
    )
    item = models.ForeignKey(
        'WarehouseItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customs_documents',
    )
    document_type = models.CharField(
        max_length=30,
        choices=DOCUMENT_TYPE_CHOICES,
        default=DOC_OTHER,
        db_index=True,
    )
    document_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="e.g. BOL number, AWB number, declaration reference",
    )
    file = models.FileField(
        upload_to=customs_document_upload_path,
        blank=True,
        null=True,
        help_text="PDF, JPG or PNG — max 10MB",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
    )
    issued_date = models.DateField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='customs_documents_created',
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customs_documents_updated',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['shipment', 'document_type']),
            models.Index(fields=['item', 'document_type']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.get_document_type_display()} — {self.document_number or 'No Ref'}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if not self.shipment and not self.item:
            raise ValidationError(
                "A customs document must be linked to either a Shipment or a Warehouse Item."
            )


class UploadedDocument(models.Model):

    DOCUMENT_TYPE_CHOICES = [
        ('shipping_label',  'Shipping Label'),
        ('delivery_note',   'Delivery Note'),
        ('invoice',         'Invoice'),
        ('customs_form',    'Customs Form'),
        ('payment_proof',   'Payment Proof'),
        ('reimbursement',   'Reimbursement Receipt'),
        ('other',           'Other'),
    ]

    STATUS_PENDING  = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_PROCESSING = 'processing'

    STATUS_CHOICES = [
        (STATUS_PENDING,  'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_PROCESSING, 'Processing'),
    ]

    uuid          = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPE_CHOICES)
    title         = models.CharField(max_length=255)
    file          = models.FileField(upload_to=document_upload_to)
    file_size     = models.PositiveIntegerField(null=True, blank=True, help_text='Size in bytes')
    status        = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    notes         = models.TextField(blank=True)

    # Links — all optional, staff attaches to whatever is relevant
    order         = models.ForeignKey('Order',    null=True, blank=True, on_delete=models.SET_NULL, related_name='documents')
    shipment      = models.ForeignKey('Shipment', null=True, blank=True, on_delete=models.SET_NULL, related_name='documents')
    invoice       = models.ForeignKey('Invoice',  null=True, blank=True, on_delete=models.SET_NULL, related_name='documents')

    uploaded_by   = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='uploaded_documents')
    generated     = models.BooleanField(default=False, help_text='True if system-generated (label/note), False if manually uploaded')
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Uploaded Document'
        verbose_name_plural = 'Uploaded Documents'

    def __str__(self):
        return f'{self.get_document_type_display()} — {self.title}'

    def filename(self):
        return os.path.basename(self.file.name) if self.file else ''

# ============================================================
# CUSTOMS USER PROFILE IMAGE AND OTHER FIELDS
# ============================================================
def profile_image_upload_path(instance, filename):
    return f'profile_images/{instance.user.id}/{filename}'

class UserProfile(models.Model):
    user          = models.OneToOneField(
                        settings.AUTH_USER_MODEL,
                        on_delete=models.CASCADE,
                        related_name='profile'
                    )
    uuid          = models.UUIDField(default=uuid.uuid4, unique=True, editable=False) # ← add this
    phone         = models.CharField(max_length=30, unique=True, blank=True, null=True)
    profile_image = models.ImageField(
                        upload_to=profile_image_upload_path,
                        blank=True, null=True
                    )
    is_online      = models.BooleanField(default=False)
    last_login_at  = models.DateTimeField(null=True, blank=True)
    last_logout_at = models.DateTimeField(null=True, blank=True)
    is_deleted    = models.BooleanField(default=False, db_index=True)
    deleted_at    = models.DateTimeField(blank=True, null=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.get_full_name()} — Profile'


class LoginHistory(models.Model):
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('logout', 'Logout'),
    ]

    uuid        = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='login_history')
    ip_address  = models.GenericIPAddressField(null=True, blank=True)
    user_agent  = models.TextField(blank=True)
    status      = models.CharField(max_length=10, choices=STATUS_CHOICES, default='success')
    timestamp   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Login History'
        verbose_name_plural = 'Login Histories'

    def __str__(self):
        return f"{self.user} — {self.status} — {self.timestamp:%d/%m/%Y %H:%M}"


class UserActivity(models.Model):
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('deleted', 'Deleted'),
    ]

    uuid        = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='activities')
    action      = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name  = models.CharField(max_length=100)
    object_repr = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    timestamp   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'User Activity'
        verbose_name_plural = 'User Activities'

    def __str__(self):
        return f"{self.user} {self.action} {self.model_name} — {self.timestamp:%d/%m/%Y %H:%M}"

class SystemSetting(models.Model):
    # General
    company_name        = models.CharField(max_length=200, default='TDSSUK Global Services Ltd')
    company_email       = models.EmailField(default='')
    company_phone       = models.CharField(max_length=30, blank=True)
    company_address     = models.TextField(blank=True)
    company_logo        = models.ImageField(upload_to='settings/', blank=True, null=True)
    website_url         = models.URLField(blank=True)

    # Email / SMTP
    smtp_host           = models.CharField(max_length=200, blank=True)
    smtp_port           = models.PositiveIntegerField(default=587)
    smtp_username       = models.CharField(max_length=200, blank=True)
    smtp_password       = models.CharField(max_length=200, blank=True)
    smtp_use_tls        = models.BooleanField(default=True)
    email_from_name     = models.CharField(max_length=100, blank=True)
    email_from_address  = models.EmailField(blank=True)

    # Security
    max_login_attempts  = models.PositiveIntegerField(default=5)
    session_timeout_mins = models.PositiveIntegerField(default=60)
    require_2fa         = models.BooleanField(default=False)
    password_min_length = models.PositiveIntegerField(default=8)

    updated_at          = models.DateTimeField(auto_now=True)
    updated_by          = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='settings_updates'
    )

    class Meta:
        verbose_name = 'System Setting'

    def __str__(self):
        return self.company_name

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

class BackupLog(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    filename    = models.CharField(max_length=255)
    size_kb     = models.PositiveIntegerField(default=0)
    created_by  = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True,
        on_delete=models.SET_NULL
    )
    created_at  = models.DateTimeField(auto_now_add=True)
    notes       = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.filename


# ── NOTIFICATION ──────────────────────────────────────────────
class Notification(models.Model):
    TYPES = [
        ('shipment', 'Shipment Update'),
        ('order',    'Order Update'),
        ('system',   'System'),
        ('ticket',   'Support Ticket'),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title      = models.CharField(max_length=255)
    message    = models.TextField()
    notif_type = models.CharField(max_length=20, choices=TYPES, default='system')
    is_read    = models.BooleanField(default=False)
    url        = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} → {self.user.username}'


# ── SUPPORT TICKET ────────────────────────────────────────────
class SupportTicket(models.Model):
    PRIORITY = [
        ('low',      'Low'),
        ('medium',   'Medium'),
        ('high',     'High'),
        ('urgent',   'Urgent'),
    ]
    STATUS = [
        ('open',        'Open'),
        ('in_progress', 'In Progress'),
        ('resolved',    'Resolved'),
        ('closed',      'Closed'),
    ]
    ticket_number = models.CharField(max_length=20, unique=True, editable=False)
    submitted_by  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets')
    submitter_email = models.EmailField(blank=True) 
    submitter_name  = models.CharField(max_length=150, blank=True) 
    subject       = models.CharField(max_length=255)
    description   = models.TextField()
    priority      = models.CharField(max_length=10, choices=PRIORITY, default='medium')
    status        = models.CharField(max_length=15, choices=STATUS, default='open')
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tickets'
    )

    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)
    resolved_at   = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            last = SupportTicket.objects.order_by('-id').first()
            next_id = (last.id + 1) if last else 1
            self.ticket_number = f'TKT-{next_id:05d}'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.ticket_number


class TicketReply(models.Model):
    ticket     = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='replies')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    message    = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']


# ── PROMO CODE ────────────────────────────────────────────
class PromoCode(models.Model):
    DISCOUNT_TYPES = [
        ('percentage', 'Percentage'),
        ('fixed',      'Fixed Amount'),
    ]
    STATUS = [
        ('active',   'Active'),
        ('inactive', 'Inactive'),
        ('expired',  'Expired'),
    ]

    code            = models.CharField(max_length=50, unique=True)
    discount_type   = models.CharField(max_length=10, choices=DISCOUNT_TYPES, default='percentage')
    discount_value  = models.DecimalField(max_digits=10, decimal_places=2)
    min_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_uses        = models.PositiveIntegerField(null=True, blank=True, help_text='Leave blank for unlimited')
    used_count      = models.PositiveIntegerField(default=0)
    status          = models.CharField(max_length=10, choices=STATUS, default='active')
    valid_from      = models.DateTimeField(default=timezone.now)
    valid_until     = models.DateTimeField(null=True, blank=True)
    created_by      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='promo_codes')
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.code

    @property
    def is_expired(self):
        if self.valid_until and timezone.now() > self.valid_until:
            return True
        return False

    @property
    def is_fully_used(self):
        if self.max_uses and self.used_count >= self.max_uses:
            return True
        return False

    @property
    def remaining_uses(self):
        if self.max_uses is None:
            return '∞'
        return max(0, self.max_uses - self.used_count)








