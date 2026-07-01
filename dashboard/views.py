from __future__ import annotations
from datetime import timedelta, date
import subprocess
from django.db.models import Q, Count, Prefetch, Sum, Max,  Avg, Q, F, ExpressionWrapper, DurationField, FloatField
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.decorators import login_required, user_passes_test
import time
import os
import shutil
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.conf import settings as django_settings
from django.db import models
from django.urls import reverse
from django.http import Http404, HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django import forms
from django_countries import countries
import csv
from django.db.models.functions import TruncMonth, TruncDate
from django.core.mail import send_mail
from urllib.parse import urlencode
from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.shortcuts import render, redirect
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.contrib.auth import logout as auth_logout

from dashboard.forms.form_details import AgentCommissionForm, ChangePasswordForm, CustomsDocumentForm, CustomsDutyForm, EmailConfigForm, ExchangeRateForm, ExpenseForm, FuelRecordForm, GeneralSettingsForm, InvoiceForm, InvoiceLineItemForm, MaintenanceRecordForm, OrderEditForm, OrderForm, PaymentForm, ProfileUpdateForm, PromoCodeForm, RoleForm, RouteForm, SecuritySettingsForm, ShipmentCreateForm, ShipmentStatusChangeForm, ShipmentTrackingEventForm, StockMovementForm, StorageLocationForm, SupportTicketForm, TicketReplyForm, TrackingSearchForm, UploadedDocumentForm, VehicleForm, WarehouseForm, WarehouseItemForm
from dashboard.services import ShipmentTransitionError, transition_shipment_status
from dashboard.utils.file_handler import decode_pk, delete_file, encode_pk
from dashboard.utils.promo_utils import apply_promo_code
from .forms.formLogin import LoginForm
from mainWebsite.models import AgentCommission, BackupLog, Category, ContactMessage, CustomsDocument, CustomsDutyRecord, ExchangeRate, Expense, FuelRecord, Invoice, InvoiceLineItem, LoginHistory, Notification, Order, OrderImage, OrderType, Payment, PromoCode, QuoteRequest, Route, Shipment, ShipmentTrackingEvent, StockMovement, StorageLocation, SupportTicket, SystemSetting, UploadedDocument, UserActivity, UserProfile, Vehicle, VehicleMaintenanceRecord, Warehouse, WarehouseItem
from mainWebsite.helpers import log_activity, notify, render_form_errors_oob, render_simple_form_errors_oob, send_shipment_status_email, send_ticket_reply_email, send_ticket_status_email, validation_error, success_message, error_message, toast_success, toast_error
from django.core.paginator import Paginator
from dashboard.helper.pagination import get_page_range



# Create your views here.

# logout function
@require_POST
def logout_view(request):
    auth_logout(request)
    return redirect('/dashboard/auth/login/')

# login function
@never_cache
def login(request):

    if request.user.is_authenticated:
        return redirect('/dashboard/')
    
    error = None

    if request.method == "POST":
        form = LoginForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data["login_email"]
            password = form.cleaned_data["login_password"]
            remember = request.POST.get("remember")

            user = authenticate(request, username=email, password=password)

            if user is not None:
                auth_login(request, user)

                request.session.set_expiry(1209600 if remember else 0)

                next_url = request.POST.get("next")

                return redirect(next_url or "/dashboard/")
            else:
                error = "Invalid login details"
    else:
        form = LoginForm()

    response = render(request, "mainDash/authentication/login.html", {
        "form": form,
        "error": error
    })

    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    return response

def forgotPassword(request):
    return render(request, 'mainDash/authentication/forgetpassword.html');

def resetForgotPassword(request):
    return render(request, 'mainDash/authentication/resetpassword.html');


def index(request):
    return render(request, 'mainDash/index.html');

# fetch and show all contact request
def contact_page(request):
    search_query  = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')

    contacts = ContactMessage.objects.all().order_by('-created_at')

    if search_query:
        contacts = contacts.filter(
            Q(sender_email__icontains=search_query)   |
            Q(sender_subject__icontains=search_query) |
            Q(status__icontains=search_query)
        )

    if status_filter:
        contacts = contacts.filter(status=status_filter)

    paginator   = Paginator(contacts, 10)
    page_number = request.GET.get('page')
    page_obj    = paginator.get_page(page_number)

    # ← loop page_obj items, not the queryset
    for contact in page_obj:
        if contact.ticket and contact.ticket.pk:
            contact.ticket.token = encode_pk(contact.ticket.pk)

    query_params = request.GET.copy()
    if 'page' in query_params:
        query_params.pop('page')

    context = {
        'contacts':      page_obj,
        'page_range':    get_page_range(page_obj),
        'search_query':  search_query,
        'status_filter': status_filter,
        'query_string':  query_params.urlencode(),
    }
    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/contact_request_dataTable.html', context)
    return render(request, 'mainDash/contact_request.html', context)

# fetch all quote request
def quote_request(request):

    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')

    quote_requests = QuoteRequest.objects.all().order_by('-created_at')
     # FILTER LOGIC
    if search_query:
        quote_requests = quote_requests.filter(
            Q(quote_email__icontains=search_query) |
            Q(quote_name__icontains=search_query) |
            Q(quote_phone__icontains=search_query) 
        )

    # STATUS FILTER
    if status_filter:
        quote_requests = quote_requests.filter(
            status=status_filter
        )
    # with pagination
    paginator = Paginator(quote_requests, 10)  # 10 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # build query string without page
    query_params = request.GET.copy()
    if 'page' in query_params:
        query_params.pop('page')

    query_string = query_params.urlencode()

    return render(request, 'mainDash/quote-request.html', {
    'quote_request': page_obj,
    'page_range': get_page_range(page_obj),
    'search_query': search_query,
    'status_filter': status_filter,
    'query_string': query_string,
    }); 
 
# fetch and show deleted quote request
def quote_message(request, uuid):
    try:
        quote = QuoteRequest.objects.get(uuid=uuid)
    except QuoteRequest.DoesNotExist:
        return render(request, "mainDash/error_pages/not_found.html", status=404)
    return render(request, 'mainDash/innerPages/quote-message.html', {"quote": quote});

# update quote request status
def update_quote_status(request, uuid, status):
    
    quote = get_object_or_404(QuoteRequest, uuid=uuid)
    next_url = request.GET.get('next') or request.META.get('HTTP_REFERER') or reverse("quote_request")

    try:
        if status in ['approved', 'rejected', 'deleted']:
            if quote.status != status:
                quote.status = status
                quote.updated_by = request.user
                quote.updated_by_username = request.user.email
                quote.updated_at = timezone.now()
                quote.save()
                
            if status == "deleted":
                alert_type = "danger"
            elif status == "rejected":
                alert_type = "warning"
            else:
                alert_type = "success"

            return toast_success(
                request,
                f'Quote request successfully marked as {status}.',
                alert_type=alert_type,
                redirect_url=next_url
            )
             
        else:
            # messages.error(request, 'Invalid status action.')
            return toast_error(
                request, "Invalid status action",
                alert_type="danger"
                )

    except Exception as e:
        print(e)
        # messages.error(request, f'Error: {str(e)}')
        return error_message(
                request, "Sorry, an error occurred while processing your request! Try again",
                alert_type="danger"
                )

    # return redirect('quote_request')

# view deleted quote message details
def viewQuoteDetails(request, uuid):
    
    try:
        quoteDetails = QuoteRequest.objects.get(uuid=uuid)
    except QuoteRequest.DoesNotExist:
        return render(request, "mainDash/error_pages/not_found.html", status=404)
    return render(request, 'mainDash/innerPages/quoteDetails_message.html', {"quote": quoteDetails});

# fetch deleted quotes only
def deletedQuote_request(request):

    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')

    quoteDelete = QuoteRequest.objects.filter(
    status=QuoteRequest.STATUS_DELETED).order_by('-created_at')

    # FILTER LOGIC
    if search_query:
        quoteDelete = quoteDelete.filter(
            Q(quote_email__icontains=search_query) |
            Q(quote_name__icontains=search_query) |
            Q(quote_phone__icontains=search_query)
        )

    # STATUS FILTER
    if status_filter:
        quoteDelete = quoteDelete.filter(
            status=status_filter
        )
    # with pagination
    paginator = Paginator(quoteDelete, 10)  # 10 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # build query string without page
    query_params = request.GET.copy()
    if 'page' in query_params:
        query_params.pop('page')

    query_string = query_params.urlencode()

    context = {
        'quoteDelete_request': page_obj,
        'page_range': get_page_range(page_obj),
        'search_query': search_query,
        'status_filter': status_filter,
        'query_string': query_string,
    }
    return render(request, 'mainDash/deletedQuote-request.html', context);

# get and show pending quotes
def pendingQuote_request(request):

    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')

    pendingQuote = QuoteRequest.objects.filter(
    status=QuoteRequest.STATUS_PENDING).order_by('-created_at')

    # FILTER LOGIC
    if search_query:
        pendingQuote = pendingQuote.filter(
            Q(quote_email__icontains=search_query) |
            Q(quote_name__icontains=search_query) |
            Q(quote_phone__icontains=search_query)
        )

    # STATUS FILTER
    if status_filter:
        pendingQuote = pendingQuote.filter(
            status=status_filter
        )

    # with pagination
    paginator = Paginator(pendingQuote, 10)  # 10 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # build query string without page
    query_params = request.GET.copy()
    if 'page' in query_params:
        query_params.pop('page')

    query_string = query_params.urlencode()
    
    context = {
        'quotePending_request': page_obj,
        'page_range': get_page_range(page_obj),
        'search_query': search_query,
        'status_filter': status_filter,
        'query_string': query_string,
    }
    return render(request, 'mainDash/pendingQuote-request.html', context);

# fetch and show approved quote request
def approvedQuote_request(request):

    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')

    approvedQuote = QuoteRequest.objects.filter(
    status=QuoteRequest.STATUS_APPROVED).order_by('-created_at')
    # FILTER LOGIC
    if search_query:
        approvedQuote = approvedQuote.filter(
            Q(quote_email__icontains=search_query) |
            Q(quote_name__icontains=search_query) |
            Q(quote_phone__icontains=search_query)
        )

    # STATUS FILTER
    if status_filter:
        approvedQuote = approvedQuote.filter(
            status=status_filter
        )
    # with pagination
    paginator = Paginator(approvedQuote, 10)  # 10 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # build query string without page
    query_params = request.GET.copy()
    if 'page' in query_params:
        query_params.pop('page')

    query_string = query_params.urlencode()

    context = {
        'quoteApproved_request': page_obj,
        'page_range': get_page_range(page_obj),
        'search_query': search_query,
        'status_filter': status_filter,
        'query_string': query_string,
    }
    return render(request, 'mainDash/approvedQuote_request.html', context);

# fetch and show rejected quote request
def rejectedQuote_request(request):

    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')

    quoteRejected = QuoteRequest.objects.filter(
    status=QuoteRequest.STATUS_REJECTED).order_by('-created_at')

    # FILTER LOGIC
    if search_query:
        quoteRejected = quoteRejected.filter(
            Q(quote_email__icontains=search_query) |
            Q(quote_name__icontains=search_query) |
            Q(quote_phone__icontains=search_query)
        )

    # STATUS FILTER
    if status_filter:
        quoteRejected = quoteRejected.filter(
            status=status_filter
        )
    # with pagination
    paginator = Paginator(quoteRejected, 10)  # 10 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    # build query string without page
    query_params = request.GET.copy()
    if 'page' in query_params:
        query_params.pop('page')

    query_string = query_params.urlencode()

    context = {
        'quoteRejected_request': page_obj,
        'page_range': get_page_range(page_obj),
        'search_query': search_query,
        'status_filter': status_filter,
        'query_string': query_string,
    }
    return render(request, 'mainDash/rejectedQuote_request.html', context);

# fetch and show all orders
def order_list(request):

    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')

    orders_details = Order.objects.all().order_by('-created_at')

    # FILTER LOGIC
    if search_query:
        orders_details = orders_details.filter(
            Q(order_number__icontains=search_query) |
            Q(tracking_number__icontains=search_query) |
            Q(customer_email__icontains=search_query)|
            Q(customer_phone__icontains=search_query) 
        )

    # STATUS FILTER
    if status_filter:
        orders_details = orders_details.filter(
            status=status_filter
        )
    # with pagination
    paginator = Paginator(orders_details, 10)  # 10 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # build query string without page
    query_params = request.GET.copy()
    if 'page' in query_params:
        query_params.pop('page')

    query_string = query_params.urlencode()

    order_context = {
        'orders_details_request': page_obj,
        'page_range': get_page_range(page_obj),
        'search_query': search_query,
        'status_filter': status_filter,
        'query_string': query_string,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/orderShipment_dataTable.html', order_context)

    return render(request,'mainDash/order_shipment.html', order_context)

# create new function goes here

def createNew_order(request):

    orders_type = OrderType.objects.all().order_by('-name')
    orders_category = Category.objects.all().order_by('-name')

    next_url = request.GET.get('next') or request.META.get('HTTP_REFERER') or reverse("order_list")

    if request.method == 'POST':
        errors = []
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.created_by = request.user
            order.status = Order.STATUS_NEW

            # --- Promo code ---
            code_str         = request.POST.get('promo_code_input', '').strip()
            discount_amount  = 0

            if code_str:
                promo, discount, error = apply_promo_code(code_str, float(order.shipping_cost))
                if not error:
                    order.promo_code      = promo
                    order.discount_amount = discount
                    discount_amount       = discount
                    promo.used_count     += 1
                    promo.save(update_fields=['used_count'])

            order.total_amount = max(0, float(order.shipping_cost) - discount_amount)
            order.save()

            log_activity(
            user=request.user,
            action='created',
            model_name='Order',
            object_repr=order.order_number,
            description=f"Created order '{order.order_number}'.",
        )

            return toast_success(
                request,
                f'Order {order.order_number} created successfully!',
                alert_type="success",
                redirect_url=next_url
            )
        
        # Build OOB field errors and attach to the toast response
        oob_html = render_form_errors_oob(
            request, form, countries, orders_type, orders_category
        )
       
        return toast_error(
            request,
            "Invalid form data. Please check your inputs.",
            alert_type="danger",
            oob_content=oob_html,
        )

    form = OrderForm()

    return render(request, 'mainDash/createOrder_shipment.html', 
        {
        'form': form,
        'countries': countries,
        'ship_type': orders_type,
        'ship_category': orders_category
        });


# order details page fetch by id, tracking id uuid
def viewOrderDetail(request, uuid):
    order = get_object_or_404(Order, uuid=uuid)
    return render(request, 'mainDash/order_detailsPage.html', {
        'order': order
    })

# edit/update order details
def order_edit(request, uuid):
    order = get_object_or_404(Order, uuid=uuid)
 
    orders_type = OrderType.objects.all().order_by('-name')
    orders_category = Category.objects.all().order_by('-name')
 
    next_url = reverse("order_list")
 
    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            updated_order = form.save(commit=False)
            updated_order.updated_by = request.user
            # status is excluded from OrderForm, handle separately
            posted_status = request.POST.get('status')
            if posted_status:
                updated_order.status = posted_status
                # --- Promo code ---
                code_str = request.POST.get('promo_code_input', '').strip()

                # If promo changed or newly applied
                if code_str and (not updated_order.promo_code or updated_order.promo_code.code != code_str.upper()):
                    promo, discount, error = apply_promo_code(code_str, float(updated_order.shipping_cost))
                    if not error:
                        # Decrement old code if swapping
                        if updated_order.promo_code:
                            old_promo             = updated_order.promo_code
                            old_promo.used_count  = max(0, old_promo.used_count - 1)
                            old_promo.save(update_fields=['used_count'])

                        updated_order.promo_code      = promo
                        updated_order.discount_amount = discount
                        promo.used_count     += 1
                        promo.save(update_fields=['used_count'])

                # If code cleared
                if not code_str and updated_order.promo_code:
                    old_promo             = updated_order.promo_code
                    old_promo.used_count  = max(0, old_promo.used_count - 1)
                    old_promo.save(update_fields=['used_count'])
                    updated_order.promo_code      = None
                    updated_order.discount_amount = 0

                updated_order.total_amount = max(0, float(updated_order.shipping_cost) - float(updated_order.discount_amount))
                updated_order.save()

                log_activity(
                user=request.user,
                action='updated',
                model_name='Order',
                object_repr=updated_order.order_number,
                description=f"Updated order '{updated_order.order_number}'.",
            )
 
            return toast_success(
                request,
                f'Order {updated_order.order_number} updated successfully!',
                alert_type="success",
                redirect_url=next_url
            )
 
        oob_html = render_form_errors_oob(
            request, form, countries, orders_type, orders_category
        )
 
        return toast_error(
            request,
            "Invalid form data. Please check your inputs.",
            alert_type="danger",
            oob_content=oob_html,
        )
 
    form = OrderForm(instance=order)
 
    return render(request, 'mainDash/order_editPage.html', {
        'form': form,
        'order': order,
        'countries': countries,
        'ship_type': orders_type,
        'ship_category': orders_category,
    })
 

# order image upload
@require_POST
def order_image_upload(request, uuid):
    time.sleep(2)
    order = get_object_or_404(Order, uuid=uuid)
 
    files = request.FILES.getlist('images')
    if not files:
        return JsonResponse({'success': False, 'error': 'No files received.'}, status=400)
 
    created = []
    for f in files:
        # basic safety: only accept actual images, cap size at 8MB
        if not f.content_type.startswith('image/'):
            continue
        if f.size > 8 * 1024 * 1024:
            continue
 
        img = OrderImage.objects.create(
            order=order,
            image=f,
            uploaded_by=request.user,
        )
        created.append({
            'id': img.id,
            'url': img.image.url,
            'uploaded_at': img.uploaded_at.strftime('%d/%m/%Y %H:%M'),
        })
 
    if not created:
        return JsonResponse({'success': False, 'error': 'No valid images were uploaded.'}, status=400)
 
    return JsonResponse({'success': True, 'images': created})
 
# delete the uploaded image
@require_POST
def order_image_delete(request, image_id):
    image = get_object_or_404(OrderImage, id=image_id)
    image.image.delete(save=False)
    image.delete()
    return JsonResponse({'success': True})
 

# fetch and show all cancelled orders request
def orderCancelled_list(request):

    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')

    orders_details = Order.objects.filter(
    status=Order.STATUS_CANCELLED).order_by('-created_at')

    # FILTER LOGIC
    if search_query:
        orders_details = orders_details.filter(
            Q(order_number__icontains=search_query) |
            Q(tracking_number__icontains=search_query) |
            Q(customer_email__icontains=search_query)|
            Q(customer_phone__icontains=search_query) 
        )

    # STATUS FILTER
    if status_filter:
        orders_details = orders_details.filter(
            status=status_filter
        )
    # with pagination
    paginator = Paginator(orders_details, 10)  # 10 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # build query string without page
    query_params = request.GET.copy()
    if 'page' in query_params:
        query_params.pop('page')

    query_string = query_params.urlencode()

    order_context = {
        'orders_details_request': page_obj,
        'page_range': get_page_range(page_obj),
        'search_query': search_query,
        'status_filter': status_filter,
        'query_string': query_string,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/orderShipmentCancelled_dataTable.html', order_context)

    return render(request,'mainDash/order_shipmentCancelled.html', order_context)


# fetch and show all completed orders request
def orderCompleted_list(request):

    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')

    orders_details = Order.objects.filter(
    status=Order.STATUS_COMPLETED).order_by('-created_at')

    # FILTER LOGIC
    if search_query:
        orders_details = orders_details.filter(
            Q(order_number__icontains=search_query) |
            Q(tracking_number__icontains=search_query) |
            Q(customer_email__icontains=search_query)|
            Q(customer_phone__icontains=search_query) 
        )

    # STATUS FILTER
    if status_filter:
        orders_details = orders_details.filter(
            status=status_filter
        )
    # with pagination
    paginator = Paginator(orders_details, 10)  # 10 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # build query string without page
    query_params = request.GET.copy()
    if 'page' in query_params:
        query_params.pop('page')

    query_string = query_params.urlencode()

    order_context = {
        'orders_details_request': page_obj,
        'page_range': get_page_range(page_obj),
        'search_query': search_query,
        'status_filter': status_filter,
        'query_string': query_string,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/orderShipmentCompleted_dataTable.html', order_context)

    return render(request,'mainDash/order_shipmentCompleted.html', order_context)

# fetch and show all deleted orders request
def orderDeleted_list(request):

    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')

    orders_details = Order.objects.filter(
    status=Order.STATUS_DELETED).order_by('-created_at')

    # FILTER LOGIC
    if search_query:
        orders_details = orders_details.filter(
            Q(order_number__icontains=search_query) |
            Q(tracking_number__icontains=search_query) |
            Q(customer_email__icontains=search_query)|
            Q(customer_phone__icontains=search_query) 
        )

    # STATUS FILTER
    if status_filter:
        orders_details = orders_details.filter(
            status=status_filter
        )
    # with pagination
    paginator = Paginator(orders_details, 10)  # 10 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # build query string without page
    query_params = request.GET.copy()
    if 'page' in query_params:
        query_params.pop('page')

    query_string = query_params.urlencode()

    order_context = {
        'orders_details_request': page_obj,
        'page_range': get_page_range(page_obj),
        'search_query': search_query,
        'status_filter': status_filter,
        'query_string': query_string,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/orderShipmentCompleted_dataTable.html', order_context)

    return render(request,'mainDash/order_shipmentCompleted.html', order_context)

# fetch and show all in-transit orders request
def orderIn_transit_list(request):

    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')

    orders_details = Order.objects.filter(
    status=Order.STATUS_IN_TRANSIT).order_by('-created_at')

    # FILTER LOGIC
    if search_query:
        orders_details = orders_details.filter(
            Q(order_number__icontains=search_query) |
            Q(tracking_number__icontains=search_query) |
            Q(customer_email__icontains=search_query)|
            Q(customer_phone__icontains=search_query) 
        )

    # STATUS FILTER
    if status_filter:
        orders_details = orders_details.filter(
            status=status_filter
        )
    # with pagination
    paginator = Paginator(orders_details, 10)  # 10 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # build query string without page
    query_params = request.GET.copy()
    if 'page' in query_params:
        query_params.pop('page')

    query_string = query_params.urlencode()

    order_context = {
        'orders_details_request': page_obj,
        'page_range': get_page_range(page_obj),
        'search_query': search_query,
        'status_filter': status_filter,
        'query_string': query_string,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/orderShipmentIntransit_dataTable.html', order_context)

    return render(request,'mainDash/order_shipmentIntransit.html', order_context)

# fetch and show all processing orders request
def orderProcessing_list(request):

    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')

    orders_details = Order.objects.filter(
    status=Order.STATUS_PROCESSING).order_by('-created_at')

    # FILTER LOGIC
    if search_query:
        orders_details = orders_details.filter(
            Q(order_number__icontains=search_query) |
            Q(tracking_number__icontains=search_query) |
            Q(customer_email__icontains=search_query)|
            Q(customer_phone__icontains=search_query) 
        )

    # STATUS FILTER
    if status_filter:
        orders_details = orders_details.filter(
            status=status_filter
        )
    # with pagination
    paginator = Paginator(orders_details, 10)  # 10 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # build query string without page
    query_params = request.GET.copy()
    if 'page' in query_params:
        query_params.pop('page')

    query_string = query_params.urlencode()

    order_context = {
        'orders_details_request': page_obj,
        'page_range': get_page_range(page_obj),
        'search_query': search_query,
        'status_filter': status_filter,
        'query_string': query_string,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/orderShipmentProcessing_dataTable.html', order_context)

    return render(request,'mainDash/order_shipmentProcessing.html', order_context)


# fetch and show all rejected orders request
def orderReturned_list(request):

    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')

    orders_details = Order.objects.filter(
    status=Order.STATUS_RETURNED).order_by('-created_at')

    # FILTER LOGIC
    if search_query:
        orders_details = orders_details.filter(
            Q(order_number__icontains=search_query) |
            Q(tracking_number__icontains=search_query) |
            Q(customer_email__icontains=search_query)|
            Q(customer_phone__icontains=search_query) 
        )

    # STATUS FILTER
    if status_filter:
        orders_details = orders_details.filter(
            status=status_filter
        )
    # with pagination
    paginator = Paginator(orders_details, 10)  # 10 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # build query string without page
    query_params = request.GET.copy()
    if 'page' in query_params:
        query_params.pop('page')

    query_string = query_params.urlencode()

    order_context = {
        'orders_details_request': page_obj,
        'page_range': get_page_range(page_obj),
        'search_query': search_query,
        'status_filter': status_filter,
        'query_string': query_string,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/orderShipmentReturn_dataTable.html', order_context)

    return render(request,'mainDash/order_shipmentReturn.html', order_context)

# shipment view goes here

def shipment_list(request, status=None):
    shipments = Shipment.objects.select_related('order').all()

    status_filter = request.GET.get('status', status or '')
    if status_filter:
        shipments = shipments.filter(status=status_filter)

    search_query = request.GET.get('search', '')
    if search_query:
        shipments = shipments.filter(
            models.Q(shipment_number__icontains=search_query) |
            models.Q(order__order_number__icontains=search_query) |
            models.Q(order__customer_email__icontains=search_query) |
            models.Q(order__customer_phone__icontains=search_query) |
            models.Q(order__tracking_number__icontains=search_query)
        )

    paginator = Paginator(shipments, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'shipments_details_request': page_obj,
        'status_filter': status_filter,
        'search_query': search_query,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/shipment_dataTable.html', context)
    return render(request, 'mainDash/shipment_page.html', context)


def shipment_create(request):
    next_url = request.GET.get('next', '')

    if request.method == 'POST':
        form = ShipmentCreateForm(request.POST)
        if form.is_valid():
            shipment = form.save(commit=False)
            shipment.created_by = request.user
            shipment.save()

            log_activity(
            user=request.user,
            action='created',
            model_name='Shipment',
            object_repr=shipment.shipment_number,
            description=f"Created shipment '{shipment.shipment_number}'.",
            )
            return toast_success(
                request,
                f'Shipment {shipment.shipment_number} created successfully!',
                alert_type="success",
                redirect_url=next_url or f"/dashboard/shipments/{shipment.uuid}/",
            )
        else:
            oob_html = render_form_errors_oob(form)  # adjust if your helper signature differs
            return toast_error(
                request,
                "Invalid form data. Please check your inputs.",
                alert_type="danger",
                oob_content=oob_html,
            )

    eligible_orders = Order.objects.filter(status=Order.STATUS_PROCESSING)
    return render(request, 'mainDash/create_shipment.html', {
        'form': form if request.method == 'POST' else ShipmentCreateForm(),
        'eligible_orders': eligible_orders,
    })


def order_summary_partial(request, order_uuid):
    order = get_object_or_404(Order, uuid=order_uuid)
    return render(request, 'mainDash/includes/order_summary_card.html', {'order': order})


def shipment_detail(request, uuid):
    shipment = get_object_or_404(Shipment.objects.select_related('order'), uuid=uuid)
    next_statuses = Shipment.ALLOWED_TRANSITIONS.get(shipment.status, set())
    status_form = ShipmentStatusChangeForm(allowed_statuses=next_statuses)

    return render(request, 'mainDash/shipment_detailsPage.html', {
        'shipment': shipment,
        'order': shipment.order,
        'tracking_events': shipment.tracking_events.all(),
         'order_images': shipment.order.images.all(),
        'status_form': status_form,
        'has_next_status': bool(next_statuses),
    })

def shipment_change_status(request, uuid):
    shipment = get_object_or_404(Shipment, uuid=uuid)
    next_statuses = Shipment.ALLOWED_TRANSITIONS.get(shipment.status, set())

    if request.method == 'POST':
        form = ShipmentStatusChangeForm(request.POST, allowed_statuses=next_statuses)
        if form.is_valid():
            try:
                transition_shipment_status(
                    shipment=shipment,
                    new_status=form.cleaned_data['status'],
                    user=request.user,
                    location=form.cleaned_data['location'],
                    description=form.cleaned_data['description'],
                )

                log_activity(
                user=request.user,
                action='updated',
                model_name='Shipment',
                object_repr=shipment.shipment_number,
                description=f"Changed shipment '{shipment.shipment_number}' status to '{shipment.get_status_display()}'.",
                )
                return toast_success(
                    request,
                    f'Shipment marked as {shipment.get_status_display()}.',
                    alert_type="success",
                    redirect_url=f"/dashboard/shipments/{shipment.uuid}/",
                )
            except ShipmentTransitionError as exc:
                return toast_error(
                    request,
                    str(exc),
                    alert_type="danger",
                )
        else:
            return toast_error(
                request,
                "Invalid status selected.",
                alert_type="danger",
            )

    return toast_error(request, "Invalid request method.", alert_type="danger")


# fleet management views
# ---------- All Vehicles ----------

def vehicle_list(request):
    vehicles = Vehicle.objects.all()

    ownership_filter = request.GET.get('ownership', '')
    if ownership_filter:
        vehicles = vehicles.filter(ownership_type=ownership_filter)

    status_filter = request.GET.get('status', '')
    if status_filter:
        vehicles = vehicles.filter(status=status_filter)

    search_query = request.GET.get('search', '')
    if search_query:
        vehicles = vehicles.filter(
            models.Q(name__icontains=search_query) |
            models.Q(license_plate__icontains=search_query) |
            models.Q(carrier_company_name__icontains=search_query)
        )

    paginator = Paginator(vehicles, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'vehicles_page': page_obj,
        'ownership_filter': ownership_filter,
        'status_filter': status_filter,
        'search_query': search_query,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/vehicle_dataTable.html', context)
    return render(request, 'mainDash/vehicle_page.html', context)


def vehicle_create(request):
    
    if request.method == 'POST':
        form = VehicleForm(request.POST)
        if form.is_valid():
            vehicle = form.save(commit=False)
            vehicle.created_by = request.user
            vehicle.save()

            log_activity(
            user=request.user,
            action='created',
            model_name='Vehicle',
            object_repr=vehicle.name,
            description=f"Added vehicle '{vehicle.name}' ({vehicle.license_plate}).",
            )
            return toast_success(
                request,
                f'Vehicle "{vehicle.name}" added successfully!',
                alert_type="success",
                redirect_url="/dashboard/fleet/vehicles/",
            )
        oob_html = render_form_errors_oob(form)
        return toast_error(request, "Invalid form data. Please check your inputs.", alert_type="danger", oob_content=oob_html)

    return render(request, 'mainDash/create_vehicle.html', {'form': VehicleForm()})


def vehicle_detail(request, uuid):
    vehicle = get_object_or_404(Vehicle, uuid=uuid)
    return render(request, 'mainDash/vehicle_detailsPage.html', {
        'vehicle': vehicle,
        'maintenance_records': vehicle.maintenance_records.all()[:5],
        'fuel_records': vehicle.fuel_records.all()[:5],
    })

def vehicle_detail(request, uuid):
    vehicle = get_object_or_404(
        Vehicle.objects.prefetch_related(
            Prefetch('maintenance_records', queryset=VehicleMaintenanceRecord.objects.order_by('-service_date')),
            Prefetch('fuel_records', queryset=FuelRecord.objects.order_by('-fuel_date')),
        ),
        uuid=uuid
    )
    return render(request, 'mainDash/vehicle_detailsPage.html', {
        'vehicle': vehicle,
        'maintenance_records': vehicle.maintenance_records.all()[:5],
        'fuel_records': vehicle.fuel_records.all()[:5],
    })


def vehicle_edit(request, uuid):
    
    vehicle = get_object_or_404(Vehicle, uuid=uuid)
    if request.method == 'POST':
        form = VehicleForm(request.POST, instance=vehicle)
        if form.is_valid():
            form.save()

            log_activity(
            user=request.user,
            action='updated',
            model_name='Vehicle',
            object_repr=vehicle.name,
            description=f"Updated vehicle '{vehicle.name}' ({vehicle.license_plate}).",
            )
            
            return toast_success(request, f'Vehicle "{vehicle.name}" was updated.', alert_type="success", redirect_url=f"/dashboard/fleet/vehicles/{vehicle.uuid}/")
        oob_html = render_form_errors_oob(form)
        return toast_error(request, "Invalid form data.", alert_type="danger", oob_content=oob_html)

    return render(request, 'mainDash/vehicle_editPage.html', {'form': VehicleForm(instance=vehicle), 'vehicle': vehicle})


@require_POST
def vehicle_delete(request, pk):
    from django.http import JsonResponse
    vehicle = get_object_or_404(Vehicle, pk=pk)
    
    log_activity(
        user=request.user,
        action='deleted',
        model_name='Vehicle',
        object_repr=vehicle.name,
        description=f"Deleted vehicle '{vehicle.name}' ({vehicle.license_plate}).",
    )

    vehicle.delete()
    return JsonResponse({'success': True})

# ---------- Vehicle Maintenance ----------

def maintenance_list(request):
    records = VehicleMaintenanceRecord.objects.select_related('vehicle').all()

    vehicle_filter = request.GET.get('vehicle', '')
    if vehicle_filter:
        records = records.filter(vehicle_id=vehicle_filter)

    search_query = request.GET.get('search', '')
    if search_query:
        records = records.filter(
            models.Q(service_type__icontains=search_query) |
            models.Q(vehicle__name__icontains=search_query)
        )

    paginator = Paginator(records, 8)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'records_page': page_obj,
        'search_query': search_query,
        'vehicle_filter': vehicle_filter,
        'vehicles': Vehicle.objects.all(),
        'today': timezone.now().date(),  # add this
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/maintenance_dataTable.html', context)
    return render(request, 'mainDash/maintenance_page.html', context)


def maintenance_create(request):
    if request.method == 'POST':
        form = MaintenanceRecordForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.created_by = request.user
            record.save()

            log_activity(
            user=request.user,
            action='created',
            model_name='VehicleMaintenanceRecord',
            object_repr=str(record),
            description=f"Added maintenance record for vehicle '{record.vehicle.name}' — {record.service_type}.",
            )
            
            return toast_success(request, 'Maintenance record added.', alert_type="success", redirect_url="/dashboard/fleet/maintenance/")
        oob_html = render_form_errors_oob(form)
        return toast_error(request, "Invalid form data.", alert_type="danger", oob_content=oob_html)

    return render(request, 'mainDash/create_maintenance.html', {'form': MaintenanceRecordForm()})


@require_POST
def maintenance_delete(request, pk):
    record = get_object_or_404(VehicleMaintenanceRecord, pk=pk)
    log_activity(
        user=request.user,
        action='deleted',
        model_name='VehicleMaintenanceRecord',
        object_repr=str(record),
        description=f"Deleted maintenance record for vehicle '{record.vehicle.name}'.",
    )

    record.delete()
    return JsonResponse({'success': True})


# ---------- Fuel Records ----------

def fuel_list(request):
    records = FuelRecord.objects.select_related('vehicle').all()

    vehicle_filter = request.GET.get('vehicle', '')
    if vehicle_filter:
        records = records.filter(vehicle_id=vehicle_filter)

    paginator = Paginator(records, 8)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {'records_page': page_obj, 'vehicle_filter': vehicle_filter, 'vehicles': Vehicle.objects.all()}

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/fuelRecord_dataTable.html', context)
    return render(request, 'mainDash/fuelRecord_page.html', context)


def fuel_create(request):
    if request.method == 'POST':
        form = FuelRecordForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.created_by = request.user
            record.save()

            log_activity(
            user=request.user,
            action='created',
            model_name='FuelRecord',
            object_repr=str(record),
            description=f"Added fuel record for vehicle '{record.vehicle.name}'.",
            )
            
            return toast_success(request, 'Fuel record added.', alert_type="success", redirect_url="/dashboard/fleet/fuel/")
        oob_html = render_form_errors_oob(form)
        return toast_error(request, "Invalid form data.", alert_type="danger", oob_content=oob_html)

    return render(request, 'mainDash/create_fuelRecords.html', {'form': FuelRecordForm()})


@require_POST
def fuel_delete(request, pk):
    record = get_object_or_404(FuelRecord, pk=pk)

    log_activity(
        user=request.user,
        action='deleted',
        model_name='FuelRecord',
        object_repr=str(record),
        description=f"Deleted fuel record for vehicle '{record.vehicle.name}'.",
    )

    record.delete()
    return JsonResponse({'success': True})


# ---------- Route Planning ----------

def route_list(request):
    routes = Route.objects.select_related('vehicle').all()

    status_filter = request.GET.get('status', '')
    if status_filter:
        routes = routes.filter(status=status_filter)

    paginator = Paginator(routes, 8)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {'routes_page': page_obj, 'status_filter': status_filter}

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/routeFleet_table.html', context)
    return render(request, 'mainDash/routeFleet_page.html', context)


def route_create(request):
    if request.method == 'POST':
        form = RouteForm(request.POST)
        if form.is_valid():
            route = form.save(commit=False)
            route.created_by = request.user
            route.save()

            log_activity(
            user=request.user,
            action='created',
            model_name='Route',
            object_repr=route.route_name,
            description=f"Created route '{route.route_name}'.",
            )
            return toast_success(request, f'Route "{route.route_name}" created.', alert_type="success", redirect_url="/dashboard/fleet/routes/")
        oob_html = render_form_errors_oob(form)
        return toast_error(request, "Invalid form data.", alert_type="danger", oob_content=oob_html)

    return render(request, 'mainDash/create_routeFleet.html', {'form': RouteForm()})


# def route_detail(request, uuid):
#     route = get_object_or_404(Route.objects.select_related('vehicle'), uuid=uuid)
#     return render(request, 'mainDash/fleet/route_detail.html', {'route': route})

def route_detail(request, uuid):
    route = get_object_or_404(Route.objects.select_related('vehicle'), uuid=uuid)

    if request.method == 'POST' and request.POST.get('_status_update'):
        new_status = request.POST.get('status')
        if new_status in dict(Route.STATUS_CHOICES):
            route.status = new_status
            route.save()
            return toast_success(request, f'Route status updated to "{route.get_status_display()}".', alert_type="success")

    return render(request, 'mainDash/routeFleet_detailsPage.html', {'route': route})

@require_POST
def route_delete(request, pk):
    route = get_object_or_404(Route, pk=pk)

    log_activity(
        user=request.user,
        action='deleted',
        model_name='Route',
        object_repr=route.route_name,
        description=f"Deleted route '{route.route_name}'.",
    )

    route.delete()
    return JsonResponse({'success': True})


# ---------- Fleet Reports ----------

def fleet_reports(request):
    from django.db.models import Sum, Count
    from django.utils import timezone
    from datetime import timedelta

    thirty_days_ago = timezone.now().date() - timedelta(days=30)

    fuel_cost = FuelRecord.objects.filter(fuel_date__gte=thirty_days_ago).aggregate(total=Sum('cost'))['total'] or 0
    maintenance_cost = VehicleMaintenanceRecord.objects.filter(service_date__gte=thirty_days_ago).aggregate(total=Sum('cost'))['total'] or 0

    context = {
        'total_vehicles': Vehicle.objects.count(),
        'in_house_count': Vehicle.objects.filter(ownership_type=Vehicle.OWNERSHIP_IN_HOUSE).count(),
        'third_party_count': Vehicle.objects.filter(ownership_type=Vehicle.OWNERSHIP_THIRD_PARTY).count(),
        'available_count': Vehicle.objects.filter(status=Vehicle.STATUS_AVAILABLE).count(),
        'on_route_count': Vehicle.objects.filter(status=Vehicle.STATUS_ON_ROUTE).count(),
        'vehicles_in_maintenance': Vehicle.objects.filter(status=Vehicle.STATUS_MAINTENANCE).count(),
        'out_of_service_count': Vehicle.objects.filter(status=Vehicle.STATUS_OUT_OF_SERVICE).count(),
        'fuel_cost': fuel_cost,
        'maintenance_cost': maintenance_cost,
        'total_cost': fuel_cost + maintenance_cost,
        'planned_routes': Route.objects.filter(status=Route.STATUS_PLANNED).count(),
        'active_routes': Route.objects.filter(status=Route.STATUS_ACTIVE).count(),
        'completed_routes': Route.objects.filter(status=Route.STATUS_COMPLETED).count(),
        'cancelled_routes': Route.objects.filter(status=Route.STATUS_CANCELLED).count(),
    }
    return render(request, 'mainDash/fleetReport_page.html', context)


# fleet cost summary query
def fleet_reports_cost(request):
    from django.db.models import Sum
    from django.utils import timezone
    from datetime import timedelta

    period = request.GET.get('period', '30')
    today = timezone.now().date()

    if period == 'today':
        from_date = today
    else:
        from_date = today - timedelta(days=int(period))

    fuel_cost = FuelRecord.objects.filter(fuel_date__gte=from_date).aggregate(total=Sum('cost'))['total'] or 0
    maintenance_cost = VehicleMaintenanceRecord.objects.filter(service_date__gte=from_date).aggregate(total=Sum('cost'))['total'] or 0

    return render(request, 'mainDash/includes/fleetCost_summary.html', {
        'fuel_cost': fuel_cost,
        'maintenance_cost': maintenance_cost,
        'total_cost': fuel_cost + maintenance_cost,
    })


# ============================================================
# WAREHOUSE MANAGEMENT
# ============================================================
# ---------- Warehouses ----------

def warehouse_list(request):
    warehouses = Warehouse.objects.all()

    search_query = request.GET.get('search', '')
    if search_query:
        warehouses = warehouses.filter(
            Q(name__icontains=search_query) |
            Q(city__icontains=search_query) |
            Q(country__icontains=search_query)
        )

    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        warehouses = warehouses.filter(is_active=True)
    elif status_filter == 'inactive':
        warehouses = warehouses.filter(is_active=False)

    paginator = Paginator(warehouses, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'warehouses_page': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/warehouse_dataTable.html', context)
    return render(request, 'mainDash/warehouse_page.html', context)


def warehouse_create(request):
    if request.method == 'POST':
        form = WarehouseForm(request.POST)
        if form.is_valid():
            warehouse = form.save(commit=False)
            warehouse.created_by = request.user
            warehouse.updated_by = request.user
            warehouse.save()

            log_activity(
            user=request.user,
            action='created',
            model_name='Warehouse',
            object_repr=warehouse.name,
            description=f"Created warehouse '{warehouse.name}' in {warehouse.city}, {warehouse.country}.",
            )
            return toast_success(request, f'Warehouse "{warehouse.name}" created successfully!', alert_type="success", redirect_url="/dashboard/warehouse/")
        oob_html = render_simple_form_errors_oob(form)
        return toast_error(request, "Please fix the errors below.", alert_type="danger", oob_content=oob_html)

    return render(request, 'mainDash/create_warehouse.html', {'form': WarehouseForm()})

def warehouse_detail(request, uuid):
    from django.db.models import Count, Q

    warehouse = get_object_or_404(
        Warehouse.objects.prefetch_related(
            Prefetch('items', queryset=WarehouseItem.objects.order_by('-created_at')),
            Prefetch('locations', queryset=StorageLocation.objects.order_by('zone', 'shelf')),
        ).annotate(
            total_items=Count('items'),
            in_stock=Count('items', filter=Q(items__status=WarehouseItem.STATUS_IN_STOCK)),
            dispatched=Count('items', filter=Q(items__status=WarehouseItem.STATUS_DISPATCHED)),
            on_hold=Count('items', filter=Q(items__status=WarehouseItem.STATUS_HELD)),
        ),
        uuid=uuid
    )

    return render(request, 'mainDash/warehouse_detailsPage.html', {
        'warehouse': warehouse,
        'recent_items': warehouse.items.all()[:5],
        'locations': warehouse.locations.all(),
        'total_items': warehouse.total_items,
        'in_stock': warehouse.in_stock,
        'dispatched': warehouse.dispatched,
        'on_hold': warehouse.on_hold,
    })

def warehouse_edit(request, uuid):
    warehouse = get_object_or_404(Warehouse, uuid=uuid)
    if request.method == 'POST':
        form = WarehouseForm(request.POST, instance=warehouse)
        if form.is_valid():
            w = form.save(commit=False)
            w.updated_by = request.user
            w.save()

            log_activity(
            user=request.user,
            action='updated',
            model_name='Warehouse',
            object_repr=warehouse.name,
            description=f"Updated warehouse '{warehouse.name}'.",
            )
            
            return toast_success(request, f'Warehouse "{warehouse.name}" updated.', alert_type="success", redirect_url=f"/dashboard/warehouse/{warehouse.uuid}/")
        oob_html = render_form_errors_oob(form)
        return toast_error(request, "Invalid form data.", alert_type="danger", oob_content=oob_html)

    return render(request, 'mainDash/warehouse_editPage.html', {'form': WarehouseForm(instance=warehouse), 'warehouse': warehouse})

@require_POST
def warehouse_delete(request, pk):
    warehouse = get_object_or_404(Warehouse, pk=pk)
    log_activity(
        user=request.user,
        action='deleted',
        model_name='Warehouse',
        object_repr=warehouse.name,
        description=f"Deleted warehouse '{warehouse.name}'.",
    )
    warehouse.delete()
    return JsonResponse({'success': True})

# ---------- Inventory ----------

def inventory_list(request):
    items = WarehouseItem.objects.select_related('warehouse', 'location').all()

    search_query = request.GET.get('search', '')
    if search_query:
        items = items.filter(
            Q(customer_name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(tracking_number__icontains=search_query) |
            Q(destination_country__icontains=search_query)
        )

    warehouse_filter = request.GET.get('warehouse', '')
    if warehouse_filter:
        items = items.filter(warehouse_id=warehouse_filter)

    status_filter = request.GET.get('status', '')
    if status_filter:
        items = items.filter(status=status_filter)

    category_filter = request.GET.get('category', '')
    if category_filter:
        items = items.filter(category=category_filter)

    paginator = Paginator(items, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'items_page': page_obj,
        'search_query': search_query,
        'warehouse_filter': warehouse_filter,
        'status_filter': status_filter,
        'category_filter': category_filter,
        'warehouses': Warehouse.objects.filter(is_active=True),
        'categories': WarehouseItem.CATEGORY_CHOICES,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/inventory_dataTable.html', context)
    return render(request, 'mainDash/inventory_page.html', context)

def inventory_create(request):
    if request.method == 'POST':
        form = WarehouseItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.created_by = request.user
            item.updated_by = request.user
            item.save()
            # auto log inbound movement
            StockMovement.objects.create(
                item=item,
                movement_type=StockMovement.MOVEMENT_IN,
                quantity=item.quantity,
                to_location=item.location,
                movement_date=item.received_date,
                reference=item.tracking_number,
                notes='Auto-logged on item creation.',
                created_by=request.user,
                updated_by=request.user,
            )

            log_activity(
            user=request.user,
            action='created',
            model_name='WarehouseItem',
            object_repr=item.customer_name,
            description=f"Added inventory item for '{item.customer_name}' (tracking: {item.tracking_number}).",
            )
            return toast_success(request, f'Item for "{item.customer_name}" added to inventory.', alert_type="success", redirect_url="/dashboard/warehouse/inventory/")
        oob_html = render_simple_form_errors_oob(form)
        return toast_error(request, "Please fix the required data errors below.", alert_type="danger", oob_content=oob_html)

    return render(request, 'mainDash/components/create_inventoryItem.html', {'form': WarehouseItemForm()})


def inventory_detail(request, uuid):
    item = get_object_or_404(
        WarehouseItem.objects.select_related('warehouse', 'location'),
        uuid=uuid
    )
    return render(request, 'mainDash/inventory_detailsPage.html', {
        'item': item,
        'movements': item.movements.select_related('from_location', 'to_location').all()[:10],
    })

# def inventory_edit(request, uuid):
#     item = get_object_or_404(WarehouseItem, uuid=uuid)
#     if request.method == 'POST':
#         form = WarehouseItemForm(request.POST, instance=item)
#         if form.is_valid():
#             i = form.save(commit=False)
#             i.updated_by = request.user
#             i.save()
#             return toast_success(request, f'Item updated successfully.', alert_type="success", redirect_url=f"/dashboard/warehouse/inventory/{item.uuid}/")
#         oob_html = render_form_errors_oob(form)
#         return toast_error(request, "Invalid form data.", alert_type="danger", oob_content=oob_html)

#     return render(request, 'mainDash/inventory_editPage.html', {'form': WarehouseItemForm(instance=item), 'item': item})

def inventory_edit(request, uuid):
    item = get_object_or_404(WarehouseItem, uuid=uuid)
    if request.method == 'POST':
        form = WarehouseItemForm(request.POST, instance=item)
        if form.is_valid():
            i = form.save(commit=False)
            i.updated_by = request.user
            i.save()

            log_activity(
            user=request.user,
            action='updated',
            model_name='WarehouseItem',
            object_repr=item.customer_name,
            description=f"Updated inventory item for '{item.customer_name}' (tracking: {item.tracking_number}).",
            )
            
            return toast_success(
                request,
                f'Item updated successfully.',
                alert_type="success",
                redirect_url=f"/dashboard/warehouse/inventory/{item.uuid}/"
            )
        oob_html = render_simple_form_errors_oob(form)
        return toast_error(request, "Please fix the errors below.", alert_type="danger", oob_content=oob_html)

    return render(request, 'mainDash/inventory_editPage.html', {
        'form': WarehouseItemForm(instance=item),
        'item': item,
    })


@require_POST
def inventory_delete(request, pk):
    item = get_object_or_404(WarehouseItem, pk=pk)
    log_activity(
        user=request.user,
        action='deleted',
        model_name='WarehouseItem',
        object_repr=item.customer_name,
        description=f"Deleted inventory item for '{item.customer_name}' (tracking: {item.tracking_number}).",
    )
    item.delete()
    return JsonResponse({'success': True})

# ---------- Stock Movement ----------

def stock_movement_list(request):
    movements = StockMovement.objects.select_related('item', 'item__warehouse', 'from_location', 'to_location').all()

    search_query = request.GET.get('search', '')
    if search_query:
        movements = movements.filter(
            Q(item__customer_name__icontains=search_query) |
            Q(reference__icontains=search_query) |
            Q(item__tracking_number__icontains=search_query)
        )

    movement_filter = request.GET.get('movement_type', '')
    if movement_filter:
        movements = movements.filter(movement_type=movement_filter)

    paginator = Paginator(movements, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'movements_page': page_obj,
        'search_query': search_query,
        'movement_filter': movement_filter,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/stockMovement_dataTable.html', context)
    return render(request, 'mainDash/stockMovement_page.html', context)

def stock_movement_create(request):
    if request.method == 'POST':
        form = StockMovementForm(request.POST)
        if form.is_valid():
            movement = form.save(commit=False)
            movement.created_by = request.user
            movement.updated_by = request.user
            movement.save()

            # update item status if outbound
            if movement.movement_type == StockMovement.MOVEMENT_OUT:
                movement.item.status = WarehouseItem.STATUS_DISPATCHED
                movement.item.dispatched_date = movement.movement_date
                movement.item.updated_by = request.user
                movement.item.save()

                log_activity(
                user=request.user,
                action='created',
                model_name='StockMovement',
                object_repr=str(movement.item.customer_name),
                description=f"Recorded {movement.get_movement_type_display()} stock movement for '{movement.item.customer_name}'.",
                )

            return toast_success(request, 'Stock movement recorded.', alert_type="success", redirect_url="/dashboard/warehouse/stock-movement/")
        oob_html = render_simple_form_errors_oob(form)
        return toast_error(request, "Please fix the required data errors below.", alert_type="danger", oob_content=oob_html)

    return render(request, 'mainDash/create_stockMovement.html', {'form': StockMovementForm()})

@require_POST
def stock_movement_delete(request, pk):
    movement = get_object_or_404(StockMovement, pk=pk)
    log_activity(
        user=request.user,
        action='deleted',
        model_name='StockMovement',
        object_repr=str(movement.item.customer_name),
        description=f"Deleted stock movement record for '{movement.item.customer_name}'.",
    )
    movement.delete()
    return JsonResponse({'success': True})

# ---------- Storage Locations ----------

def storage_location_list(request):
    locations = StorageLocation.objects.select_related('warehouse').all()

    warehouse_filter = request.GET.get('warehouse', '')
    if warehouse_filter:
        locations = locations.filter(warehouse_id=warehouse_filter)

    search_query = request.GET.get('search', '')
    if search_query:
        locations = locations.filter(
            Q(zone__icontains=search_query) |
            Q(shelf__icontains=search_query) |
            Q(warehouse__name__icontains=search_query)
        )

    paginator = Paginator(locations, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'locations_page': page_obj,
        'search_query': search_query,
        'warehouse_filter': warehouse_filter,
        'warehouses': Warehouse.objects.filter(is_active=True),
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/storageLocation_dataTable.html', context)
    return render(request, 'mainDash/storageLocation_page.html', context)

def storage_location_create(request):
    if request.method == 'POST':
        form = StorageLocationForm(request.POST)
        if form.is_valid():
            location = form.save(commit=False)
            location.created_by = request.user
            location.updated_by = request.user
            location.save()
            log_activity(
            user=request.user,
            action='created',
            model_name='StorageLocation',
            object_repr=str(location),
            description=f"Added storage location '{location}' in warehouse '{location.warehouse.name}'.",
            )
            return toast_success(
                request,
                f'Storage location "{location}" added.',
                alert_type="success",
                redirect_url="/dashboard/warehouse/locations/",
            )
        oob_html = render_simple_form_errors_oob(form)
        return toast_error(
            request,
            "Please fix the required data errors below.",
            alert_type="danger",
            oob_content=oob_html,
        )

    # GET — pre-select warehouse if passed via query param from detail page
    warehouse_id = request.GET.get('warehouse')
    return render(request, 'mainDash/components/create_storageLocation.html', {
        'form': StorageLocationForm(warehouse_id=warehouse_id),
    })

@require_POST
def storage_location_delete(request, pk):
    location = get_object_or_404(StorageLocation, pk=pk)
    log_activity(
        user=request.user,
        action='deleted',
        model_name='StorageLocation',
        object_repr=str(location),
        description=f"Deleted storage location '{location}' from warehouse '{location.warehouse.name}'.",
    )
    location.delete()
    return JsonResponse({'success': True})


# ---------- Warehouse Reports ----------

def warehouse_reports(request):
    from django.db.models import Sum, Count
    from django.utils import timezone
    from datetime import timedelta

    thirty_days_ago = timezone.now().date() - timedelta(days=30)

    context = {
        'total_warehouses': Warehouse.objects.filter(is_active=True).count(),
        'total_items': WarehouseItem.objects.count(),
        'in_stock_count': WarehouseItem.objects.filter(status=WarehouseItem.STATUS_IN_STOCK).count(),
        'dispatched_count': WarehouseItem.objects.filter(status=WarehouseItem.STATUS_DISPATCHED).count(),
        'on_hold_count': WarehouseItem.objects.filter(status=WarehouseItem.STATUS_HELD).count(),
        'inbound_30d': StockMovement.objects.filter(movement_type=StockMovement.MOVEMENT_IN, movement_date__gte=thirty_days_ago).count(),
        'outbound_30d': StockMovement.objects.filter(movement_type=StockMovement.MOVEMENT_OUT, movement_date__gte=thirty_days_ago).count(),
        'total_weight': WarehouseItem.objects.filter(status=WarehouseItem.STATUS_IN_STOCK).aggregate(total=Sum('weight_kg'))['total'] or 0,
        'destinations': WarehouseItem.objects.filter(status=WarehouseItem.STATUS_IN_STOCK).values('destination_country').annotate(count=Count('id')).order_by('-count')[:5],
        'warehouses': Warehouse.objects.filter(is_active=True).annotate(item_count=Count('items')),
    }

    return render(request, 'mainDash/warehouseReport_page.html', context)

def warehouse_reports_summary(request):
    from django.db.models import Sum, Count
    from django.utils import timezone
    from datetime import timedelta

    period = request.GET.get('period', '30')
    today = timezone.now().date()
    from_date = today if period == 'today' else today - timedelta(days=int(period))

    context = {
        'inbound': StockMovement.objects.filter(movement_type=StockMovement.MOVEMENT_IN, movement_date__gte=from_date).count(),
        'outbound': StockMovement.objects.filter(movement_type=StockMovement.MOVEMENT_OUT, movement_date__gte=from_date).count(),
        'total_weight': WarehouseItem.objects.filter(received_date__gte=from_date).aggregate(total=Sum('weight_kg'))['total'] or 0,
    }

    return render(request, 'mainDash/includes/warehouseSummary_fragment.html', context)


# views.py — Finance Management section

# ============================================================
# INVOICES
# ============================================================

def invoice_list(request):
    invoices = Invoice.objects.all()

    search_query = request.GET.get('search', '')
    if search_query:
        invoices = invoices.filter(
            Q(invoice_number__icontains=search_query) |
            Q(customer_name__icontains=search_query) |
            Q(customer_email__icontains=search_query) |
            Q(destination_country__icontains=search_query)
        )

    status_filter = request.GET.get('status', '')
    if status_filter:
        invoices = invoices.filter(status=status_filter)

    currency_filter = request.GET.get('currency', '')
    if currency_filter:
        invoices = invoices.filter(currency=currency_filter)

    paginator = Paginator(invoices, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'invoices_page': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'currency_filter': currency_filter,
        'status_choices': Invoice.STATUS_CHOICES,
        'currency_choices': Invoice.CURRENCY_CHOICES,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/invoice_dataTable.html', context)
    return render(request, 'mainDash/invoice_page.html', context)

def invoice_create(request):
    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.created_by = request.user
            invoice.updated_by = request.user
            invoice.save()

            log_activity(
            user=request.user,
            action='created',
            model_name='Invoice',
            object_repr=invoice.invoice_number,
            description=f"Created invoice '{invoice.invoice_number}' for '{invoice.customer_name}'.",
            )
            
            return toast_success(
                request,
                f'Invoice created successfully!',
                alert_type="success",
                redirect_url=f"/dashboard/finance/invoices/{invoice.uuid}/",
            )
        oob_html = render_simple_form_errors_oob(form)
        return toast_error(
            request, "Please fix the required data errors below.",
            alert_type="danger", oob_content=oob_html,
        )

    return render(request, 'mainDash/create_invoice.html', {'form': InvoiceForm()})

def invoice_detail(request, uuid):
    invoice = get_object_or_404(
        Invoice.objects.prefetch_related('line_items', 'payments'),
        uuid=uuid,
    )
    return render(request, 'mainDash/invoice_detailsPage.html', {
        'invoice': invoice,
        'line_items': invoice.line_items.all(),
        'payments': invoice.payments.all(),
        'line_item_form': InvoiceLineItemForm(),
        'payment_form': PaymentForm(initial={'invoice': invoice}),
    })

def invoice_edit(request, uuid):
    invoice = get_object_or_404(Invoice, uuid=uuid)
    if request.method == 'POST':
        form = InvoiceForm(request.POST, instance=invoice)
        if form.is_valid():
            inv = form.save(commit=False)
            inv.updated_by = request.user
            inv.save()

            log_activity(
            user=request.user,
            action='updated',
            model_name='Invoice',
            object_repr=invoice.invoice_number,
            description=f"Updated invoice '{invoice.invoice_number}'.",
            )
            return toast_success(
                request, f'Invoice {invoice.invoice_number} updated.',
                alert_type="success",
                redirect_url=f"/dashboard/finance/invoices/{invoice.uuid}/",
            )
        oob_html = render_simple_form_errors_oob(form)
        return toast_error(
            request, "Please fix the errors below.",
            alert_type="danger", oob_content=oob_html,
        )
    return render(request, 'mainDash/invoice_editPage.html', {
        'form': InvoiceForm(instance=invoice),
        'invoice': invoice,
    })

@require_POST
def invoice_delete(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    log_activity(
        user=request.user,
        action='deleted',
        model_name='Invoice',
        object_repr=invoice.invoice_number,
        description=f"Deleted invoice '{invoice.invoice_number}' for '{invoice.customer_name}'.",
    )
    invoice.delete()
    return JsonResponse({'success': True})


@require_POST
def invoice_add_line_item(request, uuid):
    """Add a line item to an invoice and recalculate totals."""
    invoice = get_object_or_404(Invoice, uuid=uuid)
    form = InvoiceLineItemForm(request.POST)
    if form.is_valid():
        line_item = form.save(commit=False)
        line_item.invoice = invoice
        line_item.save()
        log_activity(
            user=request.user,
            action='updated',
            model_name='Invoice',
            object_repr=invoice.invoice_number,
            description=f"Added line item '{line_item.description}' to invoice '{invoice.invoice_number}'.",
        )
        invoice.recalculate_totals()
        return toast_success(
            request, 'Line item added.',
            alert_type="success",
            redirect_url=f"/dashboard/finance/invoices/{invoice.uuid}/",
        )
    oob_html = render_simple_form_errors_oob(form)
    return toast_error(
        request, "Invalid line item.", alert_type="danger", oob_content=oob_html,
    )


@require_POST
def invoice_delete_line_item(request, pk):
    """Delete a line item and recalculate invoice totals."""
    line_item = get_object_or_404(InvoiceLineItem, pk=pk)
    invoice = line_item.invoice
    log_activity(
        user=request.user,
        action='updated',
        model_name='Invoice',
        object_repr=invoice.invoice_number,
        description=f"Removed line item '{line_item.description}' from invoice '{invoice.invoice_number}'.",
    )
    line_item.delete()
    invoice.recalculate_totals()
    return JsonResponse({'success': True})

@require_POST
def invoice_update_status(request, uuid):
    """Quick status update from the invoice detail page."""
    invoice = get_object_or_404(Invoice, uuid=uuid)
    new_status = request.POST.get('status')
    if new_status not in dict(Invoice.STATUS_CHOICES):
        return toast_error(request, "Invalid status.", alert_type="danger")
    invoice.status = new_status
    invoice.updated_by = request.user
    invoice.save(update_fields=['status', 'updated_by', 'updated_at'])

    log_activity(
        user=request.user,
        action='updated',
        model_name='Invoice',
        object_repr=invoice.invoice_number,
        description=f"Updated invoice '{invoice.invoice_number}' status to '{invoice.get_status_display()}'.",
    )
    return toast_success(
        request,
        f'Invoice status updated to "{invoice.get_status_display()}".',
        alert_type="success",
        redirect_url=f"/dashboard/finance/invoices/{invoice.uuid}/",
    )

# ============================================================
# PAYMENTS
# ============================================================

def payment_list(request):
    payments = Payment.objects.select_related('invoice').all()

    search_query = request.GET.get('search', '')
    if search_query:
        payments = payments.filter(
            Q(invoice__invoice_number__icontains=search_query) |
            Q(invoice__customer_name__icontains=search_query) |
            Q(reference__icontains=search_query)
        )

    method_filter = request.GET.get('method', '')
    if method_filter:
        payments = payments.filter(method=method_filter)

    paginator = Paginator(payments, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'payments_page': page_obj,
        'search_query': search_query,
        'method_filter': method_filter,
        'method_choices': Payment.METHOD_CHOICES,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/payment_dataTable.html', context)
    return render(request, 'mainDash/payment_page.html', context)

def payment_create(request):
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.created_by = request.user
            payment.updated_by = request.user
            payment.save()  # Payment.save() auto-syncs invoice amount_paid + status
            
            log_activity(
            user=request.user,
            action='created',
            model_name='Payment',
            object_repr=str(payment.reference or payment.pk),
            description=f"Recorded payment of {payment.amount} {payment.invoice.currency} for invoice '{payment.invoice.invoice_number}'.",
            )
            return toast_success(
                request, 'Payment recorded successfully.',
                alert_type="success",
                redirect_url="/dashboard/finance/payments/",
            )
        oob_html = render_simple_form_errors_oob(form)
        return toast_error(
            request, "Please fix the errors below.",
            alert_type="danger", oob_content=oob_html,
        )
    return render(request, 'mainDash/create_payment.html', {'form': PaymentForm()})

@require_POST
def payment_delete(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    invoice = payment.invoice
    log_activity(
        user=request.user,
        action='deleted',
        model_name='Payment',
        object_repr=str(payment.reference or payment.pk),
        description=f"Deleted payment from invoice '{invoice.invoice_number}'.",
    )

    payment.delete()
    # Recalculate invoice amount_paid after deletion
    total_paid = invoice.payments.aggregate(
        total=models.Sum('amount')
    )['total'] or 0
    invoice.amount_paid = total_paid
    if total_paid == 0:
        invoice.status = Invoice.STATUS_SENT
    elif total_paid < invoice.total_amount:
        invoice.status = Invoice.STATUS_PARTIALLY_PAID
    else:
        invoice.status = Invoice.STATUS_PAID
    invoice.save(update_fields=['amount_paid', 'status', 'updated_at'])
    return JsonResponse({'success': True})

# ============================================================
# FREIGHT CHARGES (InvoiceLineItem filtered by charge_type=freight)
# ============================================================

def freight_charge_list(request):
    """
    All freight/shipping charges across all invoices — a filtered
    view of InvoiceLineItem with charge_type='freight', giving staff
    a cross-invoice freight summary without opening each invoice.
    """
    charges = InvoiceLineItem.objects.select_related(
        'invoice', 'item'
    ).filter(charge_type=InvoiceLineItem.CHARGE_FREIGHT)

    search_query = request.GET.get('search', '')
    if search_query:
        charges = charges.filter(
            Q(description__icontains=search_query) |
            Q(invoice__customer_name__icontains=search_query) |
            Q(invoice__invoice_number__icontains=search_query)
        )

    paginator = Paginator(charges, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'charges_page': page_obj,
        'search_query': search_query,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/freightCharge_dataTable.html', context)
    return render(request, 'mainDash/freightCharge_page.html', context)

# ============================================================
# CUSTOMS & DUTY
# ============================================================

def customs_duty_list(request):
    records = CustomsDutyRecord.objects.select_related('item', 'invoice').all()

    search_query = request.GET.get('search', '')
    if search_query:
        records = records.filter(
            Q(item__customer_name__icontains=search_query) |
            Q(customs_reference__icontains=search_query) |
            Q(destination_country__icontains=search_query)
        )

    status_filter = request.GET.get('status', '')
    if status_filter:
        records = records.filter(status=status_filter)

    paginator = Paginator(records, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'records_page': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'status_choices': CustomsDutyRecord.STATUS_CHOICES,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/customsDuty_dataTable.html', context)
    return render(request, 'mainDash/customsDuty_page.html', context)

def customs_duty_create(request):
    if request.method == 'POST':
        form = CustomsDutyForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.created_by = request.user
            record.updated_by = request.user
            record.save()

            log_activity(
            user=request.user,
            action='created',
            model_name='CustomsDutyRecord',
            object_repr=record.customs_reference or str(record.pk),
            description=f"Added customs duty record for '{record.destination_country}'.",
            )
            return toast_success(
                request, 'Customs duty record added.',
                alert_type="success",
                redirect_url="/dashboard/finance/customs/",
            )
        oob_html = render_simple_form_errors_oob(form)
        return toast_error(
            request, "Please fix the errors below.",
            alert_type="danger", oob_content=oob_html,
        )
    return render(request, 'mainDash/create_customsDuty.html', {'form': CustomsDutyForm()})


@require_POST
def customs_duty_delete(request, pk):
    record = get_object_or_404(CustomsDutyRecord, pk=pk)
    log_activity(
        user=request.user,
        action='deleted',
        model_name='CustomsDutyRecord',
        object_repr=record.customs_reference or str(record.pk),
        description=f"Deleted customs duty record '{record.customs_reference}'.",
    )
    record.delete()
    return JsonResponse({'success': True})

# ============================================================
# EXPENSES
# ============================================================

def expense_list(request):
    expenses = Expense.objects.select_related('warehouse').all()

    search_query = request.GET.get('search', '')
    if search_query:
        expenses = expenses.filter(
            Q(description__icontains=search_query) |
            Q(warehouse__name__icontains=search_query)
        )

    category_filter = request.GET.get('category', '')
    if category_filter:
        expenses = expenses.filter(category=category_filter)

    currency_filter = request.GET.get('currency', '')
    if currency_filter:
        expenses = expenses.filter(currency=currency_filter)

    paginator = Paginator(expenses, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'expenses_page': page_obj,
        'search_query': search_query,
        'category_filter': category_filter,
        'currency_filter': currency_filter,
        'category_choices': Expense.CATEGORY_CHOICES,
        'currency_choices': Invoice.CURRENCY_CHOICES,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/expense_dataTable.html', context)
    return render(request, 'mainDash/expense_page.html', context)

def expense_create(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.created_by = request.user
            expense.updated_by = request.user
            expense.save()

            log_activity(
            user=request.user,
            action='created',
            model_name='Expense',
            object_repr=expense.description[:60],
            description=f"Recorded expense '{expense.description[:60]}' of {expense.amount} {expense.currency}.",
            )
            return toast_success(
                request, 'Expense recorded.',
                alert_type="success",
                redirect_url="/dashboard/finance/expenses/",
            )
        oob_html = render_simple_form_errors_oob(form)
        return toast_error(
            request, "Please fix the errors below.",
            alert_type="danger", oob_content=oob_html,
        )
    return render(request, 'mainDash/create_expense.html', {'form': ExpenseForm()})

@require_POST
def expense_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    log_activity(
        user=request.user,
        action='deleted',
        model_name='Expense',
        object_repr=expense.description[:60],
        description=f"Deleted expense '{expense.description[:60]}'.",
    )
    expense.delete()
    return JsonResponse({'success': True})

# ============================================================
# AGENT COMMISSIONS
# ============================================================

def agent_commission_list(request):
    commissions = AgentCommission.objects.select_related('item').all()

    search_query = request.GET.get('search', '')
    if search_query:
        commissions = commissions.filter(
            Q(agent_name__icontains=search_query) |
            Q(agent_country__icontains=search_query)
        )

    status_filter = request.GET.get('status', '')
    if status_filter:
        commissions = commissions.filter(status=status_filter)

    paginator = Paginator(commissions, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'commissions_page': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'status_choices': AgentCommission.STATUS_CHOICES,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/agentCommission_dataTable.html', context)
    return render(request, 'mainDash/agentCommission_page.html', context)

def agent_commission_create(request):
    if request.method == 'POST':
        form = AgentCommissionForm(request.POST)
        if form.is_valid():
            commission = form.save(commit=False)
            commission.created_by = request.user
            commission.updated_by = request.user
            commission.save()

            log_activity(
            user=request.user,
            action='created',
            model_name='AgentCommission',
            object_repr=commission.agent_name,
            description=f"Recorded commission for agent '{commission.agent_name}' ({commission.agent_country}).",
            )
            return toast_success(
                request, f'Commission for "{commission.agent_name}" recorded.',
                alert_type="success",
                redirect_url="/dashboard/finance/commissions/",
            )
        oob_html = render_simple_form_errors_oob(form)
        return toast_error(
            request, "Please fix the errors below.",
            alert_type="danger", oob_content=oob_html,
        )
    return render(request, 'mainDash/create_agentCommission.html', {'form': AgentCommissionForm()})

@require_POST
def agent_commission_delete(request, pk):
    commission = get_object_or_404(AgentCommission, pk=pk)
    log_activity(
        user=request.user,
        action='deleted',
        model_name='AgentCommission',
        object_repr=commission.agent_name,
        description=f"Deleted commission record for agent '{commission.agent_name}'.",
    )
    commission.delete()
    return JsonResponse({'success': True})

# ============================================================
# EXCHANGE RATES
# ============================================================

def exchange_rate_list(request):
    rates = ExchangeRate.objects.select_related('created_by').all()

    currency_filter = request.GET.get('currency', '')
    if currency_filter:
        rates = rates.filter(
            Q(base_currency=currency_filter) | Q(target_currency=currency_filter)
        )

    paginator = Paginator(rates, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'rates_page': page_obj,
        'currency_filter': currency_filter,
        'currency_choices': Invoice.CURRENCY_CHOICES,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/exchangeRate_dataTable.html', context)
    return render(request, 'mainDash/exchangeRate_page.html', context)


def exchange_rate_create(request):
    if request.method == 'POST':
        form = ExchangeRateForm(request.POST)
        if form.is_valid():
            rate = form.save(commit=False)
            rate.created_by = request.user
            rate.save()

            log_activity(
            user=request.user,
            action='created',
            model_name='ExchangeRate',
            object_repr=f"{rate.base_currency} → {rate.target_currency}",
            description=f"Added exchange rate {rate.base_currency} → {rate.target_currency} = {rate.rate}.",
            )
            return toast_success(
                request, 'Exchange rate added.',
                alert_type="success",
                redirect_url="/dashboard/finance/exchange-rates/",
            )
        oob_html = render_simple_form_errors_oob(form)
        return toast_error(
            request, "Please fix the errors below.",
            alert_type="danger", oob_content=oob_html,
        )
    return render(request, 'mainDash/create_exchangeRate.html', {'form': ExchangeRateForm()})

@require_POST
def exchange_rate_delete(request, pk):
    rate = get_object_or_404(ExchangeRate, pk=pk)
    log_activity(
        user=request.user,
        action='deleted',
        model_name='ExchangeRate',
        object_repr=f"{rate.base_currency} → {rate.target_currency}",
        description=f"Deleted exchange rate {rate.base_currency} → {rate.target_currency}.",
    )
    rate.delete()
    return JsonResponse({'success': True})

# ============================================================
# FINANCIAL REPORTS
# ============================================================

def finance_reports(request):

    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)

    # Revenue
    total_invoiced = Invoice.objects.aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    total_collected = Invoice.objects.aggregate(
        total=Sum('amount_paid')
    )['total'] or 0
    outstanding = total_invoiced - total_collected

    # Invoice status breakdown
    invoice_by_status = {
        status: Invoice.objects.filter(status=status).count()
        for status, _ in Invoice.STATUS_CHOICES
    }

    # Expenses last 30 days
    expenses_30d = Expense.objects.filter(
        expense_date__gte=thirty_days_ago
    ).aggregate(total=Sum('amount'))['total'] or 0

    # Customs duties outstanding
    duties_pending = CustomsDutyRecord.objects.filter(
        status__in=[CustomsDutyRecord.STATUS_PENDING, CustomsDutyRecord.STATUS_PROCESSING]
    ).aggregate(total=Sum('duty_amount'))['total'] or 0

    # Commissions unpaid
    commissions_pending = AgentCommission.objects.filter(
        status__in=[AgentCommission.STATUS_PENDING, AgentCommission.STATUS_PROCESSING]
    ).aggregate(total=Sum('commission_amount'))['total'] or 0

    # Latest exchange rates (one per pair)
    latest_rate_dates = ExchangeRate.objects.values(
    'base_currency', 'target_currency'
    ).annotate(latest_date=Max('effective_date'))

    latest_rates = [
        ExchangeRate.objects.filter(
            base_currency=e['base_currency'],
            target_currency=e['target_currency'],
            effective_date=e['latest_date']
        ).first()
        for e in latest_rate_dates
    ]

    context = {
        'total_invoiced': total_invoiced,
        'total_collected': total_collected,
        'outstanding': outstanding,
        'invoice_by_status': invoice_by_status,
        'expenses_30d': expenses_30d,
        'duties_pending': duties_pending,
        'commissions_pending': commissions_pending,
        'latest_rates': latest_rates,
        'overdue_invoices': Invoice.objects.filter(
            status=Invoice.STATUS_OVERDUE
        ).count(),
        'recent_payments': Payment.objects.select_related('invoice').order_by('-paid_on')[:5],
    }

    # Invoice aging buckets — based on due_date for unpaid/overdue invoices
    unpaid_invoices = Invoice.objects.filter(
        status__in=[
            Invoice.STATUS_SENT,
            Invoice.STATUS_PARTIALLY_PAID,
            Invoice.STATUS_OVERDUE,
        ]
    )

    aging_current = unpaid_invoices.filter(due_date__gte=today)
    aging_0_30 = unpaid_invoices.filter(
        due_date__lt=today,
        due_date__gte=today - timedelta(days=30)
    )
    aging_31_60 = unpaid_invoices.filter(
        due_date__lt=today - timedelta(days=30),
        due_date__gte=today - timedelta(days=60)
    )
    aging_60_plus = unpaid_invoices.filter(
        due_date__lt=today - timedelta(days=60)
    )

    context.update({
    'aging_current': aging_current,
    'aging_current_total': aging_current.aggregate(
        t=Sum(models.F('total_amount') - models.F('amount_paid'))
    )['t'] or 0,

    'aging_0_30': aging_0_30,
    'aging_0_30_total': aging_0_30.aggregate(
        t=Sum(models.F('total_amount') - models.F('amount_paid'))
    )['t'] or 0,

    'aging_31_60': aging_31_60,
    'aging_31_60_total': aging_31_60.aggregate(
        t=Sum(models.F('total_amount') - models.F('amount_paid'))
    )['t'] or 0,

    'aging_60_plus': aging_60_plus,
    'aging_60_plus_total': aging_60_plus.aggregate(
        t=Sum(models.F('total_amount') - models.F('amount_paid'))
    )['t'] or 0,

    'aging_60_plus_count': aging_60_plus.count(),
    })

    return render(request, 'mainDash/financeReport_page.html', context)

# ============================================================
# CUSTOMS SHIPPING VIEWS
# ============================================================

# --- Customs Documentation ---

def customs_document_list(request):
    documents = CustomsDocument.objects.select_related(
        'shipment', 'shipment__order', 'item'
    ).all()

    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    doc_type_filter = request.GET.get('document_type', '')

    if search_query:
        documents = documents.filter(
            Q(document_number__icontains=search_query) |
            Q(shipment__shipment_number__icontains=search_query) |
            Q(item__customer_name__icontains=search_query)
        )
    if status_filter:
        documents = documents.filter(status=status_filter)
    if doc_type_filter:
        documents = documents.filter(document_type=doc_type_filter)

    paginator = Paginator(documents, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'documents_page': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'doc_type_filter': doc_type_filter,
        'status_choices': CustomsDocument.STATUS_CHOICES,
        'document_type_choices': CustomsDocument.DOCUMENT_TYPE_CHOICES,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/customs_document_dataTable.html', context)
    return render(request, 'mainDash/customs_document_page.html', context)


def customs_document_create(request):
    if request.method == 'POST':
        form = CustomsDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.created_by = request.user
            doc.save()

            log_activity(
            user=request.user,
            action='created',
            model_name='CustomsDocument',
            object_repr=doc.document_number or doc.get_document_type_display(),
            description=f"Added customs document '{doc.get_document_type_display()}' (ref: {doc.document_number}).",
            )
            return toast_success(
                request,
                f'Document "{doc.get_document_type_display()}" added successfully.',
                alert_type='success',
                redirect_url='/dashboard/customs/documents/',
            )
        oob_html = render_simple_form_errors_oob(form)
        return toast_error(
            request, "Invalid form data. Please check your inputs.",
            alert_type="danger", 
            oob_content=oob_html,
        )

    return render(request, 'mainDash/customs_document_create.html', {
        'form': CustomsDocumentForm(),
    })


def customs_document_detail(request, uuid):
    document = get_object_or_404(
        CustomsDocument.objects.select_related('shipment', 'shipment__order', 'item'),
        uuid=uuid,
    )
    return render(request, 'mainDash/customs_document_detail.html', {
        'document': document,
    })


def customs_document_edit(request, uuid):
    document = get_object_or_404(CustomsDocument, uuid=uuid)
    if request.method == 'POST':
        form = CustomsDocumentForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.updated_by = request.user
            doc.save()

            log_activity(
            user=request.user,
            action='updated',
            model_name='CustomsDocument',
            object_repr=document.document_number or document.get_document_type_display(),
            description=f"Updated customs document '{doc.get_document_type_display()}' (ref: {document.document_number}).",
            )
            return toast_success(
                request,
                f'Document "{doc.get_document_type_display()}" updated successfully.',
                alert_type='success',
                redirect_url=f'/dashboard/customs/documents/{document.uuid}/',
            )
        oob_html = render_simple_form_errors_oob(form)
        return toast_error(
            request,
            "Invalid form data. Please check your inputs.",
            alert_type="danger",
            oob_content=oob_html,
        )

    return render(request, 'mainDash/customs_document_edit.html', {
        'form': CustomsDocumentForm(instance=document),
        'document': document,
    })


@require_POST
def customs_document_delete(request, pk):
    document = get_object_or_404(CustomsDocument, pk=pk)
    log_activity(
        user=request.user,
        action='deleted',
        model_name='CustomsDocument',
        object_repr=document.document_number or str(document.pk),
        description=f"Deleted customs document '{document.document_number}'.",
    )
    if document.file:
        document.file.delete(save=False)
    document.delete()
    return JsonResponse({'success': True})

# --- Import Shipments ---

def import_shipment_list(request):
    shipments = Shipment.objects.select_related('order').filter(
        shipment_direction=Shipment.DIRECTION_INBOUND
    )

    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    customs_status_filter = request.GET.get('customs_status', '')

    if search_query:
        shipments = shipments.filter(
            Q(shipment_number__icontains=search_query) |
            Q(order__order_number__icontains=search_query) |
            Q(order__customer_name__icontains=search_query) |
            Q(order__tracking_number__icontains=search_query)
        )
    if status_filter:
        shipments = shipments.filter(status=status_filter)
    if customs_status_filter:
        shipments = shipments.filter(customs_status=customs_status_filter)

    paginator = Paginator(shipments, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'shipments_page': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'customs_status_filter': customs_status_filter,
        'status_choices': Shipment.STATUS_CHOICES,
        'customs_status_choices': Shipment.CUSTOMS_STATUS_CHOICES,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/import_shipment_dataTable.html', context)
    return render(request, 'mainDash/import_shipment_page.html', context)

# --- Export Shipments ---

def export_shipment_list(request):
    shipments = Shipment.objects.select_related('order').filter(
        shipment_direction=Shipment.DIRECTION_OUTBOUND
    )

    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    customs_status_filter = request.GET.get('customs_status', '')

    if search_query:
        shipments = shipments.filter(
            Q(shipment_number__icontains=search_query) |
            Q(order__order_number__icontains=search_query) |
            Q(order__customer_name__icontains=search_query) |
            Q(order__tracking_number__icontains=search_query)
        )
    if status_filter:
        shipments = shipments.filter(status=status_filter)
    if customs_status_filter:
        shipments = shipments.filter(customs_status=customs_status_filter)

    paginator = Paginator(shipments, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'shipments_page': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'customs_status_filter': customs_status_filter,
        'status_choices': Shipment.STATUS_CHOICES,
        'customs_status_choices': Shipment.CUSTOMS_STATUS_CHOICES,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/export_shipment_dataTable.html', context)
    return render(request, 'mainDash/export_shipment_page.html', context)

@require_POST
def shipment_update_customs_status(request, uuid):
    shipment = get_object_or_404(Shipment, uuid=uuid)
    new_status = request.POST.get('customs_status')
    valid_statuses = [s[0] for s in Shipment.CUSTOMS_STATUS_CHOICES]

    if new_status not in valid_statuses:
        return toast_error(request, 'Invalid customs status.', alert_type='danger')

    shipment.customs_status = new_status
    shipment.updated_at = timezone.now()
    shipment.save(update_fields=['customs_status', 'updated_at'])
    # send email notification here
    send_shipment_status_email(shipment)
    
    log_activity(
        user=request.user,
        action='updated',
        model_name='Shipment',
        object_repr=shipment.shipment_number,
        description=f"Updated customs status of shipment '{shipment.shipment_number}' to '{shipment.get_customs_status_display()}'.",
    )

    return toast_success(
        request,
        f'Customs status updated to "{shipment.get_customs_status_display()}".',
        alert_type='success',
        redirect_url=f'/dashboard/shipments/{shipment.uuid}/',
    )

# --- Duty & Tax Management ---

def duty_tax_list(request):
    records = CustomsDutyRecord.objects.select_related('item', 'invoice').all()

    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')

    if search_query:
        records = records.filter(
            Q(customs_reference__icontains=search_query) |
            Q(item__customer_name__icontains=search_query) |
            Q(customs_agent__icontains=search_query) |
            Q(clearance_port__icontains=search_query)
        )
    if status_filter:
        records = records.filter(status=status_filter)

    paginator = Paginator(records, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'records_page': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'status_choices': CustomsDutyRecord.STATUS_CHOICES,
        'total_duty': records.aggregate(t=Sum('duty_amount'))['t'] or 0,
        'total_tax': records.aggregate(t=Sum('tax_amount'))['t'] or 0,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/duty_tax_dataTable.html', context)
    return render(request, 'mainDash/duty_tax_page.html', context)


def duty_tax_create(request):
    if request.method == 'POST':
        form = CustomsDutyForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.created_by = request.user
            record.save()

            log_activity(
            user=request.user,
            action='created',
            model_name='CustomsDutyRecord',
            object_repr=record.customs_reference or str(record.pk),
            description=f"Created duty & tax record for '{record.destination_country}' (ref: {record.customs_reference}).",
            )
            return toast_success(
                request,
                "Duty & tax record created successfully.",
                alert_type="success",
                redirect_url="/dashboard/customs/duty-tax/",
            )
        oob_html = render_simple_form_errors_oob(form)
        return toast_error(
            request,
            "Invalid form data. Please check your inputs.",
            alert_type="danger",
            oob_content=oob_html,
        )

    return render(request, 'mainDash/duty_tax_create.html', {
        'form': CustomsDutyForm(),
        'countries': countries,
    })

@require_POST
def duty_tax_delete(request, pk):
    record = get_object_or_404(CustomsDutyRecord, pk=pk)
    log_activity(
        user=request.user,
        action='deleted',
        model_name='CustomsDutyRecord',
        object_repr=record.customs_reference or str(record.pk),
        description=f"Deleted duty & tax record '{record.customs_reference}'.",
    )
    record.delete()
    return JsonResponse({'success': True})


# ──────────────────────────────────────────
# Documents Module Views
# ──────────────────────────────────────────
# --- Shipping Labels ---
def shipping_label_list(request):
    labels = UploadedDocument.objects.filter(
        document_type='shipping_label'
    ).select_related('shipment', 'order', 'uploaded_by')

    search = request.GET.get('search', '')
    if search:
        labels = labels.filter(title__icontains=search)

    paginator = Paginator(labels, 20)
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'mainDash/shipping_label_page.html', {
        'labels': page,
        'search': search,
    })


def shipping_label_detail(request, uuid):
    label = get_object_or_404(UploadedDocument, uuid=uuid, document_type='shipping_label')
    return render(request, 'mainDash/shipping_label_detail.html', {'label': label})


# --- Invoices (print-ready) ---
def document_invoice_list(request):
    invoices = Invoice.objects.select_related('created_by').all()

    search        = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')

    if search:
        invoices = invoices.filter(
            Q(invoice_number__icontains=search) |
            Q(customer_name__icontains=search) |
            Q(destination_country__icontains=search)
        )
    if status_filter:
        invoices = invoices.filter(status=status_filter)

    paginator = Paginator(invoices, 20)
    page      = paginator.get_page(request.GET.get('page'))

    context = {
        'invoices':      page,
        'search':        search,
        'status_filter': status_filter,
        'status_choices': Invoice.STATUS_CHOICES,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/document_invoice_dataTable.html', context)
    return render(request, 'mainDash/document_invoice_list.html', context)


def document_invoice_detail(request, uuid):
    from mainWebsite.models import Invoice
    invoice = get_object_or_404(Invoice, uuid=uuid)
    return render(request, 'mainDash/document_invoice_detail.html', {'invoice': invoice})


# --- Delivery Notes ---
def delivery_note_list(request):
    notes = UploadedDocument.objects.filter(
        document_type='delivery_note'
    ).select_related('shipment', 'order', 'uploaded_by')

    search = request.GET.get('search', '')
    if search:
        notes = notes.filter(title__icontains=search)

    paginator = Paginator(notes, 20)
    page = paginator.get_page(request.GET.get('page'))

    context = {
        'notes': page,
        'search': search,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/delivery_note_dataTable.html', context)
    return render(request, 'mainDash/delivery_note_list.html', context)


def delivery_note_detail(request, uuid):
    note = get_object_or_404(UploadedDocument, uuid=uuid, document_type='delivery_note')
    return render(request, 'mainDash/delivery_note_detail.html', {'note': note})


# --- Customs Forms ---
def document_customs_list(request):
    from mainWebsite.models import CustomsDocument
    from django.db.models import Q
    from django.core.paginator import Paginator

    customs = CustomsDocument.objects.select_related(
        'shipment', 'shipment__order', 'item', 'created_by'
    ).all().order_by('-created_at')

    search        = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    type_filter   = request.GET.get('document_type', '')

    if search:
        customs = customs.filter(
            Q(document_number__icontains=search) |
            Q(shipment__shipment_number__icontains=search) |
            Q(item__customer_name__icontains=search)
        )
    if status_filter:
        customs = customs.filter(status=status_filter)
    if type_filter:
        customs = customs.filter(document_type=type_filter)

    paginator = Paginator(customs, 20)
    page      = paginator.get_page(request.GET.get('page'))

    context = {
        'customs':          page,
        'search':           search,
        'status_filter':    status_filter,
        'type_filter':      type_filter,
        'status_choices':   CustomsDocument.STATUS_CHOICES,
        'doc_type_choices': CustomsDocument.DOCUMENT_TYPE_CHOICES,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/document_customs_dataTable.html', context)
    return render(request, 'mainDash/document_customs_list.html', context)


def document_customs_detail(request, uuid):
    from mainWebsite.models import CustomsDocument
    doc = get_object_or_404(CustomsDocument, uuid=uuid)
    return render(request, 'mainDash/document_customs_detail.html', {'doc': doc})

# --- Uploaded Documents ---
def uploaded_document_list(request):
    documents = UploadedDocument.objects.select_related(
        'order', 'shipment', 'invoice', 'uploaded_by'
    ).all()

    search      = request.GET.get('search', '')
    type_filter = request.GET.get('document_type', '')
    status      = request.GET.get('status', '')

    if search:
        documents = documents.filter(
            Q(title__icontains=search) |
            Q(order__order_number__icontains=search) |
            Q(shipment__tracking_number__icontains=search)
        )
    if type_filter:
        documents = documents.filter(document_type=type_filter)
    if status:
        documents = documents.filter(status=status)

    paginator = Paginator(documents, 20)
    page = paginator.get_page(request.GET.get('page'))

    context = {
        'documents':   page,
        'search':      search,
        'type_filter': type_filter,
        'status':      status,
        'doc_types':   UploadedDocument.DOCUMENT_TYPE_CHOICES,
        'statuses':    UploadedDocument.STATUS_CHOICES,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/uploaded_document_dataTable.html', context)
    return render(request, 'mainDash/uploaded_document_list.html', context)


def uploaded_document_create(request):
    if request.method == 'POST':
        form = UploadedDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.uploaded_by = request.user
            doc.file_size   = request.FILES['file'].size if 'file' in request.FILES else None
            doc.save()

            log_activity(
            user=request.user,
            action='created',
            model_name='UploadedDocument',
            object_repr=doc.title,
            description=f"Uploaded document '{doc.title}' ({doc.get_document_type_display()}).",
            )
            
            return toast_success(
                request,
                "Document uploaded successfully.",
                alert_type="success",
                redirect_url="/dashboard/documents/uploaded/",
             )
        oob_html = render_simple_form_errors_oob(form)
        return toast_error(
            request,
            "Invalid form data. Please check your inputs.",
            alert_type="danger",
            oob_content=oob_html,
        )

    return render(request, 'mainDash/uploaded_document_create.html', {
        'form': UploadedDocumentForm(),
    })


def uploaded_document_detail(request, uuid):
    doc = get_object_or_404(UploadedDocument, uuid=uuid)
    return render(request, 'mainDash/uploaded_document_detail.html', {'doc': doc})


def uploaded_document_edit(request, uuid):
    doc  = get_object_or_404(UploadedDocument, uuid=uuid)
    form = UploadedDocumentForm(instance=doc)

    if request.method == 'POST':
        form = UploadedDocumentForm(request.POST, request.FILES, instance=doc)
        if form.is_valid():
            form.save()

            log_activity(
            user=request.user,
            action='updated',
            model_name='UploadedDocument',
            object_repr=doc.title,
            description=f"Updated document '{doc.title}'.",
            )
            return toast_success(
                request,
                "Document updated successfully.",
                alert_type="success",
                redirect_url="/dashboard/documents/uploaded/",
             )
           
        oob_html = render_simple_form_errors_oob(request, form)
        return toast_error(
            request,
            "Invalid form data. Please check your inputs.",
            alert_type="danger",
            oob_content=oob_html,
        )
    return render(request, 'mainDash/uploaded_document_edit.html', {
        'form': form,
        'doc':  doc,
    })


@require_POST
def uploaded_document_delete(request, uuid):
    doc = get_object_or_404(UploadedDocument, uuid=uuid)
    log_activity(
        user=request.user,
        action='deleted',
        model_name='UploadedDocument',
        object_repr=doc.title,
        description=f"Deleted document '{doc.title}'.",
    )
    try:
        delete_file(doc.file)
    except Exception:
        pass  # file already gone or missing — still proceed
    doc.delete()
    return JsonResponse({'success': True})

# ============================================================
# USER MANAGEMENT
# ============================================================

def _get_or_create_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


# --- All Users ---

def user_list(request):
    # Ensure every user has a profile first
    for user in User.objects.all():
        _get_or_create_profile(user)

    users = User.objects.prefetch_related(
        'groups', 'profile'
    ).filter(
        profile__is_deleted=False
    ).order_by('-date_joined')

    search        = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')

    if search:
        users = users.filter(
            Q(email__icontains=search)          |
            Q(first_name__icontains=search)     |
            Q(last_name__icontains=search)      |
            Q(profile__phone__icontains=search)
        )

    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    elif status_filter == 'staff':
        users = users.filter(is_staff=True)
    elif status_filter == 'superuser':
        users = users.filter(is_superuser=True)

    paginator = Paginator(users, 20)
    page      = paginator.get_page(request.GET.get('page'))

    context = {
        'users':         page,
        'search':        search,
        'status_filter': status_filter,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/user_dataTable.html', context)
    return render(request, 'mainDash/user_list.html', context)

# --- Deleted Users ---

def user_deleted_list(request):
    users = User.objects.prefetch_related(
        'groups', 'profile'
    ).filter(
        profile__is_deleted=True
    ).order_by('-profile__deleted_at')

    search = request.GET.get('search', '')
    if search:
        users = users.filter(
            Q(email__icontains=search)      |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )

    paginator = Paginator(users, 20)
    page      = paginator.get_page(request.GET.get('page'))

    context = {
        'users':  page,
        'search': search,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/user_deleted_dataTable.html', context)
    return render(request, 'mainDash/user_deleted_list.html', context)


# --- Create User ---

def user_create(request):
    groups = Group.objects.all()

    if request.method == 'POST':
        first_name   = request.POST.get('first_name', '').strip()
        last_name    = request.POST.get('last_name', '').strip()
        email        = request.POST.get('email', '').strip()
        phone        = request.POST.get('phone', '').strip()
        password1    = request.POST.get('password1', '')
        password2    = request.POST.get('password2', '')
        is_staff     = request.POST.get('is_staff') == 'on'
        is_superuser = request.POST.get('is_superuser') == 'on'
        group_ids    = request.POST.getlist('groups')

        errors = {}

        if not first_name:
            errors['first_name'] = 'First name is required.'
        if not last_name:
            errors['last_name'] = 'Last name is required.'
        if not email:
            errors['email'] = 'Email is required.'
        elif User.objects.filter(username=email).exists():
            errors['email'] = 'A user with this email already exists.'
        if not phone:
            errors['phone'] = 'Phone number is required.'
        elif UserProfile.objects.filter(phone=phone).exists():
            errors['phone'] = 'A user with this phone number already exists.'
        if not password1:
            errors['password1'] = 'Password is required.'
        elif len(password1) < 8:
            errors['password1'] = 'Password must be at least 8 characters.'
        elif password1 != password2:
            errors['password2'] = 'Passwords do not match.'

        if errors:
            oob_html = ''.join(
                f'<div id="error-{field}" hx-swap-oob="innerHTML">'
                f'<p class="text-danger small mb-0">{msg}</p>'
                f'</div>'
                for field, msg in errors.items()
            )
            return toast_error(
                request,
                "Please fix the errors below.",
                alert_type="danger",
                oob_content=oob_html,
            )

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name,
        )
        user.is_staff     = is_staff
        user.is_superuser = is_superuser
        user.save()

        profile       = _get_or_create_profile(user)
        profile.phone = phone
        profile.save()

        log_activity(
            user=request.user,
            action='created',
            model_name='User',
            object_repr=user.get_full_name(),
            description=f"Created user account for '{user.get_full_name()}' ({user.email}).",
        )

        if group_ids:
            user.groups.set(Group.objects.filter(id__in=group_ids))

        return toast_success(
            request,
            f"User {user.get_full_name()} created successfully.",
            alert_type="success",
            redirect_url="/dashboard/users/",
        )

    return render(request, 'mainDash/user_create.html', {'groups': groups})

# --- User Detail ---

def user_detail(request, uuid):
    profile      = get_object_or_404(UserProfile, uuid=uuid)
    profile_user = profile.user
    return render(request, 'mainDash/user_detail.html', {
        'profile_user': profile_user,
        'profile':      profile,
        'groups':       Group.objects.all(),
    })

# --- User Edit ---

def user_edit(request, uuid):
    profile      = get_object_or_404(UserProfile, uuid=uuid)
    profile_user = profile.user
    groups       = Group.objects.all()

    if request.method == 'POST':
        first_name   = request.POST.get('first_name', '').strip()
        last_name    = request.POST.get('last_name', '').strip()
        email        = request.POST.get('email', '').strip()
        phone        = request.POST.get('phone', '').strip()
        is_staff     = request.POST.get('is_staff') == 'on'
        is_superuser = request.POST.get('is_superuser') == 'on'
        is_active    = request.POST.get('is_active') == 'on'
        group_ids    = request.POST.getlist('groups')

        errors = {}

        if not first_name:
            errors['first_name'] = 'First name is required.'
        if not last_name:
            errors['last_name'] = 'Last name is required.'
        if not email:
            errors['email'] = 'Email is required.'
        elif User.objects.filter(username=email).exclude(pk=profile_user.pk).exists():
            errors['email'] = 'A user with this email already exists.'
        if not phone:
            errors['phone'] = 'Phone number is required.'
        elif UserProfile.objects.filter(phone=phone).exclude(user=profile_user).exists():
            errors['phone'] = 'A user with this phone number already exists.'

        if errors:
            oob_html = ''.join(
                f'<div id="error-{field}" hx-swap-oob="innerHTML">'
                f'<p class="text-danger small mb-0">{msg}</p>'
                f'</div>'
                for field, msg in errors.items()
            )
            return toast_error(
                request,
                "Please fix the errors below.",
                alert_type="danger",
                oob_content=oob_html,
            )

        # handle profile image
        if 'profile_image' in request.FILES:
            if profile.profile_image:
                delete_file(profile.profile_image)
            profile.profile_image = request.FILES['profile_image']

        profile_user.first_name   = first_name
        profile_user.last_name    = last_name
        profile_user.email        = email
        profile_user.username     = email
        profile_user.is_staff     = is_staff
        profile_user.is_superuser = is_superuser
        profile_user.is_active    = is_active
        profile_user.save()

        profile.phone = phone
        profile.save()

        log_activity(
            user=request.user,
            action='updated',
            model_name='User',
            object_repr=profile_user.get_full_name(),
            description=f"Updated user account for '{profile_user.get_full_name()}' ({profile_user.email}).",
        )
        profile_user.groups.set(Group.objects.filter(id__in=group_ids))

        return toast_success(
            request,
            f"User {profile_user.get_full_name()} updated successfully.",
            alert_type="success",
            redirect_url="/dashboard/users/",
        )

    return render(request, 'mainDash/user_edit.html', {
        'profile_user': profile_user,
        'profile':      profile,
        'groups':       groups,
    })

# --- User Toggle Active (HTMX inline) ---

@require_POST
def user_toggle_active(request, uuid):
    profile      = get_object_or_404(UserProfile, uuid=uuid)
    profile_user = profile.user

    if profile_user == request.user:
        return toast_error(
            request,
            "You cannot deactivate your own account.",
            alert_type="danger",
        )

    profile_user.is_active = not profile_user.is_active
    profile_user.save()

    badge_class = 'bg-success text-white' if profile_user.is_active else 'bg-secondary text-white'
    label       = 'Active' if profile_user.is_active else 'Inactive'

    return HttpResponse(
        f'<span class="badge {badge_class}">{label}</span>',
        content_type='text/html',
    )

# --- Soft Delete User ---
@require_POST
def user_delete(request, uuid):
    profile      = get_object_or_404(UserProfile, uuid=uuid)
    profile_user = profile.user

    if profile_user == request.user:
        return JsonResponse({'success': False, 'error': 'You cannot delete your own account.'})

    profile.is_deleted = True
    profile.deleted_at = timezone.now()
    profile.save()

    profile_user.is_active = False
    profile_user.save()
    
    log_activity(
        user=request.user,
        action='deleted',
        model_name='User',
        object_repr=profile_user.get_full_name(),
        description=f"Soft-deleted user account '{profile_user.get_full_name()}' ({profile_user.email}).",
    )

    return JsonResponse({
        'success': True,
        "message": f"User {profile_user.get_full_name()} has been deleted.",
        'alert_type': 'success',
        "redirect_url": "",
    })

# --- Restore Deleted User ---

@require_POST
def user_restore(request, uuid):
    profile = get_object_or_404(UserProfile, uuid=uuid)
    profile_user = profile.user

    profile.is_deleted = False
    profile.deleted_at = None
    profile.save()

    profile_user.is_active = True
    profile_user.save()
    log_activity(
            user=request.user,
            action='updated',
            model_name='User',
            object_repr=profile_user.get_full_name(),
            description=f"Restored user account '{profile_user.get_full_name()}' ({profile_user.email}).",
        )
    return toast_success(
        request,
        f'User {profile_user.get_full_name()} has been restored successfully.',
        alert_type="success",
        redirect_url="/dashboard/users/deleted/",
    )
# --- Admin Password Reset ---

@require_POST
def user_reset_password(request, uuid):
    profile      = get_object_or_404(UserProfile, uuid=uuid)
    profile_user = profile.user

    password1 = request.POST.get('password1', '')
    password2 = request.POST.get('password2', '')

    errors = {}

    if not password1:
        errors['password1'] = 'Password is required.'
    elif len(password1) < 8:
        errors['password1'] = 'Password must be at least 8 characters.'
    elif password1 != password2:
        errors['password2'] = 'Passwords do not match.'

    if errors:
        oob_html = ''.join(
            f'<div id="error-{field}" hx-swap-oob="innerHTML">'
            f'<p class="text-danger small mb-0">{msg}</p>'
            f'</div>'
            for field, msg in errors.items()
        )
        return toast_error(
            request,
            "Please fix the errors below.",
            alert_type="danger",
            oob_content=oob_html,
        )

    profile_user.set_password(password1)
    profile_user.save()

    log_activity(
        user=request.user,
        action='updated',
        model_name='User',
        object_repr=profile_user.get_full_name(),
        description=f"Reset password for user '{profile_user.get_full_name()}' ({profile_user.email}).",
    )

    return toast_success(
        request,
        f"Password for {profile_user.get_full_name()} updated successfully.",
        alert_type="success",
        redirect_url=f"/dashboard/users/",
    )

# ─── Login History ───────────────────────────────────────────────────────────

def login_history_list(request):
    qs = LoginHistory.objects.select_related('user').all()

    # Filters
    status_filter = request.GET.get('status', '')
    search        = request.GET.get('search', '')

    if status_filter:
        qs = qs.filter(status=status_filter)
    if search:
        qs = qs.filter(
            Q(user__username__icontains=search)   |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search)  |
            Q(ip_address__icontains=search)
        )

    paginator = Paginator(qs, 10)
    page      = request.GET.get('page', 1)
    entries   = paginator.get_page(page)

    context = {
        'entries':       entries,
        'status_filter': status_filter,
        'search':        search,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/login_history_table.html', context)
    return render(request, 'mainDash/login_history_list.html', context)

# ─── User Activity ────────────────────────────────────────────────────────────

def user_activity_list(request):
    qs = UserActivity.objects.select_related('user').all()

    # Filters
    action_filter = request.GET.get('action', '')
    search        = request.GET.get('search', '')

    if action_filter:
        qs = qs.filter(action=action_filter)
    if search:
        qs = qs.filter(
        Q(user__username__icontains=search)    |
        Q(user__first_name__icontains=search)  |
        Q(user__last_name__icontains=search)   |
        Q(model_name__icontains=search)        |
        Q(description__icontains=search)
    )

    paginator = Paginator(qs, 10)
    page      = request.GET.get('page', 1)
    entries   = paginator.get_page(page)

    context = {
        'entries':       entries,
        'action_filter': action_filter,
        'search':        search,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/user_activity_table.html', context)
    return render(request, 'mainDash/user_activity_list.html', context)


# ─── Roles & Permissions ──────────────────────────────────────────────────────

def role_list(request):
    roles  = Group.objects.prefetch_related('permissions').all()
    search = request.GET.get('search', '')

    if search:
        roles = roles.filter(name__icontains=search)

    paginator = Paginator(roles, 10)
    page      = paginator.get_page(request.GET.get('page'))

    # attach token to each role in the page
    for role in page:
        role.token = encode_pk(role.pk)

    context = {
        'roles':  page,
        'search': search,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/role_dataTable.html', context)
    return render(request, 'mainDash/role_list.html', context)

def role_create(request):
    permissions = Permission.objects.select_related('content_type').all()

    if request.method == 'POST':
        name           = request.POST.get('name', '').strip()
        permission_ids = request.POST.getlist('permissions')

        errors = {}

        if not name:
            errors['name'] = 'Role name is required.'
        elif Group.objects.filter(name=name).exists():
            errors['name'] = 'A role with this name already exists.'

        if errors:
            oob_html = ''.join(
                f'<div id="error-{field}" hx-swap-oob="innerHTML">'
                f'<p class="text-danger small mb-0">{msg}</p>'
                f'</div>'
                for field, msg in errors.items()
            )
            return toast_error(
                request,
                "Please fix the errors below.",
                alert_type="danger",
                oob_content=oob_html,
            )

        role = Group.objects.create(name=name)
        role.permissions.set(permission_ids)

        log_activity(
            user=request.user,
            action='created',
            model_name='Role',
            object_repr=role.name,
            description=f"Created role '{role.name}' with {role.permissions.count()} permission(s)."
        )

        return toast_success(
            request,
            f"Role '{role.name}' created successfully.",
            alert_type="success",
            redirect_url="/dashboard/roles/",
        )

    return render(request, 'mainDash/role_create.html', {
        'permissions': permissions,
    })

def role_edit(request, token):
    pk = decode_pk(token)
    if pk is None:
        raise Http404

    role             = get_object_or_404(Group, pk=pk)
    permissions      = Permission.objects.select_related('content_type').all()
    role_permissions = set(role.permissions.values_list('pk', flat=True))

    if request.method == 'POST':
        name           = request.POST.get('name', '').strip()
        permission_ids = request.POST.getlist('permissions')

        errors = {}

        if not name:
            errors['name'] = 'Role name is required.'
        elif Group.objects.filter(name=name).exclude(pk=pk).exists():
            errors['name'] = 'A role with this name already exists.'

        if errors:
            oob_html = ''.join(
                f'<div id="error-{field}" hx-swap-oob="innerHTML">'
                f'<p class="text-danger small mb-0">{msg}</p>'
                f'</div>'
                for field, msg in errors.items()
            )
            return toast_error(
                request,
                "Please fix the errors below.",
                alert_type="danger",
                oob_content=oob_html,
            )

        role.name = name
        role.save()
        role.permissions.set(permission_ids)

        log_activity(
            user=request.user,
            action='updated',
            model_name='Role',
            object_repr=role.name,
            description=f"Updated role '{role.name}'."
        )

        return toast_success(
            request,
            f"Role '{role.name}' updated successfully.",
            alert_type="success",
            redirect_url="/dashboard/roles/",
        )

    return render(request, 'mainDash/role_edit.html', {
        'role':             role,
        'permissions':      permissions,
        'role_permissions': role_permissions,
        'token':            token,
    })

@require_POST
def role_delete(request, pk):
    role = get_object_or_404(Group, pk=pk)
    name = role.name

    log_activity(
        user=request.user,
        action='deleted',
        model_name='Role',
        object_repr=name,
        description=f"Deleted role '{name}'."
    )

    role.delete()
    return JsonResponse({
        'success':      True,
        'message':      f"Role '{name}' has been deleted.",
        'alert_type':   'success',
        'redirect_url': '',
    })

# Add to your existing views.py

# ── SHARED HELPER ──────────────────────────────────────────────────────────────
def _resolve_shipment(query: str):
    """
    Accept TRK-XXXXXXXXXX  → Order.tracking_number → first shipment
    Accept SHP-XXXXXX      → Shipment.shipment_number directly
    Returns (shipment, order) or (None, None).
    """
    query = query.strip().upper()

    tracking_qs = (
        ShipmentTrackingEvent.objects
        .select_related('recorded_by')
        .order_by('-created_at')
    )

    shipment_qs = (
        Shipment.objects
        .select_related('order', 'created_by')
        .prefetch_related(
            Prefetch('tracking_events', queryset=tracking_qs),
            'order__images',
        )
    )

    if query.startswith('SHP-'):
        shipment = shipment_qs.filter(shipment_number=query).first()
        return (shipment, shipment.order if shipment else None)

    if query.startswith('TRK-'):
        shipment = shipment_qs.filter(order__tracking_number=query).order_by('-created_at').first()
        return (shipment, shipment.order if shipment else None)

    return None, None


# ── 1. PUBLIC TRACKING PAGE ────────────────────────────────────────────────────
def public_shipment_tracking(request):
    form = TrackingSearchForm(request.GET or None)
    shipment = order = None
    not_found = False

    if form.is_valid():
        shipment, order = _resolve_shipment(form.cleaned_data['query'])
        if not shipment:
            not_found = True

    return render(request, 'mainDash/public_tracking.html', {
        'form': form,
        'shipment': shipment,
        'order': order,
        'not_found': not_found,
    })


# ── 2. STAFF DASHBOARD TRACKER ────────────────────────────────────────────────
def staff_shipment_tracking(request):
    form = TrackingSearchForm(request.GET or None)
    shipment = order = None
    not_found = False

    if form.is_valid():
        shipment, order = _resolve_shipment(form.cleaned_data['query'])
        if not shipment:
            not_found = True

    context = {
        'form': form,
        'shipment': shipment,
        'order': order,
        'not_found': not_found,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/tracking_result.html', context)
    return render(request, 'mainDash/staff_tracking.html', context)

# ── 3. TRACKING UPDATES ────────────────────────────────────────────────────────
def tracking_updates(request):
    search_form = TrackingSearchForm(request.GET or None)
    event_form  = ShipmentTrackingEventForm()
    shipment = order = None
    not_found = False

    # Resolve shipment from GET
    if search_form.is_valid():
        shipment, order = _resolve_shipment(search_form.cleaned_data['query'])
        if not shipment:
            not_found = True

    if request.method == 'POST':
        # Re-resolve shipment from hidden POST field
        shp_number = request.POST.get('shipment_number', '').strip().upper()
        shipment   = (
            Shipment.objects
            .select_related('order')
            .prefetch_related(
                Prefetch(
                    'tracking_events',
                    queryset=ShipmentTrackingEvent.objects
                    .select_related('recorded_by')
                    .order_by('-created_at'),
                ),
                'order__images',
            )
            .filter(shipment_number=shp_number)
            .first()
        )

        if not shipment:
            return toast_error(request, "Shipment not found. Please search again.")

        order      = shipment.order
        event_form = ShipmentTrackingEventForm(request.POST)

        if not event_form.is_valid():
            oob_html = ''.join(
                f'<div id="error-{field}" hx-swap-oob="innerHTML">'
                f'<p class="text-danger small mb-0">{msg}</p>'
                f'</div>'
                for field, msgs in event_form.errors.items()
                for msg in msgs
            )
            return toast_error(
                request,
                "Please fix the errors below.",
                alert_type="danger",
                oob_content=oob_html,
            )

        event              = event_form.save(commit=False)
        event.shipment     = shipment
        event.recorded_by  = request.user
        event.save()

        # Sync Shipment status
        new_status = event.status
        allowed    = Shipment.ALLOWED_TRANSITIONS.get(shipment.status, set())
        if new_status in allowed or new_status == shipment.status:
            shipment.status = new_status
            shipment.save(update_fields=['status', 'updated_at'])
            order_status = Shipment.ORDER_STATUS_MAP.get(new_status)
            if order_status:
                order.status     = order_status
                order.updated_by = request.user
                order.save(update_fields=['status', 'updated_by', 'updated_at'])

        log_activity(
            user=request.user,
            action='created',
            model_name='ShipmentTrackingEvent',
            object_repr=shipment.shipment_number,
            description=(
                f"Posted tracking update '{event.get_status_display()}' "
                f"on {shipment.shipment_number}"
                f"{' at ' + event.location if event.location else ''}."
            ),
        )

        return toast_success(
            request,
            f"Tracking update posted for {shipment.shipment_number}.",
            alert_type="success",
            redirect_url=f"{request.path}?query={shipment.shipment_number}",
        )

    context = {
        'search_form': search_form,
        'event_form':  event_form,
        'shipment':    shipment,
        'order':       order,
        'not_found':   not_found,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/update_result.html', context)
    return render(request, 'mainDash/tracking_updates.html', context)

# ── 4. TRACKING HISTORY ────────────────────────────────────────────────────────

def tracking_history(request):
    qs = (
        ShipmentTrackingEvent.objects
        .select_related('shipment', 'shipment__order', 'recorded_by')
        .order_by('-created_at')
    )

    q         = request.GET.get('q', '').strip()
    status    = request.GET.get('status', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to   = request.GET.get('date_to', '').strip()

    if q:
        qs = qs.filter(
            Q(shipment__shipment_number__icontains=q) |
            Q(shipment__order__tracking_number__icontains=q) |
            Q(shipment__order__order_number__icontains=q) |
            Q(location__icontains=q) |
            Q(recorded_by__username__icontains=q)
        )
    if status:
        qs = qs.filter(status=status)
    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)

    paginator = Paginator(qs, 15)
    page      = paginator.get_page(request.GET.get('page'))

    context = {
        'events':         page,
        'status_choices': Shipment.STATUS_CHOICES,
        'q':              q,
        'status':         status,
        'date_from':      date_from,
        'date_to':        date_to,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/history_dataTable.html', context)
    return render(request, 'mainDash/tracking_history.html', context)

# Report analyst

# ── SHARED: parse date range from GET params ──────────────────────
def _get_date_range(request):
    today     = date.today()
    date_from = request.GET.get('date_from', '')
    date_to   = request.GET.get('date_to', '')
    try:
        date_from = date.fromisoformat(date_from) if date_from else today - timedelta(days=30)
        date_to   = date.fromisoformat(date_to)   if date_to   else today
    except ValueError:
        date_from = today - timedelta(days=30)
        date_to   = today
    return date_from, date_to


# ── 1. SHIPMENT REPORTS ───────────────────────────────────────────

def shipment_reports(request):
    date_from, date_to = _get_date_range(request)

    qs = Shipment.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to,
    )

    # CSV export
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="shipment_report.csv"'
        writer = csv.writer(response)
        writer.writerow([
            'Shipment No', 'Order No', 'Status', 'Direction',
            'Customs Status', 'Carrier', 'Pickup Date',
            'Expected Delivery', 'Created At',
        ])
        for s in qs.select_related('order').order_by('-created_at'):
            writer.writerow([
                s.shipment_number, s.order.order_number,
                s.get_status_display(), s.get_shipment_direction_display(),
                s.get_customs_status_display(), s.carrier_name or '—',
                s.pickup_date or '—', s.expected_delivery_date or '—',
                s.created_at.strftime('%d/%m/%Y'),
            ])
        return response

    # Stats
    total        = qs.count()
    pending      = qs.filter(status='pending').count()
    in_transit   = qs.filter(status='in_transit').count()
    delivered    = qs.filter(status='delivered').count()
    cancelled    = qs.filter(status='cancelled').count()
    returned     = qs.filter(status='returned').count()
    outbound     = qs.filter(shipment_direction='outbound').count()
    inbound      = qs.filter(shipment_direction='inbound').count()

    # Chart: shipments per day
    daily = (
        qs.annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )
    chart_labels  = [str(d['day']) for d in daily]
    chart_series  = [d['count'] for d in daily]

    # Status breakdown for donut
    status_labels = ['Pending', 'In Transit', 'Delivered', 'Cancelled', 'Returned']
    status_data   = [pending, in_transit, delivered, cancelled, returned]

    # Recent shipments table
    shipments_qs = qs.select_related('order').order_by('-created_at')
    paginator    = Paginator(shipments_qs, 10)
    page         = paginator.get_page(request.GET.get('page'))

    context = {
        'total': total, 'pending': pending, 'in_transit': in_transit,
        'delivered': delivered, 'cancelled': cancelled, 'returned': returned,
        'outbound': outbound, 'inbound': inbound,
        'chart_labels': chart_labels, 'chart_series': chart_series,
        'status_labels': status_labels, 'status_data': status_data,
        'shipments': page,
        'date_from': date_from,
        'date_to':   date_to,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/shipment_reports_dataTable.html', context)
    return render(request, 'mainDash/shipment_reports.html', context)

# ── 2. DELIVERY PERFORMANCE ───────────────────────────────────────

def delivery_performance(request):
    date_from, date_to = _get_date_range(request)

    qs = Shipment.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to,
    )

    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="delivery_performance.csv"'
        writer = csv.writer(response)
        writer.writerow([
            'Shipment No', 'Status', 'Pickup Date',
            'Expected Delivery', 'Delivered At', 'On Time',
        ])
        for s in qs.filter(status='delivered').select_related('order').order_by('-delivered_at'):
            on_time = '—'
            if s.delivered_at and s.expected_delivery_date:
                on_time = 'Yes' if s.delivered_at.date() <= s.expected_delivery_date else 'No'
            writer.writerow([
                s.shipment_number, s.get_status_display(),
                s.pickup_date or '—', s.expected_delivery_date or '—',
                s.delivered_at.strftime('%d/%m/%Y %H:%M') if s.delivered_at else '—',
                on_time,
            ])
        return response

    delivered_qs = qs.filter(status='delivered')
    total        = qs.count()
    delivered    = delivered_qs.count()
    cancelled    = qs.filter(status='cancelled').count()
    in_transit   = qs.filter(status='in_transit').count()

    # On-time: delivered on or before expected_delivery_date
    on_time = sum(
        1 for s in delivered_qs
        if s.delivered_at and s.expected_delivery_date
        and s.delivered_at.date() <= s.expected_delivery_date
    )
    late        = delivered - on_time if delivered else 0
    on_time_pct = round((on_time / delivered * 100), 1) if delivered else 0

    # Monthly delivered chart
    monthly = (
        delivered_qs
        .annotate(month=TruncMonth('delivered_at'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    chart_labels = [d['month'].strftime('%b %Y') if d['month'] else '' for d in monthly]
    chart_series = [d['count'] for d in monthly]

    recent_qs = delivered_qs.select_related('order').order_by('-delivered_at')
    paginator = Paginator(recent_qs, 10)
    page      = paginator.get_page(request.GET.get('page'))

    context = {
        'total': total, 'delivered': delivered, 'cancelled': cancelled,
        'in_transit': in_transit, 'on_time': on_time, 'late': late,
        'on_time_pct': on_time_pct,
        'chart_labels': chart_labels, 'chart_series': chart_series,
        'recent':    page,        # ← only once, the page object
        'date_from': date_from,
        'date_to':   date_to,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/delivery_performance_dataTable.html', context)
    return render(request, 'mainDash/delivery_performance.html', context)

# ── 3. REVENUE ANALYTICS ──────────────────────────────────────────

def revenue_analytics(request):
    date_from, date_to = _get_date_range(request)

    inv_qs = Invoice.objects.filter(
        issue_date__gte=date_from,
        issue_date__lte=date_to,
    )

    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="revenue_analytics.csv"'
        writer = csv.writer(response)
        writer.writerow([
            'Invoice No', 'Customer', 'Status', 'Currency',
            'Total Amount', 'Amount Paid', 'Balance Due', 'Issue Date',
        ])
        for inv in inv_qs.order_by('-issue_date'):
            writer.writerow([
                inv.invoice_number, inv.customer_name,
                inv.get_status_display(), inv.currency,
                inv.total_amount, inv.amount_paid,
                inv.balance_due, inv.issue_date,
            ])
        return response

    totals        = inv_qs.aggregate(
        total_invoiced=Sum('total_amount'),
        total_paid=Sum('amount_paid'),
    )
    total_invoiced = totals['total_invoiced'] or 0
    total_paid     = totals['total_paid']     or 0
    outstanding    = total_invoiced - total_paid
    total_invoices = inv_qs.count()
    paid_count     = inv_qs.filter(status='paid').count()
    overdue_count  = inv_qs.filter(status='overdue').count()

    # Monthly revenue chart
    monthly = (
        inv_qs
        .annotate(month=TruncMonth('issue_date'))
        .values('month')
        .annotate(
            invoiced=Sum('total_amount'),
            paid=Sum('amount_paid'),
        )
        .order_by('month')
    )
    chart_labels   = [d['month'].strftime('%b %Y') for d in monthly]
    chart_invoiced = [float(d['invoiced'] or 0) for d in monthly]
    chart_paid     = [float(d['paid'] or 0) for d in monthly]

    # Currency breakdown
    currency_data = (
        inv_qs
        .values('currency')
        .annotate(total=Sum('total_amount'))
        .order_by('-total')
    )

    invoices_qs = inv_qs.order_by('-issue_date')
    paginator   = Paginator(invoices_qs, 10)
    page        = paginator.get_page(request.GET.get('page'))

    context = {
        'total_invoiced': total_invoiced, 'total_paid': total_paid,
        'outstanding': outstanding, 'total_invoices': total_invoices,
        'paid_count': paid_count, 'overdue_count': overdue_count,
        'chart_labels': chart_labels,
        'chart_invoiced': chart_invoiced, 'chart_paid': chart_paid,
        'currency_data': currency_data,
        'invoices':  page,
        'date_from': date_from,
        'date_to':   date_to,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/revenue_analytics_dataTable.html', context)
    return render(request, 'mainDash/revenue_analytics.html', context)

# ── 4. CUSTOMER ANALYTICS ─────────────────────────────────────────
def customer_analytics(request):
    date_from, date_to = _get_date_range(request)

    orders_qs = Order.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to,
    )

    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="customer_analytics.csv"'
        writer = csv.writer(response)
        writer.writerow([
            'Customer Name', 'Email', 'Phone',
            'Total Orders', 'Destination Country',
        ])
        for c in (
            orders_qs
            .values('customer_name', 'customer_email',
                    'customer_phone', 'receiver_country')
            .annotate(order_count=Count('id'))
            .order_by('-order_count')[:100]
        ):
            writer.writerow([
                c['customer_name'], c['customer_email'] or '—',
                c['customer_phone'], c['order_count'],
                c['receiver_country'],
            ])
        return response

    total_orders     = orders_qs.count()
    unique_customers = orders_qs.values('customer_name').distinct().count()

    # Top destination countries  ← this was missing
    top_destinations = (
        orders_qs
        .values('receiver_country')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )

    # Chart data
    monthly = (
        orders_qs
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    chart_labels = [d['month'].strftime('%b %Y') for d in monthly]
    chart_series = [d['count'] for d in monthly]

    dest_labels = [d['receiver_country'] for d in top_destinations]
    dest_data   = [d['count'] for d in top_destinations]

    # Paginated customer table
    top_customers_qs = (
        orders_qs
        .values('customer_name', 'customer_email', 'receiver_country')
        .annotate(order_count=Count('id'))
        .order_by('-order_count')
    )
    paginator = Paginator(top_customers_qs, 10)
    page      = paginator.get_page(request.GET.get('page'))

    context = {
        'total_orders':      total_orders,
        'unique_customers':  unique_customers,
        'chart_labels':      chart_labels,
        'chart_series':      chart_series,
        'dest_labels':       dest_labels,
        'dest_data':         dest_data,
        'top_customers':     page,
        'date_from':         date_from,
        'date_to':           date_to,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/customer_analytics_dataTable.html', context)
    return render(request, 'mainDash/customer_analytics.html', context)
# ── 5. DRIVER / VEHICLE ANALYTICS ────────────────────────────────

def driver_analytics(request):
    date_from, date_to = _get_date_range(request)

    shipments_qs = Shipment.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to,
        carrier_name__isnull=False,
    ).exclude(carrier_name='')

    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="driver_analytics.csv"'
        writer = csv.writer(response)
        writer.writerow(['Carrier / Driver', 'Total Shipments', 'Delivered', 'In Transit', 'Cancelled'])
        for row in (
            shipments_qs
            .values('carrier_name')
            .annotate(
                total=Count('id'),
                delivered=Count('id', filter=Q(status='delivered')),
                in_transit=Count('id', filter=Q(status='in_transit')),
                cancelled=Count('id', filter=Q(status='cancelled')),
            )
            .order_by('-total')
        ):
            writer.writerow([
                row['carrier_name'], row['total'],
                row['delivered'], row['in_transit'], row['cancelled'],
            ])
        return response

    total_shipments  = shipments_qs.count()
    active_carriers  = shipments_qs.values('carrier_name').distinct().count()

    # Per carrier stats
    carrier_stats_qs = (
    shipments_qs
    .values('carrier_name')
    .annotate(
        total=Count('id'),
        delivered=Count('id', filter=Q(status='delivered')),
        in_transit=Count('id', filter=Q(status='in_transit')),
        cancelled=Count('id', filter=Q(status='cancelled')),
    )
    .order_by('-total')
    )
    paginator = Paginator(carrier_stats_qs, 10)
    page      = paginator.get_page(request.GET.get('page'))

    # Vehicle status breakdown
    vehicle_status = (
        Vehicle.objects
        .values('status')
        .annotate(count=Count('id'))
    )

    # Routes by status
    routes_qs = Route.objects.filter(
        planned_date__gte=date_from,
        planned_date__lte=date_to,
    )
    route_stats = (
        routes_qs
        .values('status')
        .annotate(count=Count('id'))
    )

    # Chart: top 8 carriers
    top_carriers   = list(carrier_stats_qs[:8])
    chart_labels   = [c['carrier_name'] for c in top_carriers]
    chart_delivered = [c['delivered'] for c in top_carriers]
    chart_transit   = [c['in_transit'] for c in top_carriers]
    chart_cancelled = [c['cancelled'] for c in top_carriers]

    context = {
        'total_shipments': total_shipments,
        'active_carriers': active_carriers,
        'carrier_stats': page,
        'date_from':     date_from,
        'date_to':       date_to,
        'vehicle_status': vehicle_status,
        'route_stats': route_stats,
        'chart_labels': chart_labels,
        'chart_delivered': chart_delivered,
        'chart_transit': chart_transit,
        'chart_cancelled': chart_cancelled,
        
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/driver_analytics_dataTable.html', context)
    return render(request, 'mainDash/driver_analytics.html', context)

# ── 6. WAREHOUSE ANALYTICS ────────────────────────────────────────

def warehouse_analytics(request):
    date_from, date_to = _get_date_range(request)

    items_qs = WarehouseItem.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to,
    )

    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="warehouse_analytics.csv"'
        writer = csv.writer(response)
        writer.writerow([
            'Warehouse', 'Category', 'Status', 'Customer',
            'Destination', 'Quantity', 'Weight (kg)', 'Received Date',
        ])
        for item in items_qs.select_related('warehouse').order_by('-created_at'):
            writer.writerow([
                item.warehouse.name, item.get_category_display(),
                item.get_status_display(), item.customer_name,
                item.destination_country, item.quantity,
                item.weight_kg or '—', item.received_date,
            ])
        return response

    total_items  = items_qs.count()
    in_stock     = items_qs.filter(status='in_stock').count()
    dispatched   = items_qs.filter(status='dispatched').count()
    held         = items_qs.filter(status='held').count()
    total_weight = items_qs.aggregate(w=Sum('weight_kg'))['w'] or 0
    items_list_qs = items_qs.select_related('warehouse').order_by('-created_at')
    paginator     = Paginator(items_list_qs, 20)
    page          = paginator.get_page(request.GET.get('page'))

    # Per warehouse breakdown
    per_warehouse = (
        items_qs
        .values('warehouse__name')
        .annotate(
            total=Count('id'),
            in_stock=Count('id', filter=Q(status='in_stock')),
            dispatched=Count('id', filter=Q(status='dispatched')),
            held=Count('id', filter=Q(status='held')),
        )
        .order_by('-total')
    )

    # Category breakdown
    category_data = (
        items_qs
        .values('category')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    # Monthly intake chart
    monthly = (
        items_qs
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    chart_labels = [d['month'].strftime('%b %Y') for d in monthly]
    chart_series = [d['count'] for d in monthly]

    # Status donut
    status_labels = ['In Stock', 'Dispatched', 'On Hold']
    status_data   = [in_stock, dispatched, held]

    # Top destinations
    top_destinations = (
        items_qs
        .values('destination_country')
        .annotate(count=Count('id'))
        .order_by('-count')[:8]
    )

    context = {
        'total_items': total_items, 'in_stock': in_stock,
        'dispatched': dispatched, 'held': held,
        'total_weight': total_weight,
        'per_warehouse': per_warehouse,
        'category_data': category_data,
        'chart_labels': chart_labels, 'chart_series': chart_series,
        'status_labels': status_labels, 'status_data': status_data,
        'top_destinations': top_destinations,
        'items_page': page,
        'date_from':  date_from,
        'date_to':    date_to,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/warehouse_analytics_dataTable.html', context)
    return render(request, 'mainDash/warehouse_analytics.html', context)

def is_admin(user):
    return user.is_staff or user.is_superuser


# ── 1. GENERAL SETTINGS ───────────────────────────────────────────

@user_passes_test(is_admin)
def general_settings(request):
    instance = SystemSetting.get()

    if request.method == 'POST':
        form = GeneralSettingsForm(request.POST, request.FILES, instance=instance)

        if not form.is_valid():
            oob_html = ''.join(
                f'<div id="error-{field}" hx-swap-oob="innerHTML">'
                f'<p class="text-danger small mb-0">{msg}</p>'
                f'</div>'
                for field, msgs in form.errors.items()
                for msg in msgs
            )
            return toast_error(
                request,
                'Please fix the errors below.',
                alert_type='danger',
                oob_content=oob_html,
            )

        s = form.save(commit=False)
        s.updated_by = request.user
        s.save()
        log_activity(
            user=request.user,
            action='updated',
            model_name='SystemSetting',
            object_repr='General Settings',
            description='Updated general company settings.',
        )
        return toast_success(
            request,
            'General settings saved successfully.',
            alert_type='success',
        )

    form    = GeneralSettingsForm(instance=instance)
    context = {'form': form, 'setting': instance}
    return render(request, 'mainDash/general_settings.html', context)

# ── 2. EMAIL CONFIGURATION ────────────────────────────────────────
@user_passes_test(is_admin)
def email_config(request):
    instance = SystemSetting.get()

    if request.method == 'POST':
        # Test email action
        if request.POST.get('action') == 'test_email':
            recipient = request.POST.get('test_recipient', '').strip()
            if not recipient:
                return toast_error(request, 
                                   'Please enter a recipient email to test.',
                                    alert_type='danger',
                                    oob_content=oob_html
                                    )
            try:
                send_mail(
                    subject='TDSSUK — Test Email',
                    message='This is a test email from your TDSSUK dashboard.',
                    from_email=instance.email_from_address or 'noreply@tdssuk.com',
                    recipient_list=[recipient],
                    fail_silently=False,
                )
                return toast_success(request, f'Test email sent to {recipient}.', alert_type='success',)
            except Exception as e:
                return toast_error(request, f'Failed to send test email: {str(e)}',
                                   alert_type="danger",)

        form = EmailConfigForm(request.POST, instance=instance)
        if not form.is_valid():
            oob_html = ''.join(
                f'<div id="error-{field}" hx-swap-oob="innerHTML">'
                f'<p class="text-danger small mb-0">{msg}</p>'
                f'</div>'
                for field, msgs in form.errors.items()
                for msg in msgs
            )
            return toast_error(
                request,
                'Please fix the errors below.',
                alert_type='danger',
                oob_content=oob_html,
            )

        s = form.save(commit=False)
        # Only update password if a new one was entered
        if not form.cleaned_data.get('smtp_password'):
            s.smtp_password = instance.smtp_password
        s.updated_by = request.user
        s.save()
        log_activity(
            user=request.user,
            action='updated',
            model_name='SystemSetting',
            object_repr='Email Configuration',
            description='Updated SMTP/email configuration.',
        )
        return toast_success(request, 
                             'Email configuration saved.', 
                             alert_type="success")

    form = EmailConfigForm(instance=instance)
    context = {'form': form, 'setting': instance}
        
    return render(request, 'mainDash/email_config.html', context)

# ── 3. AUDIT LOGS ─────────────────────────────────────────────────
@user_passes_test(is_admin)
def audit_logs(request):
    HIGH_SEVERITY_ACTIONS = ['deleted', 'updated']

    qs = (
        UserActivity.objects
        .select_related('user')
        .filter(action__in=HIGH_SEVERITY_ACTIONS)
        .order_by('-timestamp')
    )

    q         = request.GET.get('q', '').strip()
    action    = request.GET.get('action', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to   = request.GET.get('date_to', '').strip()

    if q:
        qs = qs.filter(
            Q(user__username__icontains=q)  |
            Q(object_repr__icontains=q)      |
            Q(model_name__icontains=q)       |
            Q(description__icontains=q)
        )
    if action:
        qs = qs.filter(action=action)
    if date_from:
        qs = qs.filter(timestamp__date__gte=date_from)
    if date_to:
        qs = qs.filter(timestamp__date__lte=date_to)

    paginator = Paginator(qs, 10)
    page      = paginator.get_page(request.GET.get('page'))

    context = {
        'logs':      page,
        'actions':   HIGH_SEVERITY_ACTIONS,
        'q':         q,
        'action':    action,
        'date_from': date_from,
        'date_to':   date_to,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/audit_logs_table.html', context)
    return render(request, 'mainDash/audit_logs.html', context)

# ── 4. SECURITY SETTINGS ──────────────────────────────────────────
@user_passes_test(is_admin)
def security_settings(request):
    instance = SystemSetting.get()

    if request.method == 'POST':
        form = SecuritySettingsForm(request.POST, instance=instance)
        if not form.is_valid():
            return render_form_errors_oob(request, form)
            
        s = form.save(commit=False)
        s.updated_by = request.user
        s.save()
        log_activity(
            user=request.user,
            action='updated',
            model_name='SystemSetting',
            object_repr='Security Settings',
            description='Updated security policy settings.',
        )
        return toast_success(request, 'Security settings saved.', alert_type='success',)

    form = SecuritySettingsForm(instance=instance)

    # Use LoginHistory instead of ActivityLog
    recent_logins = (
        LoginHistory.objects
        .select_related('user')
        .order_by('-timestamp')[:10]
    )

    context = {
        'form':          form,
        'setting':       instance,
        'recent_logins': recent_logins,
    }

    return render(request, 'mainDash/security_settings.html', context)

# ── 5. BACKUP & RESTORE ───────────────────────────────────────────

@user_passes_test(is_admin)
def backup_restore(request):

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'backup':
            try:
                db       = django_settings.DATABASES['default']
                db_name  = db['NAME']
                db_user  = db['USER']
                db_pass  = db.get('PASSWORD', '')
                db_host  = db.get('HOST', 'localhost')
                db_port  = db.get('PORT', '3306')

                backup_dir = os.path.join(django_settings.MEDIA_ROOT, 'backups')
                os.makedirs(backup_dir, exist_ok=True)

                timestamp   = timezone.now().strftime('%Y%m%d_%H%M%S')
                backup_name = f'db_backup_{timestamp}.sql'
                backup_path = os.path.join(backup_dir, backup_name)

                config_path = os.path.join(backup_dir, '.my.cnf')
                with open(config_path, 'w') as f:
                    f.write(f'[client]\nuser={db_user}\npassword={db_pass}\nhost={db_host}\nport={db_port}\n')

                with open(backup_path, 'w') as out:
                    result = subprocess.run(
                        ['mysqldump', f'--defaults-file={config_path}', db_name],
                        stdout=out,
                        stderr=subprocess.PIPE,
                        text=True,
                    )

                os.remove(config_path)

                if result.returncode != 0:
                    return toast_error(request, f'Backup failed: {result.stderr}', alert_type='danger')

                size_kb = os.path.getsize(backup_path) // 1024
                BackupLog.objects.create(
                    filename   = backup_name,
                    size_kb    = size_kb,
                    created_by = request.user,
                    notes      = 'Manual backup',
                )
                log_activity(
                    user        = request.user,
                    action      = 'backup',
                    model_name  = 'BackupLog',
                    object_repr = backup_name,
                    description = f'Manual MySQL backup created: {backup_name} ({size_kb} KB)',
                )
                return toast_success(request, f'Backup created: {backup_name} ({size_kb} KB)', alert_type='success')

            except FileNotFoundError:
                return toast_error(
                    request,
                    'mysqldump not found. Make sure MySQL is installed and added to your system PATH.',
                    alert_type='danger',
                )
            except Exception as e:
                return toast_error(request, f'Backup failed: {str(e)}', alert_type='danger')

        if action == 'delete_backup':
            filename = request.POST.get('filename', '').strip()
            try:
                backup_path = os.path.join(django_settings.MEDIA_ROOT, 'backups', filename)
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                BackupLog.objects.filter(filename=filename).delete()
                log_activity(
                    user        = request.user,
                    action      = 'deleted',
                    model_name  = 'BackupLog',
                    object_repr = filename,
                    description = f'Backup file deleted: {filename}',
                )
                return toast_success(request, f'Backup {filename} deleted.', alert_type='success')
            except Exception as e:
                return toast_error(request, f'Delete failed: {str(e)}', alert_type='danger')

    backup_logs = BackupLog.objects.all()
    return render(request, 'mainDash/backup_restore.html', {'backup_logs': backup_logs})

# ── 6. ACTIVITY LOGS ──────────────────────────────────────────────
@user_passes_test(is_admin)
def activity_logs(request):
    qs = (
        UserActivity.objects
        .select_related('user')
        .order_by('-timestamp')
    )

    q         = request.GET.get('q', '').strip()
    action    = request.GET.get('action', '').strip()
    user_id   = request.GET.get('user_id', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to   = request.GET.get('date_to', '').strip()

    if q:
        qs = qs.filter(
            Q(user__username__icontains=q)  |
            Q(object_repr__icontains=q)      |
            Q(model_name__icontains=q)       |
            Q(description__icontains=q)
        )
    if action:
        qs = qs.filter(action=action)
    if user_id:
        qs = qs.filter(user_id=user_id)
    if date_from:
        qs = qs.filter(timestamp__date__gte=date_from)
    if date_to:
        qs = qs.filter(timestamp__date__lte=date_to)

    paginator = Paginator(qs, 10)
    page      = paginator.get_page(request.GET.get('page'))

    from django.contrib.auth import get_user_model
    User  = get_user_model()
    users = User.objects.filter(is_active=True).order_by('username')

    ACTION_CHOICES = ['created', 'updated', 'deleted']

    context = {
        'logs':           page,
        'users':          users,
        'action_choices': ACTION_CHOICES,
        'q':              q,
        'action':         action,
        'user_id':        user_id,
        'date_from':      date_from,
        'date_to':        date_to,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/activity_logs_table.html', context)
    return render(request, 'mainDash/activity_logs.html', context)


# ── PROFILE ───────────────────────────────────────────────────
def profile(request):
    profile_form   = ProfileUpdateForm(instance=request.user)
    password_form  = ChangePasswordForm(user=request.user)

    return render(request, 'mainDash/profile.html', {
        'profile_form':  profile_form,
        'password_form': password_form,
    })


def profile_update(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if not form.is_valid():
            oob_html = ''.join(
                f'<div id="error-{field}" hx-swap-oob="innerHTML">'
                f'<p class="text-danger small mb-0">{msg}</p></div>'
                for field, msgs in form.errors.items() for msg in msgs
            )
            return toast_error(request, 'Please fix the errors below.',
                               alert_type='danger', oob_content=oob_html)
        form.save()
        log_activity(user=request.user, action='updated',
                     model_name='User', object_repr=request.user.username,
                     description='Updated profile information.')
        return toast_success(request, 'Profile updated successfully.', alert_type='success')
    return redirect('profile')


def change_password(request):
    if request.method == 'POST':
        form = ChangePasswordForm(user=request.user, data=request.POST)
        if not form.is_valid():
            oob_html = ''.join(
                f'<div id="error-pwd-{field}" hx-swap-oob="innerHTML">'
                f'<p class="text-danger small mb-0">{msg}</p></div>'
                for field, msgs in form.errors.items() for msg in msgs
            )
            return toast_error(request, 'Please fix the errors below.',
                               alert_type='danger', oob_content=oob_html)
        request.user.set_password(form.cleaned_data['new_password'])
        request.user.save()
        update_session_auth_hash(request, request.user)
        log_activity(user=request.user, action='updated',
                     model_name='User', object_repr=request.user.username,
                     description='Changed account password.')
        return toast_success(request, 'Password changed successfully.', alert_type='success')
    return redirect('profile')


# ── NOTIFICATIONS ─────────────────────────────────────────────

def notifications_list(request):
    notifications_qs = Notification.objects.filter(user=request.user)
    unread_count  = notifications_qs.filter(is_read=False).count()

    paginator = Paginator(notifications_qs, 10)
    page_obj  = paginator.get_page(request.GET.get('page', 10))

    for notifications_qs in page_obj:
        notifications_qs.token = encode_pk(notifications_qs.pk)

    context = {
        'notifications': page_obj,
        'unread_count':  unread_count,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/notifications_listTable.html', context)
    return render(request, 'mainDash/notifications.html', context)


def notification_mark_read(request, pk):
    Notification.objects.filter(pk=pk, user=request.user).update(is_read=True)
    return redirect(request.POST.get('next', 'notifications_list'))


def notifications_mark_all_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return toast_success(request, 'All notifications marked as read.', alert_type='success')


def notifications_bell(request):
    notifications = Notification.objects.filter(user=request.user, is_read=False)[:10]
    unread_count  = Notification.objects.filter(user=request.user, is_read=False).count()
    return render(request, 'mainDash/components/notifications_bell.html', {
        'notifications': notifications,
        'unread_count':  unread_count,
    })


# ── SUPPORT TICKETS ───────────────────────────────────────────

def ticket_list(request):
    q      = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')

    tickets = SupportTicket.objects.select_related('submitted_by', 'assigned_to')

    if not request.user.is_staff:
        tickets = tickets.filter(submitted_by=request.user)
    if q:
        tickets = tickets.filter(
            Q(ticket_number__icontains=q) |
            Q(subject__icontains=q) |
            Q(submitted_by__first_name__icontains=q) |
            Q(submitted_by__last_name__icontains=q)
        )
    if status:
        tickets = tickets.filter(status=status)

    tickets  = tickets.order_by('-created_at')
    paginator = Paginator(tickets, 10)
    page_obj  = paginator.get_page(request.GET.get('page', 1))

    for ticket in page_obj:
        ticket.token = encode_pk(ticket.pk)


    context = {
        'tickets':  page_obj,
        'q':        q,
        'status':   status,
    }
    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/ticket_dataTable.html', context)
    return render(request, 'mainDash/ticket_list.html', context)


def ticket_create(request):
    if request.method == 'POST':
        form = SupportTicketForm(user=request.user, data=request.POST)
        if not form.is_valid():
            oob_html = ''.join(
                f'<div id="error-{field}" hx-swap-oob="innerHTML">'
                f'<p class="text-danger small mb-0">{msg}</p></div>'
                for field, msgs in form.errors.items() for msg in msgs
            )
            return toast_error(request, 'Please fix the errors below.',
                               alert_type='danger', oob_content=oob_html)

        ticket              = form.save(commit=False)
        ticket.submitted_by = request.user
        # If logged-in user, always sync email/name from account
        if request.user.is_authenticated:
            ticket.submitter_email = request.user.email
            ticket.submitter_name  = request.user.get_full_name()
        ticket.save()

        # Notify all staff
        staff_users = User.objects.filter(is_staff=True).exclude(pk=request.user.pk)
        for staff in staff_users:
            notify(
                user       = staff,
                title      = f'New Ticket: {ticket.ticket_number}',
                message    = f'{ticket.submitter_name} opened: {ticket.subject}',
                notif_type = 'ticket',
                url        = f'/dashboard/tickets/{encode_pk(ticket.pk)}/',
            )

        log_activity(user=request.user, action='created',
                     model_name='SupportTicket', object_repr=ticket.ticket_number,
                     description=f'Opened support ticket: {ticket.subject}')

        return toast_success(
            request,
            f'Ticket {ticket.ticket_number} submitted. We will reply to {ticket.submitter_email}.',
            alert_type='success',
            redirect_url=f'/dashboard/tickets/{encode_pk(ticket.pk)}/'
        )

    form = SupportTicketForm(user=request.user)
    return render(request, 'mainDash/ticket_create.html', {'form': form})


def ticket_detail(request, token):
    pk     = decode_pk(token)
    if pk is None:
        raise Http404
    ticket = get_object_or_404(SupportTicket, pk=pk)
    if not request.user.is_staff and ticket.submitted_by != request.user:
        return redirect('ticket_list')

    if request.method == 'POST':
        action = request.POST.get('action')

        # Reply
        if action == 'reply':
            form = TicketReplyForm(request.POST)
            if not form.is_valid():
                oob_html = ''.join(
                    f'<div id="error-{field}" hx-swap-oob="innerHTML">'
                    f'<p class="text-danger small mb-0">{msg}</p></div>'
                    for field, msgs in form.errors.items() for msg in msgs
                )
                return toast_error(request, 'Please fix the errors.',
                                   alert_type='danger', oob_content=oob_html)
            reply        = form.save(commit=False)
            reply.ticket = ticket
            reply.author = request.user
            reply.save()

            # Send email to submitter if staff replied
            if request.user.is_staff:
                send_ticket_reply_email(ticket, reply) 

            # In-app notification to ticket owner
            if request.user.is_staff and ticket.submitted_by:
                notify(
                    user       = ticket.submitted_by,
                    title      = f'Reply on {ticket.ticket_number}',
                    message    = f'Staff replied to your ticket: {ticket.subject}',
                    notif_type = 'ticket',
                    url        = f'/dashboard/tickets/{encode_pk(ticket.pk)}/',
                )
            # activity recorded
            log_activity(user=request.user, action='created',
                         model_name='TicketReply', object_repr=ticket.ticket_number,
                         description=f'Replied to ticket {ticket.ticket_number}')
            return toast_success(request, 'Reply posted.', alert_type='success',
                                 redirect_url=f'/dashboard/tickets/{encode_pk(ticket.pk)}/')

        # Status change (staff only)
        if action == 'update_status' and request.user.is_staff:
            new_status = request.POST.get('status')
            if new_status in dict(SupportTicket.STATUS):
                old_status    = ticket.status
                ticket.status = new_status
                if new_status == 'resolved':
                    from django.utils import timezone
                    ticket.resolved_at = timezone.now()
                ticket.save()
                # ← send status email to submitter
                send_ticket_status_email(ticket)

                notify(
                    user       = ticket.submitted_by,
                    title      = f'Ticket {ticket.ticket_number} Updated',
                    message    = f'Status changed from {old_status} to {new_status}.',
                    notif_type = 'ticket',
                    url        = f'/dashboard/tickets/{encode_pk(ticket.pk)}/',
                )
                log_activity(user=request.user, action='updated',
                             model_name='SupportTicket', object_repr=ticket.ticket_number,
                             description=f'Status changed to {new_status}')
                return toast_success(request, f'Ticket status updated to {new_status}.', alert_type='success',
                                     redirect_url=f'/dashboard/tickets/{encode_pk(ticket.pk)}/')

    reply_form = TicketReplyForm()
    return render(request, 'mainDash/ticket_detail.html', {
        'ticket':     ticket,
        'reply_form': reply_form,
        'token':      token,
    })
 

# ── PROMO CODE ───────────────────────────────────────────

def promo_code_list(request):
    q      = request.GET.get('q', '').strip()
    filter = request.GET.get('filter', '')

    codes = PromoCode.objects.select_related('created_by')

    if q:
        codes = codes.filter(code__icontains=q)

    if filter == 'used':
        codes = codes.filter(used_count__gt=0)
    elif filter == 'unused':
        codes = codes.filter(used_count=0)
    elif filter == 'expired':
        codes = codes.filter(valid_until__lt=timezone.now())

    paginator = Paginator(codes, 10)
    page_obj  = paginator.get_page(request.GET.get('page', 1))

    for code in page_obj:
        code.token = encode_pk(code.pk)

    context = {
        'codes':  page_obj,
        'q':      q,
        'filter': filter,
    }
    if request.headers.get('HX-Request'):
        return render(request, 'mainDash/components/promo_code_dataTable.html', context)
    return render(request, 'mainDash/promo_code_list.html', context)


def promo_code_create(request):
    if request.method == 'POST':
        form = PromoCodeForm(request.POST)
        if not form.is_valid():
            oob_html = ''.join(
                f'<div id="error-{field}" hx-swap-oob="innerHTML">'
                f'<p class="text-danger small mb-0">{msg}</p></div>'
                for field, msgs in form.errors.items() for msg in msgs
            )
            return toast_error(request, 
                               'Please fix the errors below.',
                               alert_type='danger', 
                               oob_content=oob_html
                               )
        
        promo = form.save(commit=False)
        promo.created_by = request.user
        promo.save()
        log_activity(user=request.user, action='created',
                     model_name='PromoCode', object_repr=promo.code,
                     description=f'Created promo code: {promo.code}')
        return toast_success(request, 
                             f'Promo code {promo.code} created.',
                             alert_type='success',
                             redirect_url='/dashboard/promo-codes/'
                             )
    form = PromoCodeForm()
    return render(request, 'mainDash/promo_code_create.html', {'form': form})


def promo_code_edit(request, token):
    pk    = decode_pk(token)
    if pk is None:
        raise Http404
    promo = get_object_or_404(PromoCode, pk=pk)

    if request.method == 'POST':
        form = PromoCodeForm(request.POST, instance=promo)
        if not form.is_valid():
            oob_html = ''.join(
                f'<div id="error-{field}" hx-swap-oob="innerHTML">'
                f'<p class="text-danger small mb-0">{msg}</p></div>'
                for field, msgs in form.errors.items() for msg in msgs
            )
            return toast_error(request, 
                               'Please fix the errors below.',
                               alert_type='danger', 
                               oob_content=oob_html
                               )
        form.save()
        log_activity(user=request.user, action='updated',
                     model_name='PromoCode', object_repr=promo.code,
                     description=f'Updated promo code: {promo.code}')
        return toast_success(request, 
                             f'Promo code {promo.code} updated.',
                             alert_type='success',
                             redirect_url='/dashboard/promo-codes/'
                             )
    else:
        form = PromoCodeForm(instance=promo)

    return render(request, 'mainDash/promo_code_edit.html', {
        'form':  form,
        'promo': promo,
        'token': token,
    })

@require_POST
def promo_code_delete(request, token):
    pk    = decode_pk(token)
    if pk is None:
        raise Http404
    promo = get_object_or_404(PromoCode, pk=pk)
    code  = promo.code
    promo.delete()

    log_activity(user=request.user, action='deleted',
                 model_name='PromoCode', object_repr=code,
                 description=f'Deleted promo code: {code}')
    return JsonResponse({
        'success':      True,
        'message':      f"Promo code {code} deleted.",
        'alert_type':   'success',
     })
    
# APPLY PROMO CODE

def validate_promo_code(request):
    """
    HTMX-only endpoint.
    POST: { code, shipping_cost }
    Returns inline HTML fragment injected into #promo-feedback.
    """
    code          = request.POST.get('code', '').strip()
    shipping_cost = request.POST.get('shipping_cost', '0')

    print(f"DEBUG promo: code={code!r}, shipping_cost={shipping_cost!r}")  # remove after testing

    try:
        shipping_cost = float(shipping_cost)
    except ValueError:
        shipping_cost = 0

    if not code:
        return HttpResponse('<span class="text-muted small">Enter a code to validate.</span>')

    promo, discount, error = apply_promo_code(code, shipping_cost)

    if error:
        return HttpResponse(
            f'<span class="text-danger small">'
            f'<i class="bi bi-x-circle me-1"></i>{error}</span>'
        )

    new_total = max(0, shipping_cost - float(discount))
    return HttpResponse(
        f'<span class="text-success small">'
        f'<i class="bi bi-check-circle me-1"></i>'
        f'Code <strong>{promo.code}</strong> applied — '
        f'you save <strong>£{discount}</strong>. '
        f'New total: <strong>£{new_total:.2f}</strong>'
        f'</span>'
        f'<input type="hidden" name="promo_validated" value="1">'
        f'<input type="hidden" name="discount_amount" value="{discount}">'
    )


# ============================================================
# DASHBOARD ANALYTICAL
# ============================================================

User = get_user_model()

def dashboard(request):
    today      = timezone.now().date()
    this_month = timezone.now().replace(day=1)
    last_month = (this_month - timedelta(days=1)).replace(day=1)

    # --- Section 1 ---
    total_orders_this_month = Order.objects.filter(created_at__gte=this_month).count()
    total_orders_last_month = Order.objects.filter(
        created_at__gte=last_month, created_at__lt=this_month
    ).count()

    if total_orders_last_month > 0:
        order_growth = round(
            ((total_orders_this_month - total_orders_last_month) / total_orders_last_month) * 100, 1
        )
    else:
        order_growth = 0

    order_growth_positive = order_growth >= 0

    total_shipments  = Shipment.objects.count()
    active_deliveries = Shipment.objects.filter(status=Shipment.STATUS_IN_TRANSIT).count()
    pending_orders   = Order.objects.filter(status=Order.STATUS_NEW).count()

    # --- Section 2 ---
    total_delivered   = Shipment.objects.filter(status=Shipment.STATUS_DELIVERED).count()
    delivery_rate     = round((total_delivered / total_shipments * 100), 1) if total_shipments > 0 else 0

    revenue_this_month = Order.objects.filter(
        created_at__gte=this_month
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    revenue_last_month = Order.objects.filter(
        created_at__gte=last_month, created_at__lt=this_month
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    if revenue_last_month > 0:
        revenue_growth = round(
            ((float(revenue_this_month) - float(revenue_last_month)) / float(revenue_last_month)) * 100, 1
        )
    else:
        revenue_growth = 0

    revenue_growth_positive = revenue_growth >= 0

    total_users = User.objects.filter(is_active=True).count()

    # --- Section 3 ---
    waiting_payment   = Order.objects.filter(status=Order.STATUS_NEW).count()
    waiting_pickup    = Shipment.objects.filter(status=Shipment.STATUS_PENDING).count()
    cancelled_shipments = Shipment.objects.filter(status=Shipment.STATUS_CANCELLED).count()
    waiting_shipment  = Order.objects.filter(status=Order.STATUS_PROCESSING).count()

    # --- Recent Orders ---
    recent_orders = Order.objects.select_related(
    'order_type', 'created_by'
    ).exclude(status=Order.STATUS_DELETED).order_by('-created_at')[:15]

    # print(f"DEBUG recent_orders count: {recent_orders.count()}")
    # for o in recent_orders:
    #     print(f"  -> {o.order_number} | {o.customer_name} | {o.created_at}")

    context = {
        # section 1
        'total_orders_this_month':  total_orders_this_month,
        'order_growth':             abs(order_growth),
        'order_growth_positive':    order_growth_positive,
        'total_shipments':          total_shipments,
        'active_deliveries':        active_deliveries,
        'pending_orders':           pending_orders,

        # section 2
        'delivery_rate':            delivery_rate,
        'revenue_this_month':       revenue_this_month,
        'revenue_growth':           abs(revenue_growth),
        'revenue_growth_positive':  revenue_growth_positive,
        'total_users':              total_users,

        # section 3
        'waiting_payment':          waiting_payment,
        'waiting_pickup':           waiting_pickup,
        'cancelled_shipments':      cancelled_shipments,
        'waiting_shipment':         waiting_shipment,

        # recent orders
        'recent_orders':            recent_orders,
    }
    return render(request, 'mainDash/index.html', context)

# QUICK SEARCH BAR QUERY

def quick_search(request):
    query   = request.GET.get('q', '').strip()
    print(f"DEBUG quick_search: query={query!r}")
    results = []

    if query:
        orders = Order.objects.select_related('order_type').filter(
            Q(order_number__icontains=query)       |
            Q(tracking_number__icontains=query)    |
            Q(customer_name__icontains=query)      |
            Q(customer_email__icontains=query)     |
            Q(customer_phone__icontains=query)     |
            Q(receiver_name__icontains=query)      |
            Q(receiver_phone__icontains=query)     |
            Q(reference_number__icontains=query)
        ).exclude(status=Order.STATUS_DELETED)[:10]

        shipments = Shipment.objects.select_related('order').filter(
            Q(shipment_number__icontains=query) |
            Q(order__order_number__icontains=query) |
            Q(order__tracking_number__icontains=query) |
            Q(carrier_name__icontains=query)
        )[:5]

        results = {
            'orders':    orders,
            'shipments': shipments,
            'query':     query,
        }

    return render(request, 'mainDash/components/quick_search_results.html', results)






