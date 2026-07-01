import time
from django.contrib import messages
from django.shortcuts import redirect, render
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django_countries import countries

from dashboard.forms.form_details import User
from dashboard.utils.file_handler import encode_pk
from .models import ContactMessage, Newsletter, QuoteRequest, Shipment, ShipmentTrackingEvent, SupportTicket
from .helpers import notify, validation_error, success_message, error_message
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.db.models import Q, Prefetch

from mainWebsite import models


# Create your views here.
def index(request):
    return render(request, 'mainWebsite/index.html', {});

def about(request):
    return render(request, 'mainWebsite/about.html', {});

def container(request):
    return render(request, 'mainWebsite/container-shipment.html');

def airCargo(request):
    return render(request, 'mainWebsite/air-shipment.html');

def vehicleCargo(request):
    return render(request, 'mainWebsite/vehicle-shipment.html');

def pricing(request):
    return render(request, 'mainWebsite/pricing.html');

def reviews(request):
    return render(request, 'mainWebsite/testimonial.html');

def faq(request):
    return render(request, 'mainWebsite/faq.html');

def getQuote(request):
    return render(request, 'mainWebsite/get-quote.html',
                {
                "countries": list(countries)
                }
            );

def photoGallery(request):
    return render(request, 'mainWebsite/photo-gallery.html');

def videoGallery(request):
    return render(request, 'mainWebsite/video-gallery.html');


def contact(request):
    if request.method == 'POST':
        errors = []
        
        # get the variable from the form input
        contactName = request.POST.get('contact_name', '').strip()
        contactEmail = request.POST.get('contact_email', '').strip()
        contactPhone = request.POST.get('contact_phone', '').strip()
        contactSubject = request.POST.get('contact_subject', '').strip()
        contactMessage = request.POST.get('contact_message', '').strip()

        if not contactName:
            errors.append('Name is required.')

        if not contactEmail:
            errors.append('Email is required.')

        elif '@' not in contactEmail:
            errors.append('Enter a valid email address.')

        if not contactSubject:
            errors.append('Subject is required.')

        if len(contactMessage) < 10:
            errors.append('Message must be at least 10 characters.')

        if errors:
            for error in errors:
                messages.error(request, error)
            return redirect('contact')
        try:
            # process the saving into db
            contact = ContactMessage(
                sender_name=contactName,
                sender_email=contactEmail,
                sender_phone=contactPhone,
                sender_subject=contactSubject,
                sender_message=contactMessage,
                )
            contact.save()

             # Auto-create support ticket
            ticket = SupportTicket.objects.create(
                submitter_name  = contact.sender_name,
                submitter_email = contact.sender_email,
                subject         = contact.sender_subject,
                description     = contact.sender_message,
                priority        = 'medium',
                status          = 'open',
                submitted_by    = None,  # guest user
            )

            # Link contact to ticket
            contact.ticket = ticket
            contact.save(update_fields=['ticket'])

            # Notify all staff
            staff_users = User.objects.filter(is_staff=True)
            for staff in staff_users:
                notify(
                    user       = staff,
                    title      = f'New Contact: {ticket.ticket_number}',
                    message    = f'{contact.sender_name} sent a message: {contact.sender_subject}',
                    notif_type = 'ticket',
                    url        = f'/dashboard/tickets/{encode_pk(ticket.pk)}/',
                )
            
            # success message
            messages.success(
                    request,
                    f'Thank you {contactName}, your message has been sent.'
                )
            # Error message
        except Exception:
            messages.error(
                request,
                'Sorry, an error occurred while sending your message.'
            )
        return redirect('contact')
      
    return render(request, 'mainWebsite/contact.html');


def termsAndCondition(request):
    return render(request, 'mainWebsite/terms-conditions.html');

def privacyPolicy(request):
    return render(request, 'mainWebsite/privacy_policy.html');

def trackShipment(request):
    return render(request, 'mainWebsite/trackOrder.html');

def newsletter_subscribe(request):
    # Testing only
    email = request.POST.get("news_letterEmail")
    if not email:
        return render(request, "mainWebsite/partials/newsletter_message.html",
            {
                "message": "Please enter email address.",
                "alert_type": "danger"
            }
        )
    try:
        validate_email(email)
    except ValidationError:
        return render(request, "mainWebsite/partials/newsletter_message.html", {
            "message": "Invalid email format",
            "alert_type": "danger"
        })

    if Newsletter.objects.filter(subscriber_email=email).exists():
        return render(
            request,
            "mainWebsite/partials/newsletter_message.html",
            {
                "message": "You are already subscribed.",
                "alert_type": "danger"
            }
        )

    Newsletter.objects.create(
        subscriber_email=email
    )
    # send email notification after subscribing

    try:
        html_content = render_to_string("mainWebsite/emails_template/news_letter.html", {
         # CORE EMAIL CONTENT (USED IN BODY)
        "title": "Newsletter Subscription Confirmed",
        "message": "Thank you for subscribing to our newsletter. You will now receive updates, news, and offers from our marketing team.",

        # BRAND HEADER
        "company_name": "TDSS UK",

        # OPTIONAL MEDIA
        "image_url": "https://tdssuk.co.uk/static/mainWebsite/img/logo/tdssuk_logo.png",  # or full URL like https://domain.com/static/email.png

        # OPTIONAL BUTTON (ONLY IF NEEDED)
        "button_url": "",
        "button_text": "Visit Website",

        # FOOTER DATA
        "about_title": "About",
        "about_text": "We are a registered company in the United Kingdom, providing specialized reliable logistics and shipping services across west africa.",

        "contact_title": "Contact Info",
        "company_address": "Tank Hill Road, Purfleet, Essex, RM19 1SX",
        "company_phone": "+44 741 535 5361",

        "links_title": "Useful Links",
        "contact_url": "https://tdssuk.co.uk/contact",
        "about_url": "https://tdssuk.co.uk/about",
        "services_url": "https://tdssuk.co.uk/services/container-shipment",
        "quote_url": "https://tdssuk.co.uk/get-quote",

        "unsubscribe_url": "https://tdssuk.co.uk/",
        })
       

        email_msg = EmailMultiAlternatives(
        subject="Newsletter Subscription Confirmed",
        body="Your email client does not support HTML.",
        from_email="TDSS UK Newsletter <ozaappng@gmail.com>",
        to=[email],
        )

        email_msg.attach_alternative(html_content, "text/html")
        email_msg.send()

    except Exception as e:
        # log the error but DO NOT break user flow
        print("Newsletter Email failed:", e)

    return render(
        request,
        "mainWebsite/partials/newsletter_message.html",
        {
            "message": "Thank you for subscribing.",
            "alert_type": "success",
            "clear_input": True
        }
    )

# quote request process here
def quote_submission(request):
  
    senderName = request.POST.get('sender_name', '').strip()
    senderEmail = request.POST.get('sender_email', '').strip()
    senderPhone = request.POST.get('sender_phone', '').strip()
    senderServiceType = request.POST.get('sender_serviceType', '').strip()
    senderFrom = request.POST.get('sender_from_country', '').strip()
    senderTo = request.POST.get('sender_to_country', '').strip()
    senderMessage = request.POST.get('sender_message', '').strip()
    
    if not senderName:
        return validation_error(request, "Name is required.")

    if not senderEmail:
         return validation_error(request, "Email is required.")

    try:
        validate_email(senderEmail)
    except ValidationError:
         return validation_error(request, "Enter valid email address.")

    if not senderPhone:
         return validation_error(request, "Phone number is required.")

    if not senderServiceType:
         return validation_error(request, "Service type is required.")

    if not senderFrom:
         return validation_error(request, "From location is required.")

    if not senderTo:
         return validation_error(request, "To destination is required.")

    try:
        # process the saving into db
        quoteDetails = QuoteRequest(
            quote_name=senderName,
            quote_email=senderEmail,
            quote_phone=senderPhone,
            quote_serviceType=senderServiceType,
            quoteFromCountry=senderFrom,
            quoteToCountry=senderTo,
            quote_message=senderMessage,
            )
        quoteDetails.save()
        # show success message
        # send email notification to user email here
        
        try:
            html_content = render_to_string("mainWebsite/emails_template/news_letter.html", {
            "title": "Your quote request has been submitted",
            "message": f"Dear {senderName}, thank you for choosing TDSS UK. We have received your quote request and our team is currently reviewing the information provided. A member of our team will get back to you as soon as possible with a competitive quotation and further assistance.",

            # BRAND HEADER
            "company_name": "TDSS UK",

            # OPTIONAL MEDIA
            "image_url": "https://tdssuk.co.uk/static/mainWebsite/img/logo/tdssuk_logo.png",  # or full URL like https://domain.com/static/email.png

            # OPTIONAL BUTTON (ONLY IF NEEDED)
            "button_url": "",
            "button_text": "Visit Website",

            # FOOTER DATA
            "about_title": "About",
            "about_text": "We are a registered company in the United Kingdom, providing specialized reliable logistics and shipping services across west africa.",

            "contact_title": "Contact Info",
            "company_address": "Tank Hill Road, Purfleet, Essex, RM19 1SX",
            "company_phone": "+44 741 535 5361",

            "links_title": "Useful Links",
            "contact_url": "https://tdssuk.co.uk/contact",
            "about_url": "https://tdssuk.co.uk/about",
            "services_url": "https://tdssuk.co.uk/services/container-shipment",
            "quote_url": "https://tdssuk.co.uk/get-quote",

            "unsubscribe_url": "https://tdssuk.co.uk/",
            })
        
            email_msg = EmailMultiAlternatives(
            subject= f"{senderName}, Your quote request has been received – TDSS UK",
            body="Your email client does not support HTML.",
            from_email="TDSS UK quote request <ozaappng@gmail.com>",
            to=[senderEmail],
            )

            email_msg.attach_alternative(html_content, "text/html")
            email_msg.send()

        except Exception as e:
            # log the error but DO NOT break user flow
            print("Quote request email failed:", e)

        return success_message(
                request,
                f"Thank you {senderName}, your request has been sent! We will get in touch shortly."
            )
        # Error message
    except Exception as e:
        print(e)
        
        return error_message(request, "Sorry, an error occurred while processing your request! Try again.")
    

# tracking parcel
def trackParcel(request):

    tracking_id = request.POST.get('track_number', '').strip().upper()

    if not tracking_id:
        return error_message(
                request,
                f"Error! Please enter a tracking number OR shipment number . ",
                alert_type="warning"
            )

    try:
        tracking_qs = (
            ShipmentTrackingEvent.objects
            .select_related('recorded_by')
            .order_by('created_at')
        )

        shipment_qs = (
            Shipment.objects
            .select_related('order', 'created_by')
            .prefetch_related(
                Prefetch('tracking_events', queryset=tracking_qs),
                'order__images',
            )
        )

        shipment = (
            shipment_qs
            .filter(
                Q(order__tracking_number=tracking_id) |
                Q(order__order_number=tracking_id)    |
                Q(shipment_number=tracking_id)
            )
            .order_by('-created_at')
            .first()
        )

        if not shipment:
            return error_message(
                request,
                f"No shipment found for {tracking_id}. "
                f"Please check your tracking number and try again.",
                alert_type="danger"
            )

        order = shipment.order

        return render(request, 'mainWebsite/components/trackResult.html', {
            'shipment': shipment,
            'order':    order,
            'query':    tracking_id,
        })

    except Exception as e:
        return error_message(
            request,
            "Sorry, an error occurred while processing your request. Please try again.",
            alert_type="warning"
        )





















