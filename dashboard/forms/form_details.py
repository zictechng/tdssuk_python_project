
from __future__ import annotations
from django import forms

from django.contrib.auth.models import Group, Permission

from mainWebsite.models import (
    AgentCommission, Category, CustomsDocument, CustomsDutyRecord,
    ExchangeRate, Expense, FuelRecord, Invoice, InvoiceLineItem,
    Order, OrderType, Payment, PromoCode, Route, Shipment, ShipmentTrackingEvent, StockMovement,
    StorageLocation, SupportTicket, SystemSetting, TicketReply, Vehicle, VehicleMaintenanceRecord,
    Warehouse, WarehouseItem,
)
from django.contrib.auth import get_user_model
User = get_user_model()

# create order form goes here
class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = "__all__"
        exclude = [
            "order_number", 
            "tracking_number", 
            "created_by", 
            "updated_by", 
            "origin", 
            "destination",
            "status",
            ]

    order_type = forms.ModelChoiceField(
    queryset=OrderType.objects.all(),
    required=True,                        
    error_messages={'required': 'Please select an order type.'}
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=True,                        
        error_messages={'required': 'Please select a category.'}
    )

    order_origin_country = forms.CharField(
        required=True,
        error_messages={'required': 'Please select origin country.'}
    )
    order_destination_country = forms.CharField(
        required=True,
        error_messages={'required': 'Please select a destination country.'}
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.data:
            data = self.data.copy()
            mappings = {
            'order_category':   'category',
            'order_qty':        'quantity',
            'order_weight':     'weight',
            'order_ref_number': 'reference_number',
            'order_ship_cost':  'shipping_cost',
            'order_amt':        'total_amount',
            'order_note':       'notes',
         }
            for html_name, form_name in mappings.items():
                if html_name in data:
                    data[form_name] = data[html_name]
            self.data = data


# edit form goes here
class OrderEditForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            # Customer
            'customer_name',
            'customer_phone',
            'customer_email',
 
            # Sender (pickup)
            'sender_name',
            'sender_phone',
            'sender_email',
            'sender_city',
            'sender_country',
            'sender_address',
 
            # Receiver (delivery)
            'receiver_name',
            'receiver_phone',
            'receiver_email',
            'receiver_city',
            'receiver_country',
            'receiver_address',
 
            # Order details
            'order_type',
            'category',
            'quantity',
            'weight',
            'order_origin_country',
            'order_destination_country',
            'reference_number',
            'expected_delivery_date',
            'tracking_number',
 
            # Payment
            'shipping_cost',
            'total_amount',
 
            # Status + notes
            'status',
            'notes',
        ]
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_email': forms.EmailInput(attrs={'class': 'form-control'}),
 
            'sender_name': forms.TextInput(attrs={'class': 'form-control'}),
            'sender_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'sender_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'sender_city': forms.TextInput(attrs={'class': 'form-control'}),
            'sender_country': forms.TextInput(attrs={'class': 'form-control'}),
            'sender_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
 
            'receiver_name': forms.TextInput(attrs={'class': 'form-control'}),
            'receiver_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'receiver_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'receiver_city': forms.TextInput(attrs={'class': 'form-control'}),
            'receiver_country': forms.TextInput(attrs={'class': 'form-control'}),
            'receiver_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
 
            'order_type': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'order_origin_country': forms.TextInput(attrs={'class': 'form-control'}),
            'order_destination_country': forms.TextInput(attrs={'class': 'form-control'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control'}),
            'expected_delivery_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'tracking_number': forms.TextInput(attrs={'class': 'form-control'}),
 
            'shipping_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'total_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
 
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
 

# shipment form goes here
class ShipmentCreateForm(forms.ModelForm):

    order = forms.ModelChoiceField(
        queryset=Order.objects.filter(status=Order.STATUS_PROCESSING),
        empty_label="Select an order ready for shipment",
        help_text="Only orders currently in Processing are eligible.",
    )

    class Meta:
        model = Shipment
        fields = [
            'order',
            'carrier_name',
            'shipment_direction',
            'pickup_date',
            'expected_delivery_date',
            'notes',
        ]
        widgets = {
            'pickup_date': forms.DateInput(attrs={'type': 'date'}),
            'expected_delivery_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_order(self):
        order = self.cleaned_data['order']
        has_active_shipment = Shipment.objects.filter(
            order=order,
            status__in=[Shipment.STATUS_PENDING, Shipment.STATUS_IN_TRANSIT],
        ).exists()
        if has_active_shipment:
            raise forms.ValidationError(
                "This order already has an active shipment in progress."
            )
        return order
    
class ShipmentStatusChangeForm(forms.Form):
    """
    Used on the Shipment Detail page — only shows statuses that are a
    valid next step from the shipment's current status (populated by
    the view using Shipment.ALLOWED_TRANSITIONS).
    """

    status = forms.ChoiceField(choices=[])
    location = forms.CharField(max_length=255, required=False)
    description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}), required=False,
    )

    def __init__(self, *args, allowed_statuses=None, **kwargs):
        super().__init__(*args, **kwargs)
        allowed_statuses = allowed_statuses or []
        self.fields['status'].choices = [
            choice for choice in Shipment.STATUS_CHOICES
            if choice[0] in allowed_statuses
        ]


# fleet management form

class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = [
            'ownership_type', 'status', 'name', 'vehicle_type',
            'license_plate', 'make', 'model', 'year', 'mileage', 'assigned_driver_name',
            'carrier_company_name', 'carrier_contact_phone', 'carrier_contact_email',
            'notes',
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned = super().clean()
        ownership = cleaned.get('ownership_type')

        if ownership == Vehicle.OWNERSHIP_THIRD_PARTY and not cleaned.get('carrier_company_name'):
            self.add_error('carrier_company_name', 'Required for third-party carriers.')

        if ownership == Vehicle.OWNERSHIP_IN_HOUSE and not cleaned.get('license_plate'):
            self.add_error('license_plate', 'Required for in-house vehicles.')

        return cleaned

class MaintenanceRecordForm(forms.ModelForm):
    class Meta:
        model = VehicleMaintenanceRecord
        fields = ['vehicle', 'service_type', 'description', 'cost', 'service_date', 'next_service_due', 'performed_by']
        widgets = {
            'service_date': forms.DateInput(attrs={'type': 'date'}),
            'next_service_due': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 2}),
        }

class FuelRecordForm(forms.ModelForm):
    class Meta:
        model = FuelRecord
        fields = ['vehicle', 'liters', 'cost', 'odometer_reading', 'fuel_date', 'station_name']
        widgets = {
            'fuel_date': forms.DateInput(attrs={'type': 'date'}),
        }

class RouteForm(forms.ModelForm):
    class Meta:
        model = Route
        fields = ['vehicle', 'route_name', 'start_location', 'end_location', 'planned_date', 'notes']
        widgets = {
            'planned_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

class WarehouseForm(forms.ModelForm):
    class Meta:
        model = Warehouse
        fields = ['name', 'address', 'city', 'country', 'capacity', 'is_active', 'notes']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 2}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

class StorageLocationForm(forms.ModelForm):
    class Meta:
        model = StorageLocation
        fields = ['warehouse', 'zone', 'shelf', 'description', 'is_occupied']

    def __init__(self, *args, **kwargs):
        warehouse_id = kwargs.pop('warehouse_id', None)
        super().__init__(*args, **kwargs)
        if warehouse_id:
            self.fields['warehouse'].initial = warehouse_id

class WarehouseItemForm(forms.ModelForm):
    class Meta:
        model = WarehouseItem
        fields = [
            'warehouse', 'location', 'customer_name', 'customer_phone',
            'description', 'category', 'quantity', 'weight_kg',
            'destination_country', 'status', 'tracking_number',
            'received_date', 'dispatched_date', 'notes',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
            'notes': forms.Textarea(attrs={'rows': 2}),
            'received_date': forms.DateInput(attrs={'type': 'date'}),
            'dispatched_date': forms.DateInput(attrs={'type': 'date'}),
        }

class StockMovementForm(forms.ModelForm):
    class Meta:
        model = StockMovement
        fields = [
            'item', 'movement_type', 'quantity',
            'from_location', 'to_location',
            'movement_date', 'reference', 'notes',
        ]
        widgets = {
            'movement_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }


# forms.py — Finance Management section

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = [
            'customer_name', 'customer_email', 'customer_phone',
            'destination_country', 'currency', 'status',
            'issue_date', 'due_date', 'discount', 'notes',
        ]
        # invoice_number is auto-generated, subtotal/total auto-calculated
        # amount_paid is updated by Payment.save() — never entered manually

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dates use Litepicker — no type="date" widgets
        self.fields['issue_date'].widget = forms.TextInput(
            attrs={'class': 'form-control datepicker', 'autocomplete': 'off',
                   'placeholder': 'Issue date'}
        )
        self.fields['due_date'].widget = forms.TextInput(
            attrs={'class': 'form-control datepicker', 'autocomplete': 'off',
                   'placeholder': 'Due date'}
        )

class InvoiceLineItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceLineItem
        fields = ['charge_type', 'description', 'quantity', 'unit_price', 'item']
        # amount is auto-calculated on InvoiceLineItem.save()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['item'].required = False
        self.fields['item'].help_text = 'Optional — link to a warehouse item.'

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['invoice', 'amount', 'method', 'reference', 'paid_on', 'notes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['paid_on'].widget = forms.TextInput(
            attrs={'class': 'form-control datepicker', 'autocomplete': 'off',
                   'placeholder': 'Payment date'}
        )
        # Only show unpaid/partially paid invoices as targets
        self.fields['invoice'].queryset = Invoice.objects.filter(
            status__in=[Invoice.STATUS_SENT, Invoice.STATUS_PARTIALLY_PAID, Invoice.STATUS_OVERDUE]
        )

class CustomsDutyForm(forms.ModelForm):
    class Meta:
        model = CustomsDutyRecord
        fields = [
            'item',
            'invoice',
            'destination_country',
            'duty_amount',
            'duty_currency',
            'customs_reference',
            'hs_code',
            'duty_rate',
            'tax_amount',
            'clearance_port',
            'customs_agent',
            'status',
            'paid_date',
            'reimbursed_date',
            'notes',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['invoice'].required = False
        self.fields['hs_code'].required = False
        self.fields['duty_rate'].required = False
        self.fields['clearance_port'].required = False
        self.fields['customs_agent'].required = False
        for field_name in ['paid_date', 'reimbursed_date']:
            self.fields[field_name].widget = forms.TextInput(
                attrs={
                    'class': 'form-control datepicker',
                    'autocomplete': 'off',
                    'placeholder': 'Select date',
                }
            )

class AgentCommissionForm(forms.ModelForm):
    class Meta:
        model = AgentCommission
        fields = [
            'item', 'agent_name', 'agent_country', 'commission_amount',
            'currency', 'status', 'due_date', 'paid_date', 'notes',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['item'].required = False
        for field_name in ['due_date', 'paid_date']:
            self.fields[field_name].widget = forms.TextInput(
                attrs={'class': 'form-control datepicker', 'autocomplete': 'off',
                       'placeholder': 'Select date'}
            )

class ExchangeRateForm(forms.ModelForm):
    class Meta:
        model = ExchangeRate
        fields = ['base_currency', 'target_currency', 'rate', 'effective_date']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['effective_date'].widget = forms.TextInput(
            attrs={'class': 'form-control datepicker', 'autocomplete': 'off',
                   'placeholder': 'Effective date'}
        )

    def clean(self):
        cleaned = super().clean()
        base = cleaned.get('base_currency')
        target = cleaned.get('target_currency')
        if base and target and base == target:
            raise forms.ValidationError(
                "Base and target currency cannot be the same."
            )
        return cleaned

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = [
            'warehouse', 'category', 'description',
            'amount', 'currency', 'expense_date', 'notes',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['warehouse'].required = False
        self.fields['expense_date'].widget = forms.TextInput(
            attrs={'class': 'form-control datepicker', 'autocomplete': 'off',
                   'placeholder': 'Expense date'}
        )

class CustomsDocumentForm(forms.ModelForm):
    class Meta:
        model = CustomsDocument
        fields = [
            'shipment',
            'item',
            'document_type',
            'document_number',
            'file',
            'status',
            'issued_date',
            'expiry_date',
            'notes',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['shipment'].required = False
        self.fields['item'].required = False
        self.fields['file'].required = False
        self.fields['document_number'].required = False
        self.fields['expiry_date'].required = False
        self.fields['shipment'].queryset = Shipment.objects.select_related('order').order_by('-created_at')
        self.fields['item'].queryset = WarehouseItem.objects.select_related('warehouse').order_by('-created_at')
        for field_name in ['issued_date', 'expiry_date']:
            self.fields[field_name].widget = forms.TextInput(
                attrs={
                    'class': 'form-control datepicker',
                    'autocomplete': 'off',
                    'placeholder': 'Select date',
                }
            )

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('shipment') and not cleaned.get('item'):
            raise forms.ValidationError(
                "Document must be linked to either a Shipment or a Warehouse Item."
            )
        return cleaned


# ──────────────────────────────────────────
# Uploaded Document Form
# ──────────────────────────────────────────
from mainWebsite.models import UploadedDocument

class UploadedDocumentForm(forms.ModelForm):

    class Meta:
        model = UploadedDocument
        fields = [
            'document_type',
            'title',
            'file',
            'status',
            'notes',
            'order',
            'shipment',
            'invoice',
        ]
        widgets = {
            'document_type': forms.Select(attrs={
                'class': 'form-select',
                'data-search': 'on',
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Document title',
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
            }),
            'status': forms.Select(attrs={
                'class': 'form-select',
                'data-search': 'on',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional notes...',
            }),
            'order': forms.Select(attrs={
                'class': 'form-select',
                'data-search': 'on',
            }),
            'shipment': forms.Select(attrs={
                'class': 'form-select',
                'data-search': 'on',
            }),
            'invoice': forms.Select(attrs={
                'class': 'form-select',
                'data-search': 'on',
            }),
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            if file.size > 20 * 1024 * 1024:
                raise forms.ValidationError('File size must not exceed 20MB.')
        return file


class RoleForm(forms.ModelForm):
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.select_related('content_type').all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model  = Group
        fields = ['name', 'permissions']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({'class': 'form-control'})

class TrackingSearchForm(forms.Form):
    query = forms.CharField(
        max_length=100,
        label='',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Tracking Number (TRK-...) or Shipment Number (SHP-...)',
            'autofocus': True,
        })
    )


class ShipmentTrackingEventForm(forms.ModelForm):
    class Meta:
        model  = ShipmentTrackingEvent
        fields = ['status', 'location', 'description']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Lagos Port, Heathrow Warehouse',
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Shipment cleared customs and dispatched',
            }),
        }


class GeneralSettingsForm(forms.ModelForm):
    class Meta:
        model  = SystemSetting
        fields = [
            'company_name', 'company_email', 'company_phone',
            'company_address', 'company_logo', 'website_url',
        ]
        widgets = {
            'company_name':    forms.TextInput(attrs={'class': 'form-control'}),
            'company_email':   forms.EmailInput(attrs={'class': 'form-control'}),
            'company_phone':   forms.TextInput(attrs={'class': 'form-control'}),
            'company_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'website_url':     forms.URLInput(attrs={'class': 'form-control'}),
            'company_logo':    forms.FileInput(attrs={'class': 'form-control'}),
        }


class EmailConfigForm(forms.ModelForm):
    smtp_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
        required=False,
        help_text='Leave blank to keep existing password.'
    )

    class Meta:
        model  = SystemSetting
        fields = [
            'smtp_host', 'smtp_port', 'smtp_username', 'smtp_password',
            'smtp_use_tls', 'email_from_name', 'email_from_address',
        ]
        widgets = {
            'smtp_host':          forms.TextInput(attrs={'class': 'form-control'}),
            'smtp_port':          forms.NumberInput(attrs={'class': 'form-control'}),
            'smtp_username':      forms.TextInput(attrs={'class': 'form-control'}),
            'email_from_name':    forms.TextInput(attrs={'class': 'form-control'}),
            'email_from_address': forms.EmailInput(attrs={'class': 'form-control'}),
            'smtp_use_tls':       forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class SecuritySettingsForm(forms.ModelForm):
    class Meta:
        model  = SystemSetting
        fields = [
            'max_login_attempts', 'session_timeout_mins',
            'require_2fa', 'password_min_length',
        ]
        widgets = {
            'max_login_attempts':   forms.NumberInput(attrs={'class': 'form-control'}),
            'session_timeout_mins': forms.NumberInput(attrs={'class': 'form-control'}),
            'password_min_length':  forms.NumberInput(attrs={'class': 'form-control'}),
            'require_2fa':          forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }



# ── Profile ───────────────────────────────────────────────────
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model  = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name':  forms.TextInput(attrs={'class': 'form-control'}),
            'email':      forms.EmailInput(attrs={'class': 'form-control'}),
        }

class ChangePasswordForm(forms.Form):
    current_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password     = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        pwd = self.cleaned_data.get('current_password')
        if not self.user.check_password(pwd):
            raise forms.ValidationError('Current password is incorrect.')
        return pwd

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('new_password')
        p2 = cleaned.get('confirm_password')
        if p1 and p2 and p1 != p2:
            self.add_error('confirm_password', 'Passwords do not match.')
        if p1 and len(p1) < 8:
            self.add_error('new_password', 'Password must be at least 8 characters.')
        return cleaned


# ── Support Ticket ────────────────────────────────────────────
class SupportTicketForm(forms.ModelForm):
    class Meta:
        model  = SupportTicket
        fields = ['submitter_name', 'submitter_email', 'subject', 'priority', 'description']
        widgets = {
            'submitter_name':  forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your full name'
            }),
            'submitter_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your@email.com'
            }),
            'subject':     forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brief summary of the issue'
            }),
            'priority':    forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe your issue in detail...'
            }),
        }

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If logged in user — pre-fill and hide name/email fields
        if user and user.is_authenticated:
            self.fields['submitter_name'].initial  = user.get_full_name()
            self.fields['submitter_email'].initial = user.email
            self.fields['submitter_name'].widget.attrs['readonly']  = True
            self.fields['submitter_email'].widget.attrs['readonly'] = True

class TicketReplyForm(forms.ModelForm):
    class Meta:
        model  = TicketReply
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Write your reply...'}),
        }



# ── Promo code ────────────────────────────────────────────
class PromoCodeForm(forms.ModelForm):
    class Meta:
        model  = PromoCode
        fields = [
            'code', 'discount_type', 'discount_value',
            'min_order_value', 'max_uses', 'status',
            'valid_from', 'valid_until',
        ]
        widgets = {
            'code':            forms.TextInput(attrs={'class': 'form-control text-uppercase', 'placeholder': 'e.g. SUMMER25'}),
            'discount_type':   forms.Select(attrs={'class': 'form-select'}),
            'discount_value':  forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'}),
            'min_order_value': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'}),
            'max_uses':        forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Leave blank for unlimited'}),
            'status':          forms.Select(attrs={'class': 'form-select'}),
            'valid_from':      forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'valid_until':     forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        }

    def clean_code(self):
        return self.cleaned_data.get('code', '').upper().strip()
































