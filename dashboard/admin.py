
from django.contrib import admin

from django.utils.html import format_html

from mainWebsite.models import Order, Shipment, ShipmentTrackingEvent
from .services import ShipmentTransitionError, transition_shipment_status


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number', 'customer_name', 'receiver_name',
        'status_badge', 'order_destination_country', 'created_at',
    )
    list_filter = ('status', 'order_type', 'category', 'created_at')
    search_fields = (
        'order_number', 'tracking_number', 'customer_name',
        'customer_email', 'customer_phone', 'receiver_name',
    )
    readonly_fields = ('uuid', 'order_number', 'tracking_number', 'created_at', 'updated_at')

    def status_badge(self, obj):
        colors = {
            'new': '#206bc4', 'processing': '#f59f00', 'in_transit': '#17a2b8',
            'completed': '#2fb344', 'returned': '#f76707',
            'cancelled': '#d63939', 'rejected': '#d63939', 'deleted': '#6c757d',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 8px;'
            'border-radius:4px;font-size:11px;font-weight:600;">{}</span>',
            color, obj.get_status_display(),
        )
    status_badge.short_description = 'Status'


# ... (the ShipmentTrackingEventInline / ShipmentAdmin / ShipmentTrackingEventAdmin
#      code from before goes here, unchanged)

class ShipmentTrackingEventInline(admin.TabularInline):
    model = ShipmentTrackingEvent
    extra = 0
    readonly_fields = ('status', 'location', 'description', 'recorded_by', 'created_at')
    can_delete = False
    ordering = ('-created_at',)

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = (
        'shipment_number', 'order_link', 'status_badge',
        'carrier_name', 'pickup_date', 'expected_delivery_date', 'created_at',
    )
    list_filter = ('status', 'carrier_name', 'created_at')
    search_fields = (
        'shipment_number', 'order__order_number',
        'order__receiver_name', 'order__tracking_number',
    )
    readonly_fields = (
        'uuid', 'shipment_number', 'shipped_at', 'delivered_at',
        'cancelled_at', 'created_by', 'created_at', 'updated_at',
    )
    inlines = [ShipmentTrackingEventInline]
    actions = ['mark_in_transit', 'mark_delivered', 'mark_cancelled', 'mark_returned']

    fieldsets = (
        (None, {
            'fields': ('shipment_number', 'uuid', 'order', 'status')
        }),
        ('Carrier & Schedule', {
            'fields': ('carrier_name', 'pickup_date', 'expected_delivery_date')
        }),
        ('Delivery Record', {
            'fields': ('shipped_at', 'delivered_at', 'cancelled_at',
                       'proof_of_delivery', 'signed_by')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Audit', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )

    def order_link(self, obj):
        return format_html(
            '<a href="/admin/mainWebsite/order/{}/change/">{}</a>',
            obj.order.pk, obj.order.order_number,
        )
    order_link.short_description = 'Order'

    def status_badge(self, obj):
        colors = {
            Shipment.STATUS_PENDING: '#f59f00',
            Shipment.STATUS_IN_TRANSIT: '#17a2b8',
            Shipment.STATUS_DELIVERED: '#2fb344',
            Shipment.STATUS_CANCELLED: '#d63939',
            Shipment.STATUS_RETURNED: '#f76707',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 8px;'
            'border-radius:4px;font-size:11px;font-weight:600;">{}</span>',
            color, obj.get_status_display(),
        )
    status_badge.short_description = 'Status'

    def _bulk_transition(self, request, queryset, new_status):
        succeeded, failed = 0, 0
        for shipment in queryset:
            try:
                transition_shipment_status(
                    shipment=shipment, new_status=new_status, user=request.user,
                    description="Status changed via admin bulk action.",
                )
                succeeded += 1
            except ShipmentTransitionError:
                failed += 1
        if succeeded:
            self.message_user(request, f"{succeeded} shipment(s) updated.")
        if failed:
            self.message_user(
                request,
                f"{failed} shipment(s) skipped — invalid transition from their current status.",
                level='warning',
            )

    def mark_in_transit(self, request, queryset):
        self._bulk_transition(request, queryset, Shipment.STATUS_IN_TRANSIT)
    mark_in_transit.short_description = "Mark selected as In Transit"

    def mark_delivered(self, request, queryset):
        self._bulk_transition(request, queryset, Shipment.STATUS_DELIVERED)
    mark_delivered.short_description = "Mark selected as Delivered"

    def mark_cancelled(self, request, queryset):
        self._bulk_transition(request, queryset, Shipment.STATUS_CANCELLED)
    mark_cancelled.short_description = "Mark selected as Cancelled"

    def mark_returned(self, request, queryset):
        self._bulk_transition(request, queryset, Shipment.STATUS_RETURNED)
    mark_returned.short_description = "Mark selected as Returned"

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ShipmentTrackingEvent)
class ShipmentTrackingEventAdmin(admin.ModelAdmin):
    list_display = ('shipment', 'status', 'location', 'recorded_by', 'created_at')
    list_filter = ('status', 'created_at')
    readonly_fields = ('shipment', 'status', 'location', 'description', 'recorded_by', 'created_at')

    def has_add_permission(self, request):
        return False