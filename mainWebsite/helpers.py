from django.shortcuts import render
from django.template.loader import render_to_string

from mainWebsite.models import Notification, UserActivity

from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string


def validation_error(request, message, alert_type):
    return render(
        request,
        "mainWebsite/partials/message.html",
        {
            "message": message,
            "alert_type": alert_type
        }
    )
    
def error_message(request, message, alert_type):
    return render(
        request,
        "mainWebsite/partials/message.html",
        {
            "message": message,
            "alert_type": alert_type
        }
    )
    
def success_message(request, message):
    return render(
        request,
        "mainWebsite/partials/message.html",
        {
            "message": message,
            "alert_type": "success",
            "clear_input": True
        }
    )

def toast_success(request, message, alert_type, redirect_url=None):
    return render(
        request,
        "mainWebsite/partials/notificationMessage.html",
        {
            "message": message,
            "alert_type": alert_type,
            "clear_input": True,
            "redirect_url": redirect_url,
        }
    )

def toast_error(request, message, alert_type, oob_content=""):
    return render(
        request,
        "mainWebsite/partials/notificationMessage.html",
        {
            "message": message,
            "alert_type": alert_type,
            "oob_content": oob_content,
        }
    )


def render_form_errors_oob(request, form, countries, ship_type, ship_category):

    # at the top of the function, normalize countries once
    country_choices = [(name, name) for code, name in countries]  # value=name, display=name

    panels = {
    "collapse-1-default": [
        {"name": "customer_name",  "label": "Customer Name",  "col_class": "col-md-5",          "placeholder": "Customer Name",  "required": True},
        {"name": "customer_phone", "label": "Customer Phone", "col_class": "col-sm-6 col-md-3", "placeholder": "Customer Phone", "required": True},
        {"name": "customer_email", "label": "Email address",  "col_class": "col-sm-6 col-md-4", "placeholder": "Customer Email", "type": "email"},
    ],
    "collapse-2-default": [
        {"name": "sender_name",    "label": "Sender Name",          "col_class": "col-md-5",          "placeholder": "Sender Name"},
        {"name": "sender_phone",   "label": "Sender Phone",         "col_class": "col-sm-6 col-md-3", "placeholder": "Sender Phone"},
        {"name": "sender_email",   "label": "Sender Email address", "col_class": "col-sm-6 col-md-4", "placeholder": "Sender Email", "type": "email"},
        {"name": "sender_city",    "label": "Sender City",          "col_class": "col-sm-6 col-md-6", "placeholder": "Sender City"},
        {"name": "sender_country", "label": "Sender Country",       "col_class": "col-sm-6 col-md-6", "type": "select",
         "placeholder": "Select country", "choices": country_choices},  # 
        {"name": "sender_address", "label": "Sender Address",       "col_class": "col-md-12",         "placeholder": "Sender Address"},
    ],
    "collapse-3-default": [
        {"name": "receiver_name",    "label": "Receiver Name",          "col_class": "col-md-5",          "placeholder": "Receiver Name"},
        {"name": "receiver_phone",   "label": "Receiver Phone",         "col_class": "col-sm-6 col-md-3", "placeholder": "Receiver Phone"},
        {"name": "receiver_email",   "label": "Receiver Email address", "col_class": "col-sm-6 col-md-4", "placeholder": "Receiver Email", "type": "email"},
        {"name": "receiver_city",    "label": "Receiver City",          "col_class": "col-sm-6 col-md-6", "placeholder": "Receiver City"},
        {"name": "receiver_country", "label": "Receiver Country",       "col_class": "col-sm-6 col-md-6", "type": "select",
         "placeholder": "Select country", "choices": country_choices}, 
        {"name": "receiver_address", "label": "Address",                "col_class": "col-md-12",         "placeholder": "Receiver Address"},
    ],
    "collapse-4-default": [
        {"name": "order_type",                "html_name": "order_type",                "label": "Order Type",                "col_class": "col-md-3",          "type": "select", "placeholder": "Select Type",     "choices": [(str(t.id), t.name) for t in ship_type],     "required": True},
        {"name": "category",                  "html_name": "order_category",            "label": "Order Category",            "col_class": "col-sm-6 col-md-3", "type": "select", "placeholder": "Select Category",  "choices": [(str(c.id), c.name) for c in ship_category], "required": True},
        {"name": "quantity",                  "html_name": "order_qty",                 "label": "Order Quantity",            "col_class": "col-sm-6 col-md-3", "type": "number", "placeholder": "Order Quantity"},
        {"name": "expected_delivery_date",    "html_name": "expected_delivery_date",    "label": "Expected Delivery Date",    "col_class": "col-sm-6 col-md-3", "type": "date",   "placeholder": "Select a date"},  
        {"name": "weight",                    "html_name": "order_weight",              "label": "Order Weight",              "col_class": "col-sm-3 col-md-3", "placeholder": "Order Weight"},
        {"name": "order_origin_country",      "html_name": "order_origin_country",      "label": "Order Origin Country",      "col_class": "col-sm-3 col-md-3", "type": "select", "placeholder": "Select country",   "choices": country_choices, "required": True},
        {"name": "order_destination_country", "html_name": "order_destination_country", "label": "Order Destination Country", "col_class": "col-sm-3 col-md-3", "type": "select", "placeholder": "Select country",   "choices": country_choices, "required": True},
        {"name": "reference_number",          "html_name": "order_ref_number",          "label": "Order Reference No",        "col_class": "col-sm-3 col-md-3", "placeholder": "Order Reference Number", "hint": "This order reference No. is optional."},
        {"name": "shipping_cost",             "html_name": "order_ship_cost",           "label": "Order Shipping Cost",       "col_class": "col-sm-6 col-md-4", "type": "number", "placeholder": "Shipping Cost",    "required": True},
        {"name": "total_amount",              "html_name": "order_amt",                 "label": "Order Total Amount",        "col_class": "col-sm-6 col-md-3", "type": "number", "placeholder": "Total Amount",     "required": True},
        {"name": "notes",                     "html_name": "order_note",                "label": "Additional Note",           "col_class": "col-md-12",         "type": "textarea", "placeholder": "Additional information...", "hint": "This additional note is optional."},
        ],
    }   

    error_panels = {}
    for panel_id, fields in panels.items():
        panel_has_errors = False
        enriched_fields = []

        for field_def in fields:
            fname = field_def["name"]
            if fname not in form.fields:
                continue
            bound = form[fname]
            html_name = field_def.get("html_name", fname)
            enriched = {
                **field_def,
                "errors": bound.errors,
                "value": form.data.get(html_name, ""),
            }
            if bound.errors:
                panel_has_errors = True
            enriched_fields.append(enriched)

        if panel_has_errors:
            error_panels[panel_id] = enriched_fields

    if not error_panels:
        return ""

    return render_to_string(
        "mainWebsite/partials/orderForm_error.html",
        {"error_panels": error_panels},
        request=request,
    )


def render_simple_form_errors_oob(form):
    if not form.errors:
        return ""

    error_html = ""
    for field_name, errors in form.errors.items():
        error_message = errors[0]
        error_html += f"""
        <div hx-swap-oob="true" id="error-{field_name}">
            <div class="invalid-feedback d-block">{error_message}</div>
        </div>
        """
    return error_html


def log_activity(user, action, model_name, object_repr, description=''):
   
    UserActivity.objects.create(
        user=user,
        action=action,
        model_name=model_name,
        object_repr=object_repr,
        description=description,
    )


def notify(user, title, message, notif_type='system', url=''):
    """Create an in-app notification for a user."""
    Notification.objects.create(
        user       = user,
        title      = title,
        message    = message,
        notif_type = notif_type,
        url        = url,
    )

def send_shipment_status_email(shipment):
    """Send email to customer when shipment status changes."""
    order = shipment.order
    if not order.customer_email:
        return

    subject = f'Shipment Update — {shipment.shipment_number}'
    context = {
        'shipment':        shipment,
        'order':           order,
        'tracking_number': shipment.shipment_number,
        'status':          shipment.get_status_display(),
    }
    html_message = render_to_string('mainDash/emails/shipment_status.html', context)
    plain_message = (
        f'Your shipment {shipment.shipment_number} status has been updated to: '
        f'{shipment.get_status_display()}.'
    )

    try:
        send_mail(
            subject      = subject,
            message      = plain_message,
            from_email   = settings.DEFAULT_FROM_EMAIL,
            recipient_list = [order.customer_email],
            html_message = html_message,
            fail_silently = True,
        )
    except Exception:
        pass

# send email notification to user once staff responded
def send_ticket_reply_email(ticket, reply):
    """Send email to ticket submitter when staff replies."""
    recipient = ticket.submitter_email or (
        ticket.submitted_by.email if ticket.submitted_by else None
    )
    if not recipient:
        return

    subject      = f'Reply on your ticket {ticket.ticket_number}'
    context      = {
        'ticket':     ticket,
        'reply':      reply,
        'recipient_name': ticket.submitter_name or (
            ticket.submitted_by.get_full_name() if ticket.submitted_by else 'Customer'
        ),
    }
    html_message  = render_to_string('mainDash/emails/ticket_reply.html', context)
    plain_message = f'Staff replied to your ticket {ticket.ticket_number}: {reply.message}'

    try:
        send_mail(
            subject        = subject,
            message        = plain_message,
            from_email     = settings.DEFAULT_FROM_EMAIL,
            recipient_list = [recipient],
            html_message   = html_message,
            fail_silently  = True,
        )
    except Exception:
        pass


def send_ticket_status_email(ticket):
    """Send email to ticket submitter when status changes."""
    recipient = ticket.submitter_email or (
        ticket.submitted_by.email if ticket.submitted_by else None
    )
    if not recipient:
        return

    recipient_name = ticket.submitter_name or (
        ticket.submitted_by.get_full_name() if ticket.submitted_by else 'Customer'
    )

    subject      = f'Your ticket {ticket.ticket_number} has been updated'
    context      = {
        'ticket':         ticket,
        'recipient_name': recipient_name,
    }
    html_message  = render_to_string('mainDash/emails/ticket_status.html', context)
    plain_message = (
        f'Your ticket {ticket.ticket_number} status has been updated to: '
        f'{ticket.get_status_display()}.'
    )

    try:
        send_mail(
            subject        = subject,
            message        = plain_message,
            from_email     = settings.DEFAULT_FROM_EMAIL,
            recipient_list = [recipient],
            html_message   = html_message,
            fail_silently  = True,
        )
    except Exception:
        pass